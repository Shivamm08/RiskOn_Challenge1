import { SEED_EXCHANGES } from "./seed";
import type { AskResponse, QueryContext } from "./types";

const STOP = new Set([
  "the",
  "a",
  "an",
  "is",
  "are",
  "do",
  "does",
  "can",
  "i",
  "to",
  "for",
  "in",
  "of",
  "and",
  "on",
  "what",
  "which",
  "with",
  "it",
  "that",
  "this",
  "my",
  "their",
  "client",
  "clients",
]);

function tokens(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s/&-]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 2 && !STOP.has(t));
}

let counter = 9000;
function nextRequestId() {
  counter += 1;
  return `req_${counter}`;
}

/** Follow-up resolution for the research-note clarification. */
function researchNoteAnswer(serviceModel: string): AskResponse {
  const executionOnly = serviceModel.toLowerCase().startsWith("execution");
  return {
    request_id: nextRequestId(),
    status: "answered",
    answer: executionOnly
      ? "Under Execution-only, a product research note may be sent provided it is distributed on a non-personalised basis and carries the standard generic-information disclaimer. Do not add commentary that references the client's portfolio, risk profile or objectives — that converts the note into a personal recommendation and brings the relationship outside the Execution-only scope, triggering a suitability record."
      : "Under an Advisory mandate, a product research note sent with any client-specific framing is treated as a personal recommendation and requires a suitability record before it is sent. Distributing the note unchanged, on the same basis as to all clients in the segment and with the generic-information disclaimer, remains generic information and requires no suitability record.",
    confidence: { answer_confidence: 0.91, routing_confidence: 0.9 },
    sources: [
      {
        page_title: "Suitability Wiki — Generic Information vs Personal Recommendation",
        excerpt:
          "Material distributed on a non-personalised basis to a client segment constitutes generic information. Any reference to the individual client's portfolio, risk profile or objectives converts the communication into a personal recommendation, which requires a suitability record prior to transmission.",
        url: null,
        fileType: "doc",
      },
      {
        page_title: "Suitability Wiki — Research Distribution Disclaimers",
        excerpt:
          "Research notes must carry the standard generic-information disclaimer when sent without a suitability assessment.",
        url: null,
        fileType: "excel",
      },
    ],
    scope_flags: [
      "in_scope:communications",
      executionOnly ? "in_scope:execution_only" : "in_scope:advisory",
    ],
    reasoning: [
      `Service model clarified by the RM: ${serviceModel}.`,
      "Applied the generic-information boundary test from the wiki.",
      "Confirmed the disclaimer requirement from the research distribution page.",
    ],
    escalation: null,
    clarification_question: null,
  };
}

function unknownEscalation(question: string, context: QueryContext): AskResponse {
  const centre = context.bookingCentre ?? "the client's booking centre";
  return {
    request_id: nextRequestId(),
    status: "escalated",
    answer: null,
    confidence: { answer_confidence: 0.24, routing_confidence: 0.79 },
    sources: [],
    scope_flags: ["wiki_gap:no_matching_guidance"],
    reasoning: [
      `Question parsed: "${question}".`,
      "No wiki page was retrieved above the relevance threshold for this question.",
      "Answer confidence below the 0.70 publication threshold — escalating rather than answering.",
      `Routing selected on topic and booking centre (${centre}).`,
    ],
    escalation: {
      required: true,
      tier: "suitability_champion",
      expert: {
        name: "Nina Aebi",
        role: "Suitability Champion",
        team: `Front Office — ${context.bookingCentre ?? "Switzerland"}`,
      },
      experts: [
        {
          name: "Nina Aebi",
          role: "Suitability Champion",
          team: `Front Office — ${context.bookingCentre ?? "Switzerland"}`,
        },
        {
          name: "Daniel Frei",
          role: "Business Front Support Officer",
          team: "Business Front Support",
        },
        {
          name: "Sonia Egger",
          role: "BRM Suitability Lead",
          team: "BRM Suitability Leads",
        },
      ],
      reason:
        "No wiki guidance was retrieved for this question, so it cannot be answered from the connected knowledge sources. The Suitability Champion is the first human tier and will either resolve it directly or escalate to Business Front Support.",
      fallback_contact: { name: "Daniel Frei", role: "Business Front Support Officer" },
    },
    clarification_question: null,
  };
}

/**
 * Single entry point for answering a question.
 *
 * Backend swap: replace the body with
 *   const res = await fetch("/ask", { method: "POST", body: JSON.stringify({ question, context }) });
 *   return (await res.json()) as AskResponse;
 */
export async function askSuitability(
  question: string,
  context: QueryContext,
): Promise<AskResponse> {
  await new Promise((r) => setTimeout(r, 550));

  const trimmed = question.trim();
  const serviceModelReply = ["advisory", "execution-only", "portfolio management"].find(
    (m) => trimmed.toLowerCase() === m,
  );
  if (serviceModelReply) return researchNoteAnswer(trimmed);

  const asked = tokens(trimmed);
  let best: { score: number; response: AskResponse } | null = null;

  for (const exchange of SEED_EXCHANGES) {
    const candidate = tokens(exchange.question);
    const overlap = asked.filter((t) => candidate.includes(t)).length;
    const score = overlap / Math.max(3, asked.length);
    if (!best || score > best.score) {
      best = { score, response: exchange.response };
    }
  }

  if (best && best.score >= 0.34) {
    return { ...best.response, request_id: nextRequestId() };
  }

  return unknownEscalation(trimmed, context);
}
