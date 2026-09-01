import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

const KEY = "sc-session";

export type DemoUser = {
  id: string;
  name: string;
  role: string;
  kind: "rm" | "expert";
  tier?: string;
};

export const DEMO_USERS: DemoUser[] = [
  { id: "rm_001", name: "A. Brunner", role: "RM, Zurich", kind: "rm" },
  { id: "rm_002", name: "L. Ferrari", role: "RM, Monaco", kind: "rm" },
  { id: "rm_003", name: "S. Keller", role: "Team Head, Geneva", kind: "rm" },
];

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
        if (parsed?.name) setUser({
          id: parsed.id ?? parsed.name,
          name: parsed.name,
          role: parsed.role ?? "",
          kind: parsed.kind ?? "rm",
          ...(parsed.tier ? { tier: parsed.tier } : {}),
        });
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
