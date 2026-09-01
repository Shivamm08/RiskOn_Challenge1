import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { EXPERTS } from "@/lib/experts/roster";

const KEY = "sc-session";

export type UserKind = "rm" | "expert";

export type DemoUser = { name: string; role: string; kind: UserKind; expertId?: string };

/** Invented demo profile detail for RM users, keyed by name. */
export type RmProfile = {
  office: string;
  yearsAtJb: number;
  clientSegment: string;
  languages: string[];
  specialization: string;
};

export const RM_PROFILES: Record<string, RmProfile> = {
  "A. Brunner": {
    office: "Zurich, Bahnhofstrasse",
    yearsAtJb: 11,
    clientSegment: "Private & Elected Professional clients, CH and Monaco",
    languages: ["German", "English", "French"],
    specialization: "Structured products, cross-border advisory",
  },
  "L. Ferrari": {
    office: "Monaco, Avenue de Monte-Carlo",
    yearsAtJb: 7,
    clientSegment: "Professional clients and family offices, Monaco and Italy",
    languages: ["Italian", "French", "English"],
    specialization: "Discretionary mandates, alternative investments",
  },
  "S. Keller": {
    office: "Geneva, Rue du Rhône",
    yearsAtJb: 16,
    clientSegment: "UHNW families, CH and EEA",
    languages: ["French", "German", "English"],
    specialization: "Team supervision, complex product approvals",
  },
};

export const DEFAULT_RM_PROFILE: RmProfile = {
  office: "Zurich, Bahnhofstrasse",
  yearsAtJb: 5,
  clientSegment: "Private & Elected Professional clients, CH",
  languages: ["German", "English"],
  specialization: "Advisory suitability, cross-border basics",
};

export function rmProfileFor(name: string): RmProfile {
  return RM_PROFILES[name] ?? DEFAULT_RM_PROFILE;
}

export const DEMO_USERS: DemoUser[] = [
  { name: "A. Brunner", role: "RM, Zurich", kind: "rm" },
  { name: "L. Ferrari", role: "RM, Monaco", kind: "rm" },
  { name: "S. Keller", role: "Team Head, Geneva", kind: "rm" },
];

/**
 * Curated expert quick sign-ins. Deliberately small: these three cover the full
 * demo loop (escalation → answer → KB publish → supervisor review).
 * The rest of the roster is still routable and shown in reasoning.
 */
export const DEMO_EXPERT_USERS: DemoUser[] = ["nina-aebi", "marco-steiner", "lukas-baumann"]
  .map((id) => EXPERTS.find((e) => e.id === id))
  .filter((e): e is (typeof EXPERTS)[number] => !!e)
  .map((e) => ({
    name: e.name,
    role: `${e.rank} · ${e.office}`,
    kind: "expert" as const,
    expertId: e.id,
  }));


type AuthStore = {
  user: DemoUser | null;
  ready: boolean;
  signIn: (user: DemoUser) => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthStore | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DemoUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as DemoUser;
        if (parsed?.name) {
          setUser({
            name: parsed.name,
            role: parsed.role ?? "",
            kind: parsed.kind === "expert" ? "expert" : "rm",
            ...(parsed.expertId ? { expertId: parsed.expertId } : {}),
          });
        }
      }
    } catch {
      /* ignore corrupted session */
    }
    setReady(true);
  }, []);

  const signIn = useCallback((next: DemoUser) => {
    setUser(next);
    window.localStorage.setItem(KEY, JSON.stringify(next));
  }, []);

  const signOut = useCallback(() => {
    setUser(null);
    window.localStorage.removeItem(KEY);
  }, []);

  const value = useMemo<AuthStore>(
    () => ({ user, ready, signIn, signOut }),
    [user, ready, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
