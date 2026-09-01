# Suitability Guide

Build "Suitability Copilot" — an internal AI assistant for Julius Baer Relationship Managers (RMs) to get instant, source-cited answers to client-suitability and compliance questions, or be routed to the right human expert when the AI can't confidently answer.

## PRODUCT CONTEXT

This is an internal banking tool, not a consumer app. The user is a busy, professional Relationship Manager mid-conversation with a client, or preparing for one. They need fast, trustworthy, precisely-sourced answers — never a guess. Every single answer must be traceable back to an exact source document, and every escalation must show exactly why and to whom. Think "compliance-grade," not "chatty consumer AI."

## VISUAL IDENTITY

- Professional private-banking aesthetic: dark charcoal (#1A1A1A) and warm gold (#B8860B) as primary brand colors, with a warm cream/gold-tinted neutral (#F2E9D8) for soft backgrounds and highlight cards.

- Status colors: confident/answered = green (#2E7D46 / #E4F5E9 background), escalated = deep red (#B03A3A / #FBE4E4 background), informational/data = blue (#3A5FA0 / #E7EEF9 background).

- Typography: clean serif or high-quality sans-serif for headings (confident, editorial, private-bank feel — think Bloomberg Terminal meets a Swiss private bank, not a startup chat app), simple sans-serif for body text.

- Generous whitespace, understated, no gradients or playful illustration. Subtle, precise, trustworthy — never flashy.

- Dark mode as default (matches the "terminal for professionals" feel); allow toggle to light mode.

## SCREENS

### 1. Main Chat / Co-Pilot View (primary screen)

- Central chat interface, RM types a question and hits send (or Enter).

- Above the input: a collapsible "Context" bar where the RM can optionally set: Booking Centre (dropdown: CH, Monaco, Germany, EEA, Other), Client Category (Private/Retail, Professional, Institutional), Service Model (Advisory, Execution-only, Portfolio Management). These are optional filters that refine the answer — show a small "context applied" chip once set.

- Each RM message appears as a right-aligned bubble; each system response appears as a left-aligned card (not a plain bubble — responses are structured, see below).

- Below the input: a few clickable example questions to help first-time users (e.g. "Can I recommend a structured product to a Professional client in Monaco?", "What alerts apply before executing a trade for a Retail client?").

### 2. Response Card — three distinct visual states (this is the most important part of the whole app)

**State A: Answered (confident)**

- Green-accented card.

- The answer text, written plainly.

- A "Confidence" indicator — a small horizontal bar or percentage badge (e.g. 92%), green if high, amber if medium.

- A "Sources" section below the answer: one or more source chips, each showing the Wiki page title and a short excerpt on hover/click. Clicking a source chip expands a side panel showing the exact excerpt that supports the answer, styled like a citation/footnote — this is critical, must feel like a legal citation, not a vague "learn more" link.

- A small "Why this answer" toggle that expands to show the reasoning trail: what was checked, why it was judged in-scope and sufficient.

**State B: Escalated (needs a human)**

- Red/amber-accented card.

- Clear headline: "I can't confidently answer this — here's who can help."

- An expert recommendation block: name, role, team, and a plain-language reason why this specific person/team was chosen (e.g. "This involves a cross-border CH/Monaco classification question not covered in the wiki — routing to the BRM Suitability Lead for Western Markets & Switzerland").

- Show the escalation tier visually as a small horizontal ladder/breadcrumb: Wiki → Suitability Champion → Business Front Support → BRM Suitability Lead → Suitability Expert — with the selected tier highlighted, so the RM understands where in the chain this sits.

- A visible fallback note: "If [name] is unavailable, contact [supervisor/team lead]" — always show a fallback contact, never a dead end.

- A "Notify this expert" button (visually present, can be non-functional/mocked for now) and a "Mark as resolved" button for when the RM later gets an answer from the expert (this feeds the audit log).

**State C: Needs clarification**

- Neutral/blue-accented card.

- A clarifying question back to the RM (e.g. "Which jurisdiction is the client based in — this changes which rule applies").

- A quick-reply row of likely answers as clickable chips, plus a free-text option.

### 3. Audit Trail / Source Log (secondary screen, accessible from a sidebar icon)

- A searchable, filterable table/list of every question ever asked: timestamp, RM, question, status (answered/escalated/clarification), confidence score, sources used, and resolution if escalated.

- Each row expands to show the full detail: exact source excerpts cited, full escalation reasoning, and (if resolved) who resolved it and what they said.

- This screen should feel like a compliance officer's review tool — clean, dense, exportable (show an "Export" button, can be non-functional).

- This is a key differentiator for the demo — make it feel genuinely rigorous, not an afterthought.

### 4. Sidebar

- Recent questions (last ~10, clickable to revisit).

- Link to the Audit Trail screen.

- A small "Knowledge Sources Connected" indicator showing what's connected: "Suitability Wiki ✓", "Additional JB Knowledge Bases (expanding)" — signals extensibility without overclaiming.

## MOCK DATA — use this exact shape for all sample/dummy data (this will later be replaced by a real API)

```json

{

  "request_id": "string",

  "status": "answered | escalated | clarification_needed",

  "answer": "string or null",

  "confidence": { "answer_confidence": 0.0, "routing_confidence": 0.0 },

  "sources": [{ "page_title": "string", "excerpt": "string", "url": "string or null" }],

  "scope_flags": ["string"],

  "escalation": {

    "required": true or false,

    "tier": "wiki | suitability_champion | business_front_support | brm_suitability_lead | suitability_expert",

    "expert": { "name": "string", "role": "string", "team": "string" },

    "reason": "string",

    "fallback_contact": { "name": "string", "role": "string" }

  },

  "clarification_question": "string or null"

}

```

Populate the UI with 4-5 realistic mock exchanges covering all three states, using believable Swiss private banking suitability questions (client classification, K&E checks, cross-border CH/Monaco/Germany rules, structured product alerts, execution-only vs advisory).

## TECHNICAL NOTES

- Build as a React app with clean component structure (separate components for ChatInput, ResponseCard-Answered, ResponseCard-Escalated, ResponseCard-Clarification, SourceCitation, AuditTrailTable, ContextBar).

- State management can be local/mocked for now — structure it so a real fetch() call to a backend `/ask` endpoint can be dropped in later with minimal changes.

- Fully responsive but optimized for desktop/laptop use (this is a workplace tool, not primarily mobile).

- Keep it fast and uncluttered — no unnecessary animation, no marketing-style hero sections. This opens straight into the tool.

## TONE OF ALL COPY

Precise, calm, professional. Never casual, never over-explains. Think "trusted compliance colleague," not "friendly chatbot." Never say "I think" or "maybe" — either state the answer with its confidence level, or clearly state it cannot answer and who can.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/19c1d8d3-b6ea-4c73-89cb-7b64f1b5e083).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
