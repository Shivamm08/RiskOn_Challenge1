import type { AskResponse, QueryContext } from "./types";

const API_BASE =
  import.meta.env["VITE_API_BASE_URL"] ??
  import.meta.env["VITE_API_URL"] ??
  "http://localhost:8000";

export async function askSuitability(
  question: string,
  context: QueryContext,
  history: Array<{ role: "user" | "assistant"; content: string }> = [],
): Promise<AskResponse> {
  const trimmed = question.trim();
  if (!trimmed) {
    throw new Error("Question is required.");
  }

  const response = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: trimmed,
      context,
      conversation: history,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Ask failed (${response.status}): ${errorText}`);
  }

  return (await response.json()) as AskResponse;
}
