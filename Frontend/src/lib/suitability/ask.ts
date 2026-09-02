import type { AskResponse, QueryContext } from "./types";

/** Send a live query to the FastAPI service backed by the competition Wiki. */
export async function askSuitability(
  question: string,
  context: QueryContext,
): Promise<AskResponse> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
  const response = await fetch(`${apiBase}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, context }),
  });
  if (!response.ok) throw new Error(`Suitability API returned ${response.status}`);
  return (await response.json()) as AskResponse;
}
