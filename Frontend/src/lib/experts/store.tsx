import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { QueryContext } from "@/lib/suitability/types";
import { getExpert, supervisorOf, type Expert } from "./roster";
import { routeQuestion, type RoutingDecision } from "./routing";

export type MessageStatus = "pending" | "answered" | "resolved";

export type ExpertAnswer = {
  text: string;
  answeredAt: string;
  publishedToKb: boolean;
  contradictsWiki: boolean;
  kbEntryId?: string;
};

export type EscalationMessage = {
  id: string;
  question: string;
  context: QueryContext;
  askedBy: string;
  askedAt: string;
  expertId: string;
  routing: RoutingDecision;
  status: MessageStatus;
  answer?: ExpertAnswer;
};

export type KbEntry = {
  id: string;
  question: string;
  answer: string;
  expertId: string;
  publishedAt: string;
  /** Wiki page title this entry is attached to, for the RM-facing trust badge. */
  sourceTitle: string;
  endorsedBy: string[];
  flaggedBy: string[];
};

export type ReviewItem = {
  id: string;
  kind: "contradiction" | "thumbs_down";
  supervisorId: string;
  expertId: string;
  question: string;
  answer: string;
  wikiExcerpt: string;
  kbEntryId?: string;
  status: "open" | "kept" | "updated";
  createdAt: string;
};

export type Notification = {
  id: string;
  kind: "kb" | "message";
  title: string;
  body: string;
  at: string;
  read: boolean;
  /** Undefined = everyone. */
  forExpertId?: string;
  forRm?: boolean;
  /** Deep links: kb notifications carry an entry, message ones a thread. */
  kbEntryId?: string;
  messageId?: string;
};

const WIKI_EXCERPT =
  "Suitability Wiki — Cross-Border Product Matrix: a Reverse Convertible may be marketed to a Professional client domiciled in Germany only where the meeting takes place on German premises and the note appears on the EU-approved distribution list.";

function id(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 8)}`;
}

function seed(
  base: Omit<EscalationMessage, "expertId" | "routing">,
): EscalationMessage {
  const routing = routeQuestion(base.context, { now: new Date(base.askedAt) });
  return { ...base, expertId: routing.expertId, routing };
}

const SEED_MESSAGES: EscalationMessage[] = [
  seed({
    id: "msg_5001",
    question:
      "Does a CH-booked client relocating to Monaco need reclassification before the next advisory review?",
    context: { bookingCentre: "Monaco", clientCategory: "Private/Retail", serviceModel: "Advisory" },
    askedBy: "A. Brunner",
    askedAt: "2026-09-01T07:40:00Z",
    status: "pending",
  }),
  seed({
    id: "msg_5002",
    question:
      "Can a research note on a US-listed structured note be forwarded to an Execution-only client in Dubai?",
    context: { bookingCentre: "Other", clientCategory: "Professional", serviceModel: "Execution-only" },
    askedBy: "L. Ferrari",
    askedAt: "2026-09-01T09:15:00Z",
    status: "pending",
  }),
  seed({
    id: "msg_5003",
    question:
      "Is a Knowledge & Experience check required for a German-domiciled Professional client buying a fund of funds?",
    context: { bookingCentre: "Germany", clientCategory: "Professional", serviceModel: "Advisory" },
    askedBy: "A. Brunner",
    askedAt: "2026-08-31T13:20:00Z",
    status: "answered",
    answer: {
      text: "No separate K&E questionnaire is required: the Professional classification carries a presumption of knowledge and experience for non-complex funds, including funds of funds. Record the reliance on the classification in the advisory note; if the client later opts down to Retail, the presumption falls away and a fresh K&E check is needed before the next recommendation.",
      answeredAt: "2026-08-31T15:02:00Z",
      publishedToKb: true,
      contradictsWiki: false,
      kbEntryId: "kb_2001",
    },
  }),
];

const SEED_KB: KbEntry[] = [
  {
    id: "kb_2001",
    question:
      "Is a Knowledge & Experience check required for a German-domiciled Professional client buying a fund of funds?",
    answer:
      "No separate K&E questionnaire is required: the Professional classification carries a presumption of knowledge and experience for non-complex funds. Record the reliance on the classification in the advisory note.",
    expertId: "sophie-wyss",
    publishedAt: "2026-08-31T15:04:00Z",
    sourceTitle: "Suitability Wiki — Knowledge & Experience Presumptions",
    endorsedBy: ["marco-steiner", "clara-suter"],
    flaggedBy: [],
  },
  {
    id: "kb_2002",
    question: "Which alerts must be cleared before executing a trade for a Retail client?",
    answer:
      "Concentration, risk-profile breach and complex-product alerts must all be cleared or overridden with a documented reason before release. An override requires a second pair of eyes at Business Front Support level.",
    expertId: "daniel-frei",
    publishedAt: "2026-08-28T10:12:00Z",
    sourceTitle: "Suitability Wiki — Pre-Trade Alerts",
    endorsedBy: ["nina-aebi"],
    flaggedBy: [],
  },
];

const SEED_REVIEWS: ReviewItem[] = [
  {
    id: "rev_3001",
    kind: "contradiction",
    supervisorId: "lukas-baumann",
    expertId: "marco-steiner",
    question:
      "Can I market a Reverse Convertible to a German-domiciled Professional client during a Zurich meeting?",
    answer:
      "Yes — where the client travels to Zurich at their own initiative and the meeting takes place on Swiss premises, the reverse-solicitation carve-out applies and the note may be discussed even though it is not on the EU-approved list. Document the client's initiative in the call report.",
    wikiExcerpt: WIKI_EXCERPT,
    status: "open",
    createdAt: "2026-09-01T11:30:00Z",
  },
];

const SEED_NOTIFICATIONS: Notification[] = [
  {
    id: "ntf_4001",
    kind: "kb",
    title: "New information added to the knowledge base",
    body: "Sophie Wyss published guidance on K&E presumptions for Professional clients.",
    at: "2026-08-31T15:04:00Z",
    read: false,
    kbEntryId: "kb_2001",
  },
  {
    id: "ntf_4002",
    kind: "message",
    title: "Your escalation was answered",
    body: "Sophie Wyss answered your question on K&E checks for German-domiciled Professional clients.",
    at: "2026-08-31T15:02:00Z",
    read: false,
    forRm: true,
    messageId: "msg_5003",
  },
  {
    id: "ntf_4003",
    kind: "message",
    title: "New escalation routed to you",
    body: "A. Brunner escalated a Monaco reclassification question.",
    at: "2026-09-01T07:40:00Z",
    read: false,
    forExpertId: "marco-steiner",
    messageId: "msg_5001",
  },
];

type ExpertStore = {
  messages: EscalationMessage[];
  kbEntries: KbEntry[];
  reviews: ReviewItem[];
  notifications: Notification[];
  favorabilityDelta: Record<string, number>;
  favorabilityOf: (expert: Expert) => number;
  sendEscalation: (input: {
    question: string;
    context: QueryContext;
    askedBy: string;
    expertId?: string;
    routing?: RoutingDecision;
  }) => string;
  answerEscalation: (
    messageId: string,
    text: string,
    opts?: { contradictsWiki?: boolean },
  ) => void;
  publishAnswer: (messageId: string) => void;
  reactToKb: (kbEntryId: string, expertId: string, direction: "up" | "down") => void;
  decideReview: (reviewId: string, decision: "kept" | "updated") => void;
  markNotificationsRead: () => void;
  markNotificationRead: (id: string) => void;
  notificationsFor: (who: { kind: "rm" | "expert"; expertId?: string }) => Notification[];
  kbForSource: (sourceTitle: string) => KbEntry | undefined;
  triggerDemoKbNotification: () => void;
};

const Ctx = createContext<ExpertStore | null>(null);

export function ExpertProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<EscalationMessage[]>(SEED_MESSAGES);
  const [kbEntries, setKbEntries] = useState<KbEntry[]>(SEED_KB);
  const [reviews, setReviews] = useState<ReviewItem[]>(SEED_REVIEWS);
  const [notifications, setNotifications] = useState<Notification[]>(SEED_NOTIFICATIONS);
  const [favorabilityDelta, setFavorabilityDelta] = useState<Record<string, number>>({});

  const notify = useCallback((n: Omit<Notification, "id" | "at" | "read">) => {
    setNotifications((prev) => [
      { ...n, id: id("ntf"), at: new Date().toISOString(), read: false },
      ...prev,
    ]);
  }, []);

  const sendEscalation = useCallback<ExpertStore["sendEscalation"]>(
    ({ question, context, askedBy, expertId, routing }) => {
      const decision = routing ?? routeQuestion(context);
      const targetId = expertId ?? decision.expertId;
      const messageId = id("msg");
      setMessages((prev) => [
        {
          id: messageId,
          question,
          context,
          askedBy,
          askedAt: new Date().toISOString(),
          expertId: targetId,
          routing: decision,
          status: "pending",
        },
        ...prev,
      ]);
      notify({
        kind: "message",
        title: "New escalation routed to you",
        body: `${askedBy} escalated: ${question}`,
        forExpertId: targetId,
        messageId,
      });
      return messageId;
    },
    [notify],
  );

  const answerEscalation = useCallback<ExpertStore["answerEscalation"]>(
    (messageId, text, opts) => {
      const contradicts = !!opts?.contradictsWiki;
      let target: EscalationMessage | undefined;
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== messageId) return m;
          target = m;
          return {
            ...m,
            status: "answered",
            answer: {
              text,
              answeredAt: new Date().toISOString(),
              publishedToKb: false,
              contradictsWiki: contradicts,
            },
          };
        }),
      );
      if (!target) return;
      const expert = getExpert(target.expertId);
      notify({
        kind: "message",
        title: "Your escalation was answered",
        body: `${expert?.name ?? "An expert"} answered: ${target.question}`,
        forRm: true,
        messageId,
      });
      if (contradicts && expert) {
        const supervisor = supervisorOf(expert);
        if (supervisor) {
          setReviews((prev) => [
            {
              id: id("rev"),
              kind: "contradiction",
              supervisorId: supervisor.id,
              expertId: expert.id,
              question: target!.question,
              answer: text,
              wikiExcerpt: WIKI_EXCERPT,
              status: "open",
              createdAt: new Date().toISOString(),
            },
            ...prev,
          ]);
          notify({
            kind: "message",
            title: "Contradiction flagged for your decision",
            body: `${expert.name}'s answer conflicts with existing wiki guidance.`,
            forExpertId: supervisor.id,
          });
        }
      }
    },
    [notify],
  );

  const publishAnswer = useCallback<ExpertStore["publishAnswer"]>(
    (messageId) => {
      const message = messages.find((m) => m.id === messageId);
      if (!message?.answer) return;
      const entryId = id("kb");
      const expert = getExpert(message.expertId);
      setKbEntries((prev) => [
        {
          id: entryId,
          question: message.question,
          answer: message.answer!.text,
          expertId: message.expertId,
          publishedAt: new Date().toISOString(),
          sourceTitle: "Suitability Wiki — Expert Contributions",
          endorsedBy: [],
          flaggedBy: [],
        },
        ...prev,
      ]);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId && m.answer
            ? { ...m, status: "resolved", answer: { ...m.answer, publishedToKb: true, kbEntryId: entryId } }
            : m,
        ),
      );
      notify({
        kind: "kb",
        title: "New information added to the knowledge base",
        body: `${expert?.name ?? "An expert"} published: ${message.question}`,
        kbEntryId: entryId,
      });
    },
    [messages, notify],
  );

  const reactToKb = useCallback<ExpertStore["reactToKb"]>(
    (kbEntryId, expertId, direction) => {
      const entry = kbEntries.find((e) => e.id === kbEntryId);
      if (!entry) return;
      const author = getExpert(entry.expertId);

      if (direction === "up") {
        if (entry.endorsedBy.includes(expertId)) return;
        setKbEntries((prev) =>
          prev.map((e) =>
            e.id === kbEntryId ? { ...e, endorsedBy: [...e.endorsedBy, expertId] } : e,
          ),
        );
        setFavorabilityDelta((prev) => ({
          ...prev,
          [entry.expertId]: (prev[entry.expertId] ?? 0) + 2,
        }));
        return;
      }

      if (entry.flaggedBy.includes(expertId)) return;
      setKbEntries((prev) =>
        prev.map((e) => (e.id === kbEntryId ? { ...e, flaggedBy: [...e.flaggedBy, expertId] } : e)),
      );
      setFavorabilityDelta((prev) => ({
        ...prev,
        [entry.expertId]: (prev[entry.expertId] ?? 0) - 3,
      }));
      const supervisor = author ? supervisorOf(author) : undefined;
      if (supervisor) {
        setReviews((prev) => [
          {
            id: id("rev"),
            kind: "thumbs_down",
            supervisorId: supervisor.id,
            expertId: entry.expertId,
            question: entry.question,
            answer: entry.answer,
            wikiExcerpt: WIKI_EXCERPT,
            kbEntryId: entry.id,
            status: "open",
            createdAt: new Date().toISOString(),
          },
          ...prev,
        ]);
        notify({
          kind: "message",
          title: "KB contribution flagged for review",
          body: `A published answer by ${author?.name ?? "an expert"} was flagged by a peer.`,
          forExpertId: supervisor.id,
        });
      }
    },
    [kbEntries, notify],
  );

  const decideReview = useCallback<ExpertStore["decideReview"]>(
    (reviewId, decision) => {
      const review = reviews.find((r) => r.id === reviewId);
      if (!review) return;
      setReviews((prev) => prev.map((r) => (r.id === reviewId ? { ...r, status: decision } : r)));
      if (decision === "updated") {
        const expert = getExpert(review.expertId);
        if (review.kbEntryId) {
          setKbEntries((prev) =>
            prev.map((e) =>
              e.id === review.kbEntryId ? { ...e, answer: review.answer, flaggedBy: [] } : e,
            ),
          );
        } else {
          setKbEntries((prev) => [
            {
              id: id("kb"),
              question: review.question,
              answer: review.answer,
              expertId: review.expertId,
              publishedAt: new Date().toISOString(),
              sourceTitle: "Suitability Wiki — Expert Contributions",
              endorsedBy: [review.supervisorId],
              flaggedBy: [],
            },
            ...prev,
          ]);
        }
        notify({
          kind: "kb",
          title: "New information added to the knowledge base",
          body: `Wiki guidance was updated with ${expert?.name ?? "an expert"}'s answer after supervisor review.`,
        });
      }
    },
    [reviews, notify],
  );

  const value = useMemo<ExpertStore>(
    () => ({
      messages,
      kbEntries,
      reviews,
      notifications,
      favorabilityDelta,
      favorabilityOf: (expert) =>
        Math.max(0, Math.min(100, expert.favorability + (favorabilityDelta[expert.id] ?? 0))),
      sendEscalation,
      answerEscalation,
      publishAnswer,
      reactToKb,
      decideReview,
      markNotificationsRead: () =>
        setNotifications((prev) => prev.map((n) => ({ ...n, read: true }))),
      markNotificationRead: (notificationId) =>
        setNotifications((prev) =>
          prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n)),
        ),
      notificationsFor: ({ kind, expertId }) =>
        notifications.filter((n) => {
          if (n.forRm) return kind === "rm";
          if (n.forExpertId) return kind === "expert" && n.forExpertId === expertId;
          return true;
        }),
      kbForSource: (sourceTitle) =>
        kbEntries.find((e) => e.sourceTitle.toLowerCase() === sourceTitle.toLowerCase()),
      triggerDemoKbNotification: () =>
        notify({
          kind: "kb",
          title: "New information added to the knowledge base",
          body: "A new expert contribution is now available to all Relationship Managers.",
        }),
    }),
    [
      messages,
      kbEntries,
      reviews,
      notifications,
      favorabilityDelta,
      sendEscalation,
      answerEscalation,
      publishAnswer,
      reactToKb,
      decideReview,
      notify,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useExperts() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useExperts must be used within ExpertProvider");
  return ctx;
}
