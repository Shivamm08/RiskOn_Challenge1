export type BookingCentre = "CH" | "Monaco" | "Germany" | "EEA" | "Other";
export type ClientCategory = "Private/Retail" | "Professional" | "Institutional";
export type ServiceModel = "Advisory" | "Execution-only" | "Portfolio Management";

export type QueryContext = {
  bookingCentre?: BookingCentre;
  clientCategory?: ClientCategory;
  serviceModel?: ServiceModel;
};

export type ResponseStatus = "answered" | "escalated" | "clarification_needed";

export type EscalationTier =
  | "wiki"
  | "suitability_champion"
  | "business_front_support"
  | "brm_suitability_lead"
  | "suitability_expert";

export type SourceFileType = "link" | "excel" | "csv" | "doc" | "pdf";

export type SourceRef = {
  page_title: string;
  excerpt: string;
  url: string | null;
  fileType?: SourceFileType;
};

export type Escalation = {
  required: boolean;
  tier: EscalationTier;
  expert: { name: string; role: string; team: string };
  experts?: { name: string; role: string; team: string }[];
  reason: string;
  fallback_contact: { name: string; role: string };
};

/** Wire shape returned by the `/ask` endpoint. */
export type AskResponse = {
  request_id: string;
  status: ResponseStatus;
  answer: string | null;
  confidence: { answer_confidence: number; routing_confidence: number };
  sources: SourceRef[];
  scope_flags: string[];
  escalation: Escalation | null;
  clarification_question: string | null;
  /** Optional reasoning trail surfaced under "Why this answer". */
  reasoning?: string[];
  /** Optional quick replies offered with a clarification. */
  quick_replies?: string[];
};

export type Exchange = {
  id: string;
  question: string;
  askedAt: string;
  askedBy: string;
  context: QueryContext;
  response: AskResponse;
  resolution?: { resolvedBy: string; note: string; resolvedAt: string };
};

export const TIER_LADDER: { tier: EscalationTier; label: string }[] = [
  { tier: "wiki", label: "Wiki" },
  { tier: "suitability_champion", label: "Suitability Champion" },
  { tier: "business_front_support", label: "Business Front Support" },
  { tier: "brm_suitability_lead", label: "BRM Suitability Lead" },
  { tier: "suitability_expert", label: "Suitability Expert" },
];

export const BOOKING_CENTRES: BookingCentre[] = ["CH", "Monaco", "Germany", "EEA", "Other"];
export const CLIENT_CATEGORIES: ClientCategory[] = [
  "Private/Retail",
  "Professional",
  "Institutional",
];
export const SERVICE_MODELS: ServiceModel[] = [
  "Advisory",
  "Execution-only",
  "Portfolio Management",
];
