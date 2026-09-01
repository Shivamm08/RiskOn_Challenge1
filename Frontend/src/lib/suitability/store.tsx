import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { askSuitability } from "./ask";
import { CURRENT_RM, SEED_AUDIT, SEED_EXCHANGES } from "./seed";
import type { Exchange, QueryContext, SourceRef } from "./types";

type ActiveCitation = { source: SourceRef; exchangeId: string } | null;

export type KnowledgeSource = { name: string; ref: string; connected: boolean };

const DEFAULT_SOURCES: KnowledgeSource[] = [
  { name: "Suitability Wiki", ref: "internal://suitability-wiki", connected: true },
  {
    name: "Additional JB knowledge bases (expanding)",
    ref: "internal://pending",
    connected: false,
  },
];

type Store = {
  thread: Exchange[];
  demoExchanges: Exchange[];
  liveExchanges: Exchange[];
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
};

const StoreContext = createContext<Store | null>(null);

export function SuitabilityProvider({ children }: { children: ReactNode }) {
  const [thread, setThread] = useState<Exchange[]>(SEED_EXCHANGES);
  const [extraAudit, setExtraAudit] = useState<Exchange[]>(SEED_AUDIT);
  const [liveIds, setLiveIds] = useState<string[]>([]);
  const [context, setContext] = useState<QueryContext>({});
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<ActiveCitation>(null);
  const [knowledgeSources, setKnowledgeSources] =
    useState<KnowledgeSource[]>(DEFAULT_SOURCES);


  const ask = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed) return;
      setPendingQuestion(trimmed);
      const currentContext = context;
      try {
        const response = await askSuitability(trimmed, currentContext);
        setThread((prev) => [
          ...prev,
          {
            id: response.request_id,
            question: trimmed,
            askedAt: new Date().toISOString(),
            askedBy: CURRENT_RM,
            context: currentContext,
            response,
          },
        ]);
        setLiveIds((prev) => [...prev, response.request_id]);
      } finally {
        setPendingQuestion(null);
      }
    },
    [context],
  );

  const resolveExchange = useCallback((id: string, note: string, resolvedBy: string) => {
    const resolution = { resolvedBy, note, resolvedAt: new Date().toISOString() };
    const apply = (list: Exchange[]) =>
      list.map((e) => (e.id === id ? { ...e, resolution } : e));
    setThread(apply);
    setExtraAudit(apply);
  }, []);

  const addKnowledgeSource = useCallback((source: KnowledgeSource) => {
    setKnowledgeSources((prev) => [...prev, source]);
  }, []);

  const auditRecords = useMemo(
    () =>
      [...thread, ...extraAudit].sort(
        (a, b) => new Date(b.askedAt).getTime() - new Date(a.askedAt).getTime(),
      ),
    [thread, extraAudit],
  );

  const demoExchanges = useMemo(
    () => thread.filter((e) => !liveIds.includes(e.id)),
    [thread, liveIds],
  );
  const liveExchanges = useMemo(
    () => thread.filter((e) => liveIds.includes(e.id)),
    [thread, liveIds],
  );

  const value = useMemo<Store>(
    () => ({
      thread,
      demoExchanges,
      liveExchanges,
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
    }),
    [
      thread,
      demoExchanges,
      liveExchanges,
      auditRecords,
      context,
      pendingQuestion,
      ask,
      activeCitation,
      resolveExchange,
      knowledgeSources,
      addKnowledgeSource,
    ],
  );


  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useSuitability() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useSuitability must be used within SuitabilityProvider");
  return ctx;
}
