# Suitability Copilot Workflows

This document describes how the Copilot handles each possible request outcome.

## Common request flow

Every question starts with the following steps:

1. The frontend sends the question, recent conversation history, requester details,
   and optional client context to `POST /ask`.
2. The query-rewriting LLM decides whether the request is in scope and rewrites
   follow-ups into a self-contained question.
3. The rewritten question preserves relevant details such as the country, booking
   centre, client category, service model, product, and previous question.
4. The backend checks approved expert knowledge and the real HTML documents in
   `pages/`.
5. The grounded-answer LLM decides whether the evidence directly and sufficiently
   answers the self-contained question.
6. The request is answered, clarified, declared out of scope, or escalated.
7. The decision, sources, confidence, and reasoning are stored in the audit log.

## Situation 1: The request is out of scope

Examples include general knowledge, weather, recipes, greetings, or meaningless
text with no connection to wealth-management suitability or compliance.

Workflow:

1. The query-rewriting LLM sets `needs_retrieval` to `false`.
2. No wiki or expert knowledge is searched.
3. The API returns `out_of_scope` with a short explanation of the Copilot's scope.
4. The result is written to the audit log.

## Situation 2: The question is a contextual follow-up

Example:

> User: Can someone from Finland buy structured products?
>
> User: What about Ghana?

Workflow:

1. Recent user and assistant messages are sent with the new question.
2. The query-rewriting LLM converts the follow-up into a self-contained question,
   such as “Can someone from Ghana buy structured products?”
3. Retrieval, answer validation, and escalation use the self-contained version.
4. If escalation is required, the expert receives the self-contained question—not
   only “What about Ghana?”
5. Booking centre, client category, and service model are appended to the expert
   case when available.
6. If query rewriting is unavailable, the expert case includes up to three recent
   user messages followed by the latest question.

## Situation 3: Approved expert knowledge appears relevant

Approved knowledge is an answer previously supplied by an expert and accepted for
reuse.

Workflow:

1. The backend performs a lexical search over approved knowledge.
2. A lexical match is treated only as a candidate, not as proof that the answer
   applies.
3. The grounded-answer LLM compares the complete current question with the
   original expert question and answer.
4. It must verify all distinguishing attributes, including country, jurisdiction,
   client type, product, and service model.
5. Knowledge about one country cannot answer a question about another country
   unless it explicitly states a broader rule covering both.

If the knowledge applies:

1. The LLM formulates a concise answer from the approved knowledge.
2. The answer cites the expert-approved knowledge item.
3. The response is returned as `answered`.

If the knowledge does not apply:

1. It is rejected for the current request.
2. The reason is added to the reasoning trail.
3. Processing continues with the real wiki documents.

## Situation 4: The real wiki contains a sufficient answer

Workflow:

1. TF-IDF retrieval selects up to three relevant files from `pages/*.html`.
2. Numeric filenames are treated as the real Confluence page IDs.
3. The grounded-answer LLM receives the self-contained question and retrieved page
   contents.
4. It checks that the sources directly answer the question and cover all material
   context.
5. It writes an answer using only facts stated in those sources.
6. It returns the IDs of the pages that directly support the answer.
7. The backend rejects unknown or invented source IDs.
8. The answer must meet the configured confidence threshold.
9. The API returns `answered` with citations to
   `http://localhost:8000/wiki/<page-id>`.

The LLM must preserve relevant conditions, exceptions, warnings, and jurisdictional
limits. Instructions embedded inside source documents are treated as untrusted
content and ignored.

## Situation 5: The question needs clarification

Some questions have multiple possible answers depending on missing information.
Examples include an unspecified workflow, system, solicitation type, or source of
an alert.

Workflow:

1. Retrieval finds the most relevant document.
2. The ambiguity rules detect that material context is missing.
3. The API returns `clarification_needed` instead of guessing.
4. A clarification question and optional quick replies are shown to the user.
5. The user's reply is submitted with the previous conversation as history.
6. Query rewriting converts the reply into a self-contained question, and the
   normal workflow starts again.

## Situation 6: The sources mention the topic but do not answer the question

Example: the documents describe structured-product types but do not state whether
a client in Ghana is eligible to purchase them.

Workflow:

1. Retrieval returns related documents.
2. The grounded-answer LLM determines that they are adjacent or insufficient.
3. No answer is generated from general knowledge or assumptions.
4. The request continues to the escalation workflow.
5. Retrieved documents may still be shown as material that was checked, but they
   are not represented as supporting an answer.

## Situation 7: No document matches

Workflow:

1. Retrieval produces no result above zero relevance.
2. The backend records a `wiki_gap:no_matching_guidance` scope flag.
3. The request goes directly to escalation.
4. No source is cited as supporting an answer.

## Situation 8: The LLM is unavailable or returns an invalid result

This includes a missing API key, provider timeout, malformed structured response,
empty answer, or a citation to a page the model was not given.

Workflow:

1. The grounded-answer step fails closed.
2. The Copilot does not fall back to extracting an arbitrary sentence.
3. The request is escalated rather than answered.
4. The failure reason is recorded in the reasoning trail.

## Situation 9: A jurisdiction mismatch is detected

Workflow:

1. The backend infers region scope from the retrieved document.
2. It compares a single-region source with jurisdictions mentioned in the question.
3. A mismatch produces the `source_does_not_cover_jurisdiction` flag and a scope
   warning.
4. The grounded-answer LLM must still determine whether another retrieved source
   provides sufficient applicable guidance.
5. If applicable evidence is absent, the request is escalated.

## Situation 10: Escalation is required

Escalation occurs when there is no matching source, insufficient evidence, rejected
expert knowledge, low grounded-answer confidence, or an LLM failure.

Workflow:

1. Topic tags from the best retrieved document are used to select an expert.
2. If there is no usable topic match, the request starts with a Suitability
   Champion.
3. The response explains why the Copilot could not answer and identifies the
   selected expert, team, escalation tier, and fallback contact.
4. A persistent escalation case is created.
5. The case contains the self-contained rewritten question and available client
   context.
6. The expert sees the complete question in the escalation inbox and can reply.
7. The expert's response is returned to the requesting RM and logged as the case
   resolution.

Escalation tiers:

1. Suitability Champion
2. Business Front Support
3. BRM Suitability Lead
4. Suitability Expert

## Situation 11: An expert answers an escalation

Workflow:

1. The expert posts a response to the escalation case.
2. The case is marked as answered.
3. The resolution is written to the audit log.
4. A draft reusable knowledge item is created from the complete escalated question
   and expert answer.
5. The requesting RM receives the expert response through the case synchronization
   flow.

## Situation 12: Expert knowledge is accepted or rejected

Workflow:

1. An expert answer creates a pending knowledge candidate.
2. A reviewer accepts or rejects it.
3. Rejected knowledge is not searchable.
4. Accepted knowledge becomes searchable as approved expert knowledge.
5. Future lexical matches must still pass grounded LLM validation before use.
6. Approval therefore permits consideration; it does not bypass question-specific
   validation.

## Configuration and safety defaults

Required for LLM-backed rewriting and answering:

```bash
export OPENAI_API_KEY="..."
```

Optional model configuration:

```bash
export QUERY_REWRITE_MODEL="gpt-4.1-mini"
export ANSWER_MODEL="gpt-4.1-mini"
```

`ANSWER_MODEL` defaults to `QUERY_REWRITE_MODEL`. The grounded answer confidence
threshold is configured in `Backend/main.py`. After changing configuration or
backend code, restart the FastAPI server.
