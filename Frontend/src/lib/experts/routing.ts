import type { QueryContext } from "@/lib/suitability/types";
import {
  EXPERTS,
  getExpert,
  localTime,
  rankIndex,
  type Expert,
  type RegionTier,
} from "./roster";

export type RoutingDecision = {
  expertId: string;
  /** Geographic tiers searched, in order. */
  tiersSearched: string[];
  /** Tier the chosen expert was found in. */
  matchedTier: string;
  candidateIds: string[];
  /** Candidate skipped because they were outside working hours. */
  skipped?: { expertId: string; localLabel: string };
  /** Plain-language reasoning lines, in order. */
  reasoning: string[];
  /** Timestamp the decision was computed at (ISO). */
  decidedAt: string;
};

const TIER_CHAINS: Record<string, RegionTier[]> = {
  CH: ["Branch", "CH", "EU", "EU/UK"],
  Monaco: ["Branch", "CH", "EU", "EU/UK"],
  Germany: ["EU", "EU/UK", "CH", "Branch"],
  EEA: ["EU", "EU/UK", "CH", "Branch"],
  Other: ["Branch", "CH", "EU"],
};

const TIER_LABEL: Record<RegionTier, string> = {
  Branch: "branch (Zurich)",
  CH: "country (Switzerland — Geneva)",
  EU: "region (EU — Frankfurt)",
  "EU/UK": "region (UK — London)",
  APAC: "region (APAC)",
  Japan: "region (Japan)",
  US: "region (Americas)",
  MEA: "region (MEA)",
};

const GLOBAL_TIERS: RegionTier[] = ["APAC", "Japan", "US", "MEA"];

function byStrength(a: Expert, b: Expert) {
  const r = rankIndex(b.rank) - rankIndex(a.rank);
  if (r !== 0) return r;
  if (b.favorability !== a.favorability) return b.favorability - a.favorability;
  return b.accuracy - a.accuracy;
}

/**
 * Geographic + hierarchy + timezone-aware routing.
 *
 * Backend swap: replace with the routing service response; the shape returned
 * here is what every view already renders.
 */
export function routeQuestion(
  context: QueryContext,
  options: { now?: Date; requireGlobal?: boolean } = {},
): RoutingDecision {
  const now = options.now ?? new Date();
  const centre = context.bookingCentre ?? "CH";
  const chain = [...(TIER_CHAINS[centre] ?? TIER_CHAINS["Other"]!)];
  if (options.requireGlobal) chain.push(...GLOBAL_TIERS);

  const tiersSearched: string[] = [];
  let pool: Expert[] = [];
  let matchedTier: RegionTier = chain[0]!;

  for (const tier of chain) {
    tiersSearched.push(TIER_LABEL[tier]);
    const found = EXPERTS.filter((e) => e.regionTier === tier);
    pool = [...pool, ...found];
    if (pool.length >= 2) {
      matchedTier = tier;
      break;
    }
  }
  if (pool.length === 0) pool = [...EXPERTS];

  const ranked = [...pool].sort(byStrength);
  const top = ranked[0]!;
  const topTime = localTime(top, now);

  let chosen = top;
  let skipped: RoutingDecision["skipped"];

  if (!topTime.working) {
    const available =
      ranked.slice(1).find((e) => localTime(e, now).working) ??
      [...EXPERTS].sort(byStrength).find((e) => localTime(e, now).working);
    if (available) {
      chosen = available;
      skipped = { expertId: top.id, localLabel: `${topTime.label} local, ${top.office}` };
    }
  }

  const chosenTime = localTime(chosen, now);
  const reasoning: string[] = [
    `Searched geographically outward from the client's booking centre (${centre}): ${tiersSearched.join(" → ")}.`,
    `${pool.length} experts matched at the ${TIER_LABEL[matchedTier]} tier.`,
  ];

  if (skipped) {
    const skippedExpert = getExpert(skipped.expertId)!;
    reasoning.push(
      `${skippedExpert.name} (${skippedExpert.office}, ${skippedExpert.rank}) is the highest-ranked match, but it's ${skipped.localLabel} — outside working hours — so routing to ${chosen.name} (${chosenTime.label} local, ${chosen.office}) instead.`,
    );
  } else {
    reasoning.push(
      `${chosen.name} holds the highest rank among those candidates (${chosen.rank}) and is inside working hours at ${chosenTime.label} local, ${chosen.office}.`,
    );
  }

  reasoning.push(
    `Track record supports the choice: ${chosen.accuracy}% accuracy over ${chosen.answered} answered questions, favorability ${chosen.favorability}/100.`,
    `Specialty match: ${chosen.specialty}.`,
  );

  return {
    expertId: chosen.id,
    tiersSearched,
    matchedTier: TIER_LABEL[matchedTier],
    candidateIds: ranked.slice(0, 4).map((e) => e.id),
    ...(skipped ? { skipped } : {}),
    reasoning,
    decidedAt: now.toISOString(),
  };
}

export type RoutingScenario = {
  id: string;
  title: string;
  blurb: string;
  question: string;
  context: QueryContext;
  /** Fixed clock used for the scenario, so the demo is reproducible. */
  at: string;
  atLabel: string;
  requireGlobal?: boolean;
};

export const ROUTING_SCENARIOS: RoutingScenario[] = [
  {
    id: "ch-local",
    title: "Resolved inside Switzerland",
    blurb:
      "A CH-booked advisory question. The branch and country tiers already hold a confident match, so the question never leaves Switzerland.",
    question: "Does a CH-booked Retail client need a fresh K&E check before a fund switch?",
    context: { bookingCentre: "CH", clientCategory: "Private/Retail", serviceModel: "Advisory" },
    at: "2026-09-01T09:20:00Z",
    atLabel: "11:20 Zurich",
  },
  {
    id: "cross-border-eu",
    title: "Escalated out to Frankfurt",
    blurb:
      "A cross-border EU marketing question. Zurich and Geneva have no confident match on MiFID II target market, so the search widens to the EU region tier.",
    question:
      "Can I market a Reverse Convertible to a German-domiciled Professional client during a Zurich meeting?",
    context: { bookingCentre: "Germany", clientCategory: "Professional", serviceModel: "Advisory" },
    at: "2026-09-01T13:05:00Z",
    atLabel: "15:05 Frankfurt",
  },
  {
    id: "tz-daytime",
    title: "Time-sensitive — asked at 08:00 UTC",
    blurb:
      "A global product question asked during the European morning. Tokyo and APAC are still reachable, so the highest-ranked candidate takes it.",
    question: "Is a capital-protected note distributable to an APAC-domiciled client booked in CH?",
    context: { bookingCentre: "Other", clientCategory: "Professional" },
    at: "2026-09-01T04:00:00Z",
    atLabel: "06:00 Zurich · 13:00 Tokyo",
    requireGlobal: true,
  },
  {
    id: "tz-nighttime",
    title: "Same question — asked at 19:00 UTC",
    blurb:
      "Identical question, twelve hours later. The highest-ranked candidate is asleep, so routing falls to the next-best expert who is actually available.",
    question: "Is a capital-protected note distributable to an APAC-domiciled client booked in CH?",
    context: { bookingCentre: "Other", clientCategory: "Professional" },
    at: "2026-09-01T19:00:00Z",
    atLabel: "21:00 Zurich · 04:00 Tokyo",
    requireGlobal: true,
  },
];

export function scenarioDecision(scenario: RoutingScenario): RoutingDecision {
  return routeQuestion(scenario.context, {
    now: new Date(scenario.at),
    ...(scenario.requireGlobal ? { requireGlobal: true } : {}),
  });
}
