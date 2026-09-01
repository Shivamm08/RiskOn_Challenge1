import type { Exchange } from "./types";

export const CURRENT_RM = "A. Brunner";

export const EXAMPLE_QUESTIONS = [
  "Can I recommend a structured product to a Professional client in Monaco?",
  "What alerts apply before executing a trade for a Retail client?",
  "Does a CH-booked client relocating to Monaco need reclassification?",
  "Is a Knowledge & Experience check required for a German-domiciled client?",
];

/**
 * Seeded exchanges. Same wire shape as the future `/ask` response, so this file
 * is the only thing that disappears once the backend is connected.
 */
export const SEED_EXCHANGES: Exchange[] = [
  {
    id: "req_8841",
    question: "Can I recommend a structured product to a Professional client in Monaco?",
    askedAt: "2026-09-01T07:12:00Z",
    askedBy: "A. Brunner",
    context: {
      bookingCentre: "Monaco",
      clientCategory: "Professional",
      serviceModel: "Advisory",
    },
    response: {
      request_id: "req_8841",
      status: "answered",
      answer:
        "Yes. For a Professional client booked in Monaco under an Advisory mandate, capital-protected and yield-enhancement structured products are in scope, provided the product is on the Monaco-approved distribution list and the client's risk profile covers issuer credit risk. The Knowledge & Experience check is presumed satisfied by the Professional classification, so no separate K&E questionnaire is required. Cross-border marketing restrictions do not apply where the advice is given to a Monaco-domiciled client on Monaco premises.",
      confidence: { answer_confidence: 0.94, routing_confidence: 0.91 },
      sources: [
        {
          page_title: "Suitability Wiki — Structured Products: Advisory Distribution Matrix",
          excerpt:
            "Structured products may be recommended to clients classified as Professional without a separate Knowledge & Experience assessment, provided the instrument appears on the booking centre's approved distribution list and the client risk profile permits exposure to issuer credit risk.",
          url: null,
        },
        {
          page_title: "Suitability Wiki — Booking Centre Monaco: Product Scope",
          excerpt:
            "Monaco-booked relationships follow the Monaco approved distribution list. Products absent from that list must not be recommended even where approved in Switzerland.",
          url: null,
        },
      ],
      scope_flags: ["in_scope:advisory", "in_scope:monaco", "kande:presumed_professional"],
      reasoning: [
        "Context resolved: Booking Centre Monaco, Client Category Professional, Service Model Advisory.",
        "Matched the Advisory Distribution Matrix, which governs structured-product recommendations by client classification.",
        "Confirmed the Monaco booking-centre page adds a distribution-list condition but no further classification restriction.",
        "No cross-border trigger: advice is given to a Monaco-domiciled client within Monaco.",
        "Both sources are current and mutually consistent, so the question is judged in scope and sufficiently covered.",
      ],
      escalation: null,
      clarification_question: null,
    },
  },
  {
    id: "req_8842",
    question: "What alerts apply before executing a trade for a Retail client?",
    askedAt: "2026-09-01T07:26:00Z",
    askedBy: "A. Brunner",
    context: { bookingCentre: "CH", clientCategory: "Private/Retail" },
    response: {
      request_id: "req_8842",
      status: "answered",
      answer:
        "Three pre-trade alerts are mandatory for a Private/Retail client booked in Switzerland: (1) the appropriateness alert, confirming the instrument matches the recorded Knowledge & Experience profile; (2) the concentration alert, triggered where the position would exceed the single-issuer or single-asset-class threshold in the client's risk profile; and (3) the complex-product alert, requiring documented client acknowledgement for leveraged or non-capital-protected instruments. Any alert left unresolved must be documented with the client's instruction before execution.",
      confidence: { answer_confidence: 0.89, routing_confidence: 0.9 },
      sources: [
        {
          page_title: "Suitability Wiki — Pre-Trade Alerts: Retail Clients (CH)",
          excerpt:
            "For Private/Retail clients, the appropriateness, concentration and complex-product alerts must be cleared or explicitly overridden with a documented client instruction prior to order release.",
          url: null,
        },
        {
          page_title: "Suitability Wiki — Alert Override Documentation Standard",
          excerpt:
            "An overridden alert requires the client's instruction to be recorded in the advisory log, including date, channel and the alert reference overridden.",
          url: null,
        },
      ],
      scope_flags: ["in_scope:pre_trade", "in_scope:ch", "documentation_required"],
      reasoning: [
        "Context resolved: Booking Centre CH, Client Category Private/Retail.",
        "Retrieved the CH retail pre-trade alert page, which enumerates the mandatory alert set.",
        "Cross-checked the override documentation standard, which defines what must be recorded if an alert is not cleared.",
        "Service model was not required to answer: the alert set applies to both Advisory and Execution-only order flow.",
      ],
      escalation: null,
      clarification_question: null,
    },
  },
  {
    id: "req_8843",
    question:
      "A CH-booked client has moved their tax residence to Monaco but keeps a German address for correspondence. Does that change their classification and which cross-border rules apply?",
    askedAt: "2026-09-01T07:41:00Z",
    askedBy: "A. Brunner",
    context: { bookingCentre: "CH", clientCategory: "Private/Retail", serviceModel: "Advisory" },
    response: {
      request_id: "req_8843",
      status: "escalated",
      answer: null,
      confidence: { answer_confidence: 0.31, routing_confidence: 0.88 },
      sources: [
        {
          page_title: "Suitability Wiki — Cross-Border Country Manual: Switzerland",
          excerpt:
            "The applicable country rules are determined by the client's domicile. Where domicile and correspondence country diverge, the stricter regime applies pending confirmation by Business Risk Management.",
          url: null,
        },
      ],
      scope_flags: [
        "out_of_scope:multi_jurisdiction_conflict",
        "wiki_gap:domicile_vs_correspondence",
      ],
      reasoning: [
        "Context resolved: Booking Centre CH, Client Category Private/Retail, Service Model Advisory.",
        "The Switzerland country manual states the stricter regime applies where domicile and correspondence country diverge, but does not resolve a three-way CH / Monaco / Germany combination.",
        "No wiki page covers reclassification triggered by a change of tax residence with a retained EEA correspondence address.",
        "Answer confidence below the 0.70 publication threshold — escalation required rather than a partial answer.",
      ],
      escalation: {
        required: true,
        tier: "brm_suitability_lead",
        expert: {
          name: "Isabelle Roth",
          role: "BRM Suitability Lead, Western Markets & Switzerland",
          team: "Business Risk Management",
        },
        reason:
          "This involves a cross-border CH/Monaco classification question with an additional German correspondence address, which is not covered in the wiki and cannot be resolved from the country manual alone. Routing to the BRM Suitability Lead for Western Markets & Switzerland, who owns the domicile-conflict determination for these booking centres.",
        fallback_contact: {
          name: "Marc Vuillemin",
          role: "Head of Business Risk Management, Switzerland",
        },
      },
      clarification_question: null,
    },
  },
  {
    id: "req_8844",
    question: "Can I send the client a product research note without it counting as advice?",
    askedAt: "2026-09-01T07:55:00Z",
    askedBy: "A. Brunner",
    context: { bookingCentre: "CH" },
    response: {
      request_id: "req_8844",
      status: "clarification_needed",
      answer: null,
      confidence: { answer_confidence: 0.42, routing_confidence: 0.86 },
      sources: [],
      scope_flags: ["ambiguous:service_model"],
      reasoning: [
        "The boundary between generic information and a personal recommendation depends on the service model governing the relationship.",
        "Under Execution-only, unsolicited research distribution is treated differently than under an Advisory mandate.",
        "Service Model was not set in context and cannot be inferred from the question — asking rather than assuming.",
      ],
      escalation: null,
      clarification_question:
        "Which service model governs this relationship — the distinction between generic information and a personal recommendation depends on it.",
      quick_replies: ["Advisory", "Execution-only", "Portfolio Management"],
    },
  },
  {
    id: "req_8845",
    question: "Is a Knowledge & Experience check required for a German-domiciled Retail client?",
    askedAt: "2026-09-01T08:04:00Z",
    askedBy: "A. Brunner",
    context: { bookingCentre: "Germany", clientCategory: "Private/Retail" },
    response: {
      request_id: "req_8845",
      status: "answered",
      answer:
        "Yes. A German-domiciled Private/Retail client requires a completed Knowledge & Experience assessment before any advisory recommendation, and the assessment must be refreshed at least every 24 months or on any material change to the client's circumstances. For Execution-only order flow the check narrows to an appropriateness test on complex instruments only. Note that the German booking-centre annex is currently under review, so treat the refresh interval as the binding minimum and confirm with your Suitability Champion before relying on the shorter Execution-only scope.",
      confidence: { answer_confidence: 0.76, routing_confidence: 0.88 },
      sources: [
        {
          page_title: "Suitability Wiki — Knowledge & Experience: Scope and Refresh Cycle",
          excerpt:
            "A Knowledge & Experience assessment is mandatory for Private/Retail clients prior to any personal recommendation and must be refreshed at intervals not exceeding 24 months, or earlier upon a material change in client circumstances.",
          url: null,
        },
        {
          page_title: "Suitability Wiki — Booking Centre Germany: Annex (under review)",
          excerpt:
            "For Execution-only order flow, the assessment is limited to an appropriateness test applied to complex financial instruments. This annex is under review; the general refresh cycle remains binding.",
          url: null,
        },
      ],
      scope_flags: ["in_scope:kande", "in_scope:germany", "source_under_review"],
      reasoning: [
        "Context resolved: Booking Centre Germany, Client Category Private/Retail.",
        "The general K&E page establishes the requirement and the 24-month refresh cycle.",
        "The German annex narrows the Execution-only scope but is flagged as under review, which caps answer confidence at medium.",
        "Confidence reported at 0.76 — above the publication threshold, with the review status surfaced in the answer.",
      ],
      escalation: null,
      clarification_question: null,
    },
  },
];

/** Historical records shown in the audit trail, including a resolved escalation. */
export const SEED_AUDIT: Exchange[] = [
  {
    id: "req_8790",
    question:
      "Client wants to switch from Portfolio Management to Execution-only mid-quarter — what suitability record do I need to keep?",
    askedAt: "2026-08-28T13:18:00Z",
    askedBy: "L. Keller",
    context: { bookingCentre: "CH", clientCategory: "Professional" },
    response: {
      request_id: "req_8790",
      status: "escalated",
      answer: null,
      confidence: { answer_confidence: 0.38, routing_confidence: 0.83 },
      sources: [
        {
          page_title: "Suitability Wiki — Service Model Changes",
          excerpt:
            "A change of service model requires a new suitability record from the effective date. Mid-period transitions are handled case by case.",
          url: null,
        },
      ],
      scope_flags: ["wiki_gap:mid_period_transition"],
      reasoning: [
        "The service-model change page defers mid-period transitions to a case-by-case determination.",
        "No documented record-keeping standard for a mid-quarter PM to Execution-only switch.",
      ],
      escalation: {
        required: true,
        tier: "business_front_support",
        expert: {
          name: "Daniel Frei",
          role: "Business Front Support Officer",
          team: "Front Support Switzerland",
        },
        reason:
          "The wiki defers mid-period service-model transitions to a case-by-case determination. Business Front Support maintains the record-keeping template for these transitions.",
        fallback_contact: { name: "Sonia Egger", role: "Team Lead, Front Support Switzerland" },
      },
      clarification_question: null,
    },
    resolution: {
      resolvedBy: "Daniel Frei",
      note: "Use the mid-period transition template (FS-114). Retain the closing PM suitability record dated the effective date, plus a signed client instruction confirming the switch. No new K&E required for a Professional client.",
      resolvedAt: "2026-08-28T15:02:00Z",
    },
  },
  {
    id: "req_8802",
    question: "Are FX forwards in scope for an Execution-only Institutional client in the EEA?",
    askedAt: "2026-08-29T09:44:00Z",
    askedBy: "M. Santoro",
    context: {
      bookingCentre: "EEA",
      clientCategory: "Institutional",
      serviceModel: "Execution-only",
    },
    response: {
      request_id: "req_8802",
      status: "answered",
      answer:
        "Yes. FX forwards are in scope for an Institutional client under Execution-only in the EEA. No appropriateness test applies, and no Knowledge & Experience assessment is required. Standard hedging-purpose documentation still applies where the forward is booked against a commercial exposure.",
      confidence: { answer_confidence: 0.95, routing_confidence: 0.93 },
      sources: [
        {
          page_title: "Suitability Wiki — Institutional Clients: Assessment Exemptions",
          excerpt:
            "Clients classified as Institutional are exempt from the appropriateness test and the Knowledge & Experience assessment across all service models.",
          url: null,
        },
      ],
      scope_flags: ["in_scope:execution_only", "exempt:institutional"],
      reasoning: [
        "Institutional classification carries a blanket exemption from appropriateness and K&E testing.",
        "Confirmed FX forwards are not on any restricted-instrument list for the EEA booking centre.",
      ],
      escalation: null,
      clarification_question: null,
    },
  },
];
