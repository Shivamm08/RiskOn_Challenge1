/** Global SME roster + rank hierarchy (mock data). */

export type ExpertRank =
  | "Suitability Champion"
  | "Business Front Support"
  | "Expert"
  | "Senior Expert"
  | "BRM Suitability Lead";

/** Low → high. Used everywhere ranking matters. */
export const RANK_ORDER: ExpertRank[] = [
  "Suitability Champion",
  "Business Front Support",
  "Expert",
  "Senior Expert",
  "BRM Suitability Lead",
];

export function rankIndex(rank: ExpertRank) {
  return RANK_ORDER.indexOf(rank);
}

/** Human phrasing of an expert's place on the 5-tier escalation ladder. */
export function rankTierLabel(rank: ExpertRank) {
  return `Tier ${rankIndex(rank) + 1} of ${RANK_ORDER.length} — ${rank}`;
}

export type RegionTier =
  | "Branch"
  | "CH"
  | "EU"
  | "EU/UK"
  | "APAC"
  | "Japan"
  | "US"
  | "MEA";

export type Expert = {
  id: string;
  name: string;
  office: string;
  regionTier: RegionTier;
  rank: ExpertRank;
  /** Hours offset from UTC (current season). */
  utcOffset: number;
  initials: string;
  /** 0–100. */
  favorability: number;
  answered: number;
  /** Percent. */
  accuracy: number;
  specialty: string;
  /** Full title shown in the roster, e.g. "BRM Suitability Lead, APAC". */
  title: string;
};

function initials(name: string) {
  return name
    .replace(/\./g, "")
    .split(/\s+/)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("")
    .slice(0, 2);
}

type Seed = Omit<Expert, "id" | "initials" | "title"> & { title?: string };

const SEED: Seed[] = [
  {
    name: "Nina Aebi",
    office: "Zurich",
    regionTier: "Branch",
    rank: "Suitability Champion",
    utcOffset: 2,
    favorability: 61,
    answered: 214,
    accuracy: 92,
    specialty: "Front-office triage, K&E checks, CH retail alerts",
  },
  {
    name: "Daniel Frei",
    office: "Zurich",
    regionTier: "Branch",
    rank: "Business Front Support",
    utcOffset: 2,
    favorability: 68,
    answered: 331,
    accuracy: 93,
    specialty: "Mandate scope, advisory documentation, trade blocks",
  },
  {
    name: "Elena Roth",
    office: "Geneva",
    regionTier: "CH",
    rank: "Expert",
    utcOffset: 2,
    favorability: 72,
    answered: 288,
    accuracy: 94,
    specialty: "CH suitability policy, complex product approvals",
  },
  {
    name: "Marco Steiner",
    office: "Geneva",
    regionTier: "CH",
    rank: "Senior Expert",
    utcOffset: 2,
    favorability: 84,
    answered: 512,
    accuracy: 96,
    specialty: "Cross-border classification, structured products",
  },
  {
    name: "Sophie Wyss",
    office: "Frankfurt",
    regionTier: "EU",
    rank: "Senior Expert",
    utcOffset: 2,
    favorability: 87,
    answered: 604,
    accuracy: 97,
    specialty: "MiFID II target market, EU cross-border marketing",
  },
  {
    name: "Lukas Baumann",
    office: "Frankfurt",
    regionTier: "EU",
    rank: "BRM Suitability Lead",
    utcOffset: 2,
    favorability: 90,
    answered: 447,
    accuracy: 97,
    specialty: "EU booking-centre policy, regulator liaison",
  },
  {
    name: "Clara Suter",
    office: "London",
    regionTier: "EU/UK",
    rank: "Senior Expert",
    utcOffset: 1,
    favorability: 83,
    answered: 398,
    accuracy: 95,
    specialty: "UK COBS, consumer duty, professional opt-ups",
  },
  {
    name: "Felix Graf",
    office: "Singapore",
    regionTier: "APAC",
    rank: "Senior Expert",
    utcOffset: 8,
    favorability: 81,
    answered: 356,
    accuracy: 95,
    specialty: "MAS accredited investors, APAC product gating",
  },
  {
    name: "Julia Marti",
    office: "Hong Kong",
    regionTier: "APAC",
    rank: "BRM Suitability Lead",
    utcOffset: 8,
    favorability: 92,
    answered: 501,
    accuracy: 98,
    specialty: "APAC suitability governance, SFC complex products",
    title: "BRM Suitability Lead, APAC",
  },
  {
    name: "Tobias Egli",
    office: "Tokyo",
    regionTier: "Japan",
    rank: "Senior Expert",
    utcOffset: 9,
    favorability: 86,
    answered: 302,
    accuracy: 96,
    specialty: "FIEA solicitation rules, JP client classification",
  },
  {
    name: "Mia Widmer",
    office: "Tokyo",
    regionTier: "Japan",
    rank: "BRM Suitability Lead",
    utcOffset: 9,
    favorability: 91,
    answered: 388,
    accuracy: 97,
    specialty: "Japan desk governance, escalation sign-off",
    title: "BRM Suitability Lead, Japan",
  },
  {
    name: "Simon Kunz",
    office: "New York",
    regionTier: "US",
    rank: "Senior Expert",
    utcOffset: -4,
    favorability: 85,
    answered: 419,
    accuracy: 96,
    specialty: "SEC/FINRA suitability, US-person restrictions",
  },
  {
    name: "Laura Moser",
    office: "New York",
    regionTier: "US",
    rank: "BRM Suitability Lead",
    utcOffset: -4,
    favorability: 94,
    answered: 356,
    accuracy: 98,
    specialty: "Americas suitability strategy, contested guidance",
    title: "BRM Suitability Lead, Americas",
  },
  {
    name: "Leon Zimmermann",
    office: "Dubai",
    regionTier: "MEA",
    rank: "Senior Expert",
    utcOffset: 4,
    favorability: 80,
    answered: 271,
    accuracy: 94,
    specialty: "DFSA rules, MEA cross-border solicitation",
  },
];

export const EXPERTS: Expert[] = SEED.map((s) => ({
  ...s,
  id: s.name.toLowerCase().replace(/[^a-z]+/g, "-"),
  initials: initials(s.name),
  title: s.title ?? `${s.rank}, ${s.office}`,
}));

export function getExpert(id: string | undefined | null): Expert | undefined {
  if (!id) return undefined;
  return EXPERTS.find((e) => e.id === id);
}

export function expertByName(name: string): Expert | undefined {
  return EXPERTS.find((e) => e.name.toLowerCase() === name.trim().toLowerCase());
}

/** Local wall-clock time for an expert, computed live from their UTC offset. */
export function localTime(expert: Expert, now: Date = new Date()) {
  const ms = now.getTime() + expert.utcOffset * 3_600_000;
  const d = new Date(ms);
  const hours = d.getUTCHours();
  const minutes = d.getUTCMinutes();
  return {
    hours,
    minutes,
    label: `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`,
    /** Roughly reasonable working hours. */
    working: hours >= 8 && hours < 18,
  };
}

export function localTimeLabel(expert: Expert, now: Date = new Date()) {
  return `${localTime(expert, now).label} local, ${expert.office}`;
}

/** The next rank up in the same office, else the same region, else globally. */
export function supervisorOf(expert: Expert): Expert | undefined {
  const higher = (list: Expert[]) =>
    list
      .filter((e) => rankIndex(e.rank) > rankIndex(expert.rank))
      .sort((a, b) => rankIndex(a.rank) - rankIndex(b.rank))[0];

  return (
    higher(EXPERTS.filter((e) => e.office === expert.office)) ??
    higher(EXPERTS.filter((e) => e.regionTier === expert.regionTier)) ??
    higher(EXPERTS)
  );
}
