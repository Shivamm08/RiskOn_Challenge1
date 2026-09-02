import type { AskResponse, ChatMessage, QueryContext } from "./types";

/**
 * Single entry point for answering a question.
 *
 * Questions always go through the backend so responses are grounded in the
 * real documents under pages/. VITE_API_URL can override the local default.
 */
export async function askSuitability(
  question: string,
  context: QueryContext,
  history: ChatMessage[] = [],
  requester?: { id: string; name: string },
): Promise<AskResponse> {
  const apiUrl = (import.meta.env["VITE_API_URL"] as string | undefined) ?? "http://localhost:8000";
  const response = await fetch(`${apiUrl.replace(/\/$/, "")}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      context,
      history,
      requester_id: requester?.id,
      requester_name: requester?.name,
    }),
  });
  if (!response.ok) {
    throw new Error(`Suitability API returned ${response.status}`);
  }
  return (await response.json()) as AskResponse;
}
