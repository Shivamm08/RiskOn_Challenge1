import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { askSuitability } from "./ask";
import { SEED_AUDIT, SEED_EXCHANGES } from "./seed";
import type { ChatMessage, Exchange, QueryContext, SourceFileType, SourceRef } from "./types";
import { useAuth } from "@/lib/auth";

type ActiveCitation = { source: SourceRef; exchangeId: string } | null;

export type KnowledgeSource = {
  name: string;
  ref: string;
  connected: boolean;
  active?: boolean;
  fileType?: SourceFileType;
  url?: string | null;
};

export type Chat = { id: string; title: string; exchanges: Exchange[] };

const DEFAULT_SOURCES: KnowledgeSource[] = [
  {
    name: "Suitability Wiki",
    ref: "internal://suitability-wiki",
    connected: true,
    active: true,
    fileType: "link",
    url: "https://intranet.juliusbaer.com/wiki/suitability",
  },
  {
    name: "Cross-Border Product Matrix",
    ref: "internal://product-matrix.xlsx",
    connected: true,
    active: true,
    fileType: "excel",
  },
  {
    name: "Suitability Policy Handbook",
    ref: "internal://suitability-policy.pdf",
    connected: true,
    active: false,
    fileType: "pdf",
  },
  {
    name: "Additional JB knowledge bases (expanding)",
    ref: "internal://pending",
    connected: false,
    active: false,
    fileType: "doc",
  },
];

const NEW_CHAT_TITLE = "New chat";

function chatTitle(question: string) {
  const q = question.trim();
  return q.length > 44 ? `${q.slice(0, 41).trimEnd()}…` : q;
}

function newChat(): Chat {
  return {
    id: `chat_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    title: NEW_CHAT_TITLE,
    exchanges: [],
  };
}

type Store = {
  /** Exchanges currently rendered in the Copilot view. */
  thread: Exchange[];
  demoExchanges: Exchange[];
  chats: Chat[];
  activeChatId: string | null;
  viewingDemo: boolean;
  startNewChat: () => void;
  selectChat: (id: string) => void;
  showDemo: () => void;
  auditRecords: Exchange[];
  context: QueryContext;
  setContext: (next: QueryContext) => void;
  pendingQuestion: string | null;
  ask: (question: string) => Promise<void>;
  activeCitation: ActiveCitation;
  openCitation: (source: SourceRef, exchangeId: string) => void;
  closeCitation: () => void;
  resolveExchange: (id: string, note: string, resolvedBy: string) => void;
  knowledgeSources: KnowledgeSource[];
  addKnowledgeSource: (source: KnowledgeSource) => void;
  toggleKnowledgeSource: (ref: string) => void;
  previewSource: SourceRef | null;
  openSource: (source: SourceRef) => void;
  closePreview: () => void;
};

const StoreContext = createContext<Store | null>(null);

export function SuitabilityProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [demo, setDemo] = useState<Exchange[]>(SEED_EXCHANGES);
  const [extraAudit, setExtraAudit] = useState<Exchange[]>(SEED_AUDIT);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [context, setContext] = useState<QueryContext>({});
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<ActiveCitation>(null);
  const [knowledgeSources, setKnowledgeSources] =
    useState<KnowledgeSource[]>(DEFAULT_SOURCES);
  const [previewSource, setPreviewSource] = useState<SourceRef | null>(null);

  const startNewChat = useCallback(() => {
    const chat = newChat();
    setChats((prev) => [...prev, chat]);
    setActiveChatId(chat.id);
    setActiveCitation(null);
  }, []);

  const selectChat = useCallback((id: string) => {
    setActiveChatId(id);
    setActiveCitation(null);
  }, []);

  const showDemo = useCallback(() => {
    setActiveChatId(null);
  }, []);

  const ask = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed) return;

      // Asking while the demo scenario is showing starts a fresh live chat.
      let chatId = activeChatId;
      if (!chatId) {
        const chat = newChat();
        chatId = chat.id;
        setChats((prev) => [...prev, chat]);
        setActiveChatId(chat.id);
      }

      setPendingQuestion(trimmed);
      const currentContext = context;
      const activeExchanges = chats.find((chat) => chat.id === chatId)?.exchanges ?? [];
      const history: ChatMessage[] = activeExchanges.slice(-3).flatMap((exchange) => {
        const assistantContent =
          exchange.response.answer ?? exchange.response.clarification_question;
        return [
          { role: "user" as const, content: exchange.question },
          ...(assistantContent
            ? [{ role: "assistant" as const, content: assistantContent }]
            : []),
        ];
      });
      try {
        const response = await askSuitability(trimmed, currentContext, history);
        const exchange: Exchange = {
          id: response.request_id,
          question: trimmed,
          askedAt: new Date().toISOString(),
          askedBy: user?.name ?? "Unknown user",
          context: currentContext,
          response,
        };
        setChats((prev) =>
          prev.map((c) =>
            c.id === chatId
              ? {
                  ...c,
                  title: c.exchanges.length === 0 ? chatTitle(trimmed) : c.title,
                  exchanges: [...c.exchanges, exchange],
                }
              : c,
          ),
        );
      } finally {
        setPendingQuestion(null);
      }
    },
    [activeChatId, chats, context, user],
  );

  const resolveExchange = useCallback((id: string, note: string, resolvedBy: string) => {
    const resolution = { resolvedBy, note, resolvedAt: new Date().toISOString() };
    const apply = (list: Exchange[]) =>
      list.map((e) => (e.id === id ? { ...e, resolution } : e));
    setDemo(apply);
    setExtraAudit(apply);
    setChats((prev) => prev.map((c) => ({ ...c, exchanges: apply(c.exchanges) })));
  }, []);

  const addKnowledgeSource = useCallback((source: KnowledgeSource) => {
    setKnowledgeSources((prev) => [...prev, { active: true, ...source }]);
  }, []);

  const toggleKnowledgeSource = useCallback((ref: string) => {
    setKnowledgeSources((prev) =>
      prev.map((s) => (s.ref === ref ? { ...s, active: !s.active } : s)),
    );
  }, []);

  const openSource = useCallback((source: SourceRef) => {
    const type: SourceFileType = source.fileType ?? (source.url ? "link" : "doc");
    if (type === "link" && source.url) {
      window.open(source.url, "_blank", "noopener,noreferrer");
      return;
    }
    setPreviewSource(source);
  }, []);

  const auditRecords = useMemo(
    () =>
      [...chats.flatMap((c) => c.exchanges), ...demo, ...extraAudit].sort(
        (a, b) => new Date(b.askedAt).getTime() - new Date(a.askedAt).getTime(),
      ),
    [chats, demo, extraAudit],
  );

  const thread = useMemo(() => {
    if (!activeChatId) return demo;
    return chats.find((c) => c.id === activeChatId)?.exchanges ?? [];
  }, [activeChatId, chats, demo]);

  const value = useMemo<Store>(
    () => ({
      thread,
      demoExchanges: demo,
      chats,
      activeChatId,
      viewingDemo: activeChatId === null,
      startNewChat,
      selectChat,
      showDemo,
      auditRecords,
      context,
      setContext,
      pendingQuestion,
      ask,
      activeCitation,
      openCitation: (source, exchangeId) => setActiveCitation({ source, exchangeId }),
      closeCitation: () => setActiveCitation(null),
      resolveExchange,
      knowledgeSources,
      addKnowledgeSource,
      toggleKnowledgeSource,
      previewSource,
      openSource,
      closePreview: () => setPreviewSource(null),
    }),
    [
      thread,
      demo,
      chats,
      activeChatId,
      startNewChat,
      selectChat,
      showDemo,
      auditRecords,
      context,
      pendingQuestion,
      ask,
      activeCitation,
      resolveExchange,
      knowledgeSources,
      addKnowledgeSource,
      toggleKnowledgeSource,
      previewSource,
      openSource,
    ],
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useSuitability() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useSuitability must be used within SuitabilityProvider");
  return ctx;
}
