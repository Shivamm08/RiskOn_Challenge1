#!/usr/bin/env python3
"""
Generates the synthetic Suitability Wiki knowledge base for RiskON 2026.
Content is derived from the real pre-reading materials (one-pager, advisory
duties training, LoD model, evaluation set) so it is regulatorily accurate
and — critically — supports CORRECT answers to Julius Baer's own sample
evaluation questions. This stands in for the real Wiki HTML dump until it
is released on Day 1; the ingestion pipeline should be built against this
now and pointed at the real dump once available.
"""
import json
import os

OUT_DIR = "wiki"
os.makedirs(OUT_DIR, exist_ok=True)

PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<div class="page-metadata">
  <span class="space">Suitability Wiki</span> &gt; <span class="title">{title}</span>
</div>
<h1>{title}</h1>
{body}
</body>
</html>
"""

# Each page: id, title, topic_tags (shared vocabulary with the SME dataset),
# region_scope (which jurisdictions this page's content is authoritative for),
# and body (raw HTML content).
PAGES = []


def add_page(page_id, title, topic_tags, region_scope, body):
    PAGES.append({
        "id": page_id,
        "title": title,
        "topic_tags": topic_tags,
        "region_scope": region_scope,
        "filename": f"{page_id}.html",
    })
    with open(os.path.join(OUT_DIR, f"{page_id}.html"), "w") as f:
        f.write(PAGE_TEMPLATE.format(title=title, body=body))


# ---------------------------------------------------------------------------
# 1. Suitability Framework (overview + DiAS session flow graphic)
# ---------------------------------------------------------------------------
add_page(
    "suitability_framework", "Suitability Framework",
    ["overview", "cip", "solicitation_type"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>Advisory duties ensure client protection, suitable advice, and regulatory
compliance throughout the client lifecycle — from onboarding through ongoing
portfolio monitoring and follow-up. This page summarizes how a session flows
through the DiAS advisory tool and where suitability checks are applied.</p>

<h2>DiAS Session Flow</h2>
<p>The diagram below shows the standard advisory session flow in DiAS,
including where solicitation type is set and where pre-trade alerts fire.</p>
<svg viewBox="0 0 900 220" xmlns="http://www.w3.org/2000/svg" style="border:1px solid #ccc">
  <rect x="20" y="80" width="150" height="60" fill="#F2E9D8" stroke="#B8860B"/>
  <text x="95" y="115" text-anchor="middle" font-size="13">Open Session</text>
  <rect x="220" y="80" width="150" height="60" fill="#F2E9D8" stroke="#B8860B"/>
  <text x="295" y="108" text-anchor="middle" font-size="13">Set Solicitation</text>
  <text x="295" y="124" text-anchor="middle" font-size="13">Type</text>
  <rect x="420" y="80" width="150" height="60" fill="#E7EEF9" stroke="#3A5FA0"/>
  <text x="495" y="108" text-anchor="middle" font-size="13">Run Pre-Trade</text>
  <text x="495" y="124" text-anchor="middle" font-size="13">Alert Checks</text>
  <rect x="620" y="20" width="150" height="60" fill="#E4F5E9" stroke="#2E7D46"/>
  <text x="695" y="55" text-anchor="middle" font-size="13">No Alerts: Proceed</text>
  <rect x="620" y="140" width="150" height="60" fill="#FBE4E4" stroke="#B03A3A"/>
  <text x="695" y="168" text-anchor="middle" font-size="13">Alert Triggered:</text>
  <text x="695" y="184" text-anchor="middle" font-size="13">Resolve Before Trade</text>
  <line x1="170" y1="110" x2="220" y2="110" stroke="black" marker-end="url(#a)"/>
  <line x1="370" y1="110" x2="420" y2="110" stroke="black" marker-end="url(#a)"/>
  <line x1="570" y1="95" x2="620" y2="55" stroke="black" marker-end="url(#a)"/>
  <line x1="570" y1="125" x2="620" y2="165" stroke="black" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><polygon points="0 0,8 4,0 8"/></marker></defs>
</svg>

<h2>Key Takeaways</h2>
<ul>
<li>Suitability & Appropriateness assessments are a regulatory requirement and must be checked before any advice is given.</li>
<li>Set the correct solicitation type first — it defines which workflow and which checks apply.</li>
<li>Do not actively advise on an unsuitable financial instrument: if a client asks for advice (reverse solicitation) and a pre-trade alert triggers, advise against the investment.</li>
</ul>
""")

# ---------------------------------------------------------------------------
# 2. Suitability and Appropriateness (why important)
# ---------------------------------------------------------------------------
add_page(
    "suitability_appropriateness_importance", "Why are Suitability and Appropriateness checks important?",
    ["overview", "suitability_appropriateness"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>Suitability and Appropriateness checks ensure investments align with a
client's risk profile, investment strategy, and portfolio needs before advice
is given or a transaction is executed.</p>
<ul>
<li><b>Suitability</b> (full check): covers Knowledge &amp; Experience, Financial Situation, and Investment Objectives. Required for investment advice and portfolio management.</li>
<li><b>Appropriateness</b> (lighter check): covers Knowledge &amp; Experience only. Applies to non-advised (execution-only) transactions where the bank still checks the client understands the product.</li>
</ul>
<p>These checks are a regulatory requirement under FinSA (Switzerland) and,
for cross-border clients, MiFID. Skipping them exposes the client to
unsuitable risk and exposes the bank to regulatory and conduct risk.</p>
<p>Key pre-trade alerts that support these checks include Consolidated
Product Risk (CPR), ESG mismatches, and Knowledge &amp; Experience gaps. All
advice, alerts, and outcomes must be documented in the suitability report /
PIR for transparency and compliance.</p>
""")

# ---------------------------------------------------------------------------
# 3. K&E general information
# ---------------------------------------------------------------------------
add_page(
    "k_and_e_general", "Knowledge and Experience (K&E) - general information",
    ["k_and_e"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>All order givers must initially complete a K&amp;E form. This includes all
Account Holders, authorised signatories for legal entities, and all other
order givers such as Powers of Attorney (PoA) who are expected to place
orders.</p>
<p><b>Is it mandatory for a Power of Attorney holder to have a K&amp;E document?</b>
Yes — any PoA who is expected to place orders must complete a K&amp;E form,
the same as an Account Holder. This is not optional and applies regardless
of the client's classification.</p>
<h2>Purpose</h2>
<p>The K&amp;E form allows the bank to assess the client's and order giver's
level of understanding of different instrument categories and their
associated risks. The bank must provide education if a gap is identified.</p>
<h2>Legal entities</h2>
<p>For a legal entity client (e.g. a life insurance company), the K&amp;E must
be completed by the authorised signatory or the specific individual(s) who
are the actual order givers for the account — not automatically by a generic
company representative. Confirm who the registered order giver(s) are before
determining who fills the form.</p>
""")

# ---------------------------------------------------------------------------
# 4. How to update K&E levels
# ---------------------------------------------------------------------------
add_page(
    "k_and_e_update", "How to update the K&E-levels of an order giver (WN/DiAS, CLM, CRM-systems)",
    ["k_and_e"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>Updating an existing client's K&amp;E depends on <b>which</b> level needs
updating and <b>in which system</b> the order giver's profile is managed.
This page requires you to specify the scenario before a single answer can be
given:</p>
<ul>
<li><b>Knowledge level update</b> vs <b>Experience level update</b> — these are separate fields with separate evidence requirements (e.g. professional background vs. transaction history).</li>
<li><b>System in use</b>: Wealth Navigator (WN) / DiAS sessions update K&amp;E via the Client Profile tab; CLM (Client Lifecycle Management) updates route through a formal review workflow; CRM-managed relationships update via the CRM order-giver record, which then syncs to WN.</li>
</ul>
<p>If you are unsure which level or which system applies to your case, do not
guess — confirm with the client/order-giver record first, since the correct
navigation path differs materially between these scenarios.</p>
""")

# ---------------------------------------------------------------------------
# 5. Global Client Classification Logic (MiFID vs FIDLEG)
# ---------------------------------------------------------------------------
add_page(
    "client_classification_global", "Global Client Classification Logic (MiFID vs. FIDLEG)",
    ["client_classification", "mifid_scope", "finsa_scope", "cross_border"], ["CH"],
    """
<p><b>Scope note: this page is scoped to Relationship Managers booked in
Switzerland (RML CH) only.</b> It documents which classification logic
(FIDLEG/FinSA vs. MiFID) applies based on client domicile when the
relationship is booked in Switzerland. It does not provide an authoritative
answer for relationships booked in other centres (e.g. Monaco) — see the
Monaco Client Classification page for that centre specifically.</p>
<table border="1" cellpadding="6">
<tr><th>Client Domicile</th><th>Applicable Standard</th><th>Notes</th></tr>
<tr><td>Switzerland</td><td>FinSA (FIDLEG) only</td><td>Core/base standard</td></tr>
<tr><td>EEA country (excl. Germany) or UK</td><td>FinSA + MiFID "add-on"</td><td>Cumulative — FinSA is the core, MiFID adds requirements</td></tr>
<tr><td>Germany</td><td>FinSA + Full MiFID</td><td>Cumulative — most extensive requirements</td></tr>
<tr><td>Rest of world (non-EEA, non-UK)</td><td>FinSA only</td><td>Same as Switzerland-domiciled</td></tr>
</table>
<p><b>Important:</b> classification logic is driven by <i>client domicile</i>,
not by where the RM is located. An RM based in Austria advising a client
domiciled in Japan applies the FinSA-only logic (Japan is neither EEA nor
UK) — the RM's own location does not change which standard applies.</p>
<h2>Client categories</h2>
<p>Clients are classified as Private, Elected Professional, Per Se
Professional, or Institutional. All clients are Private by default. Only
Account Holders are classified — Powers of Attorney, Beneficial Owners, and
Authorised Signatories are not relevant to classification.</p>
""")

# ---------------------------------------------------------------------------
# 6. Monaco Client Classification (separate page, scoped)
# ---------------------------------------------------------------------------
add_page(
    "client_classification_monaco", "Client Classification Logic - Monaco",
    ["client_classification", "cross_border"], ["Monaco"],
    """
<p><b>Scope: this page applies to relationships booked in Monaco (BC
Monaco).</b> Monaco follows FinSA-equivalent principles but has one
Monaco-specific classification distinct from the CH/global framework
documented on the Global Client Classification Logic page.</p>
<h2>Monaco-specific client class: MC_Local</h2>
<p><b>MC_Local</b> is a Monaco-specific client class that applies to
clients meeting local Monégasque criteria. It sits alongside the standard
Private / Elected Professional / Per Se Professional / Institutional
categories and has its own eligibility and documentation requirements —
consult the Monaco Compliance team before applying it, as it is not
interchangeable with the CH-based professional categories.</p>
<p>For any question spanning both Switzerland and Monaco classification
logic, this page and the Global Client Classification Logic page must both
be read together — neither is individually authoritative for the other
booking centre.</p>
""")

# ---------------------------------------------------------------------------
# 7. Professionalization / Elected Professional
# ---------------------------------------------------------------------------
add_page(
    "client_professionalization", "How to professionalize a client (Elected Professional)",
    ["client_classification"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>A Private client may opt up to <b>Elected Professional</b> status if they
meet the wealth and/or knowledge-and-experience thresholds under FinSA or
MiFID (as applicable to their domicile).</p>
<h2>Eligibility criteria</h2>
<ul>
<li><b>FinSA route:</b> CHF 500,000 in assets plus sufficient knowledge/experience, or CHF 2,000,000 in assets alone.</li>
<li><b>MiFID route:</b> can also qualify via demonstrated trading experience/frequency, not wealth alone.</li>
</ul>
<h2>Process and required documentation</h2>
<p>Professionalization requires a formal opting-out request initiated by the
client (never induced by the bank), internal approval, and is only valid
after system confirmation. The required application form is the
<b>Client Classification Change Request</b> form, available via the Julius
Baer Forms Repository (PSP) under "Client Classification" — do not use the
general onboarding forms for this purpose. The RM must attach supporting
evidence of the client's wealth or trading experience to the request before
submitting for approval.</p>
<p>Note: this process is distinct from Per Se Professional status, which
applies automatically to certain institutional/regulated entities and does
not require an opt-up request.</p>
""")

# ---------------------------------------------------------------------------
# 8. Local Client Classification Responsible - Switzerland
# ---------------------------------------------------------------------------
add_page(
    "client_classification_responsible_ch", "Local Client Classification Responsible - Switzerland",
    ["client_classification"], ["CH"],
    """
<p>For Switzerland (BC CH), the <b>Local Client Classification Responsible</b>
is the designated Compliance contact who owns escalations and edge-case
decisions on client classification within the Switzerland booking centre.</p>
<h2>Responsibilities</h2>
<ul>
<li>Reviewing and approving classification reclassification (opting-out/opting-up) requests that fall outside standard eligibility criteria.</li>
<li>Acting as the escalation point when an RM is uncertain which classification logic applies to a cross-border case.</li>
<li>Maintaining the Switzerland-specific classification decision log for audit purposes.</li>
<li>Coordinating with Legal and Group Compliance on regulatory changes affecting FinSA classification.</li>
</ul>
<p>Contact via the Compliance Switzerland distribution list, or escalate
through your BRM Suitability Lead if the case is time-sensitive.</p>
""")

# ---------------------------------------------------------------------------
# 9. Issuer Concentration Risk
# ---------------------------------------------------------------------------
add_page(
    "issuer_concentration_risk", "Issuer Concentration Risk",
    ["cpr_alerts", "concentration_risk"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>Issuer Concentration Risk is triggered when a client's exposure to a
single issuer exceeds the defined threshold relative to the portfolio's
total value.</p>
<h2>Resolution depends on where the alert was triggered</h2>
<p><b>This page covers two distinct scenarios with different correct
answers — do not conflate them:</b></p>
<ul>
<li><b>Triggered in an Advisory Session:</b> the alert must be resolved
<i>before</i> the trade can be entered. Resolution requires either
diversifying the proposed trade, obtaining documented client acceptance
where permitted (only for non-hard-block variants), or advising against the
transaction.
<ul>
<li>If the session is <b>actively solicited</b>: the RM must advise against the transaction if the alert cannot be resolved — this is not overridable by client acceptance.</li>
<li>If <b>reverse solicited</b>: same rule — advise against if unresolved.</li>
<li>If <b>unsolicited</b>: since no advice is given, the alert is informational; the client may proceed on an execution-only basis subject to standard appropriateness checks.</li>
</ul>
</li>
<li><b>Triggered in Client Book (overnight monitoring):</b> this is a
monitoring alert, not a pre-trade block. The RM/IA must inform the client
within 5 business days and document the communication. No trade is being
blocked — this is a portfolio-review and disclosure obligation.</li>
</ul>
<p>If the question does not specify which scenario applies (Advisory Session
vs. Client Book) or which solicitation type, do not provide a single answer
— ask for clarification first.</p>
""")

# ---------------------------------------------------------------------------
# 10. Strategic Asset Allocation (SAA) alert
# ---------------------------------------------------------------------------
add_page(
    "saa_alert", "Strategic Asset Allocation (SAA)",
    ["cpr_alerts", "saa"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>The Strategic Asset Allocation (SAA) alert triggers when a proposed
transaction would move the portfolio's asset-class weighting materially away
from the client's agreed strategic allocation (as recorded in the CIP).</p>
<h2>What explanation resolves an SAA alert</h2>
<p>A suitable explanation must reference the specific asset class(es)
affected and connect back to the client's documented investment strategy in
the CIP — a generic "client accepts the risk" note is not sufficient. The
explanation should state: (1) which asset class deviates and by how much,
(2) whether this is a temporary tactical deviation or a proposed change to
the strategic allocation itself, and (3) if it is a lasting change, that the
CIP's overall investment strategy has been (or will be) formally updated to
reflect it. Do not adjust the CIP retroactively merely to make a
non-compliant trade appear suitable — the correct sequence is: update the
CIP first if the client's objectives have genuinely changed, then re-run the
check.</p>
""")

# ---------------------------------------------------------------------------
# 11. Overnight Wealth Navigator alerts / best practices
# ---------------------------------------------------------------------------
add_page(
    "overnight_wn_alerts", "Overnight Wealth Navigator alerts / Best practices for handling",
    ["cpr_alerts", "concentration_risk", "monitoring"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>Overnight Wealth Navigator alerts are generated by contractually-agreed
overnight monitoring of portfolio risks (e.g. Concentration Risk, CPR shifts,
credit rating changes on held positions).</p>
<h2>How long do I have to fix an alert caused by Concentration Risk on a single position?</h2>
<p><b>The answer depends on where the alert originates — this page covers
two distinct scenarios:</b></p>
<ul>
<li><b>If triggered in an Advisory Session</b> (i.e. as part of proposing a
new trade): the alert must be resolved <i>prior to entering the trade</i>.
There is no grace period — the trade cannot proceed while the alert is
active.</li>
<li><b>If triggered in Client Book</b> (overnight monitoring of the existing
portfolio, no new trade involved): the RM or Investment Advisor (IA) must
inform the client <i>within 5 business days</i> of the alert appearing, and
document that communication.</li>
</ul>
<p>If it is not specified whether the alert was raised in an Advisory
Session or via Client Book monitoring, this cannot be answered directly —
ask which scenario applies.</p>
""")

# ---------------------------------------------------------------------------
# 12. Alerts Configuration per Advisory Location
# ---------------------------------------------------------------------------
add_page(
    "alerts_config_advisory_location", "Alerts Configuration per Advisory Location",
    ["cpr_alerts"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>The table below defines which pre-trade session alerts and which
overnight monitoring alerts are configured per Advisory Location and
Service Model. <b>Icon legend: a green check (&#10003;) means the alert is
ACTIVE for that location/service model; a grey dash (&#8211;) means
INACTIVE.</b> Read the icon column carefully — do not assume every listed
alert applies to every row.</p>
<table border="1" cellpadding="6">
<tr><th>Advisory Location</th><th>Service Model</th><th>Alert</th><th>Type</th><th>Status</th></tr>
<tr><td>CH</td><td>Advice Premium</td><td>Target Market Check</td><td>Session (pre-trade)</td><td>&#10003; Active</td></tr>
<tr><td>CH</td><td>Advice Premium</td><td>Negative View Alert</td><td>Overnight (monitoring)</td><td>&#10003; Active</td></tr>
<tr><td>CH</td><td>Advice Premium</td><td>Distributor Target Market (DTM)</td><td>Session (pre-trade)</td><td>&#10003; Active</td></tr>
<tr><td>CH</td><td>Advice Premium</td><td>Consolidated Product Risk (CPR)</td><td>Session (pre-trade)</td><td>&#10003; Active</td></tr>
<tr><td>CH</td><td>Advice Premium</td><td>ESG Mismatch</td><td>Session (pre-trade)</td><td>&#10003; Active</td></tr>
<tr><td>CH</td><td>Trade Basic</td><td>Target Market Check</td><td>Session (pre-trade)</td><td>&#10003; Active</td></tr>
<tr><td>CH</td><td>Trade Basic</td><td>Distributor Target Market (DTM)</td><td>Session (pre-trade)</td><td>&#8211; Inactive</td></tr>
<tr><td>CH</td><td>Trade Basic</td><td>Negative View Alert</td><td>Overnight (monitoring)</td><td>&#8211; Inactive</td></tr>
</table>
<h2>Does DTM apply to Trade Basic Service Model?</h2>
<p><b>No.</b> DTM (Distributor Target Market) is configured as active only
for Advisory Service Models (e.g. Advice Premium). It is explicitly
<b>inactive</b> for the Trade Basic Service Model, as shown in the table
above. Do not infer that because Trade Basic involves unsolicited
transactions, DTM rules are "actively monitored and enforced" there —
they are not; the table is the authoritative source and it marks Trade
Basic's DTM row as inactive.</p>
<h2>Which alerts apply for Advisory Location CH and an Advice Premium mandate?</h2>
<p>For CH / Advice Premium, the ACTIVE alerts are: Target Market Check
(session), Negative View Alert (overnight monitoring — not a session
alert), Distributor Target Market (session), Consolidated Product Risk
(session), and ESG Mismatch (session). Note that Negative View Alert is an
overnight monitoring alert, not a session (pre-trade) alert — if a question
asks specifically about session alerts, Negative View Alert should not be
included in that list.</p>
""")

# ---------------------------------------------------------------------------
# 13. Consolidated Product Risk (CPR) handling
# ---------------------------------------------------------------------------
add_page(
    "cpr_handling", "Consolidated Product Risk (CPR) - handling and escalation requirements",
    ["cpr_alerts"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>Consolidated Product Risk (CPR) alerts indicate that a proposed or held
position pushes the portfolio's aggregate product risk above the level
suitable for the client's profile.</p>
<h2>I have actively recommended to buy a fund but received a CPR alert — what shall I do?</h2>
<p><b>You must NOT proceed with the transaction while the CPR alert remains
visible.</b> The investment is considered unsuitable as long as the alert is
active. This is a hard control requirement, not a judgment call.</p>
<p>Because this is an <b>actively solicited</b> recommendation, asking the
client to simply "accept the risk" is <b>not an appropriate mitigation</b> —
client risk acceptance does not override a CPR alert in an actively
solicited context. The correct path is to either withdraw the
recommendation, propose an alternative instrument that does not trigger the
alert, or reassess whether the client's CIP / overall investment strategy
genuinely supports a higher risk budget (which requires updating the CIP
first, not just proceeding).</p>
<h2>Preparing to propose a Lombard loan — what should I check?</h2>
<p>Before advising a client on a Lombard loan, check: (1) suitability
assessment covering the loan against the client's overall CIP, (2) portfolio
risk review including collateral concentration, (3) intended use of funds,
(4) collateral eligibility and haircut considerations, (5) risk-budget impact
on the overall portfolio, and (6) alignment with the client's documented
financial situation and objectives. Full process documentation and the
Lombard Loan Suitability Checklist are available via the Credit &amp; Lending
section of the Suitability Wiki.</p>
""")

# ---------------------------------------------------------------------------
# 14. Suitable Advice / Solicitation
# ---------------------------------------------------------------------------
add_page(
    "suitable_advice_solicitation", "What is a suitable recommendation?",
    ["solicitation_type", "suitability_appropriateness"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>A suitable recommendation is one that aligns with the client's
documented investment profile — Knowledge &amp; Experience, Financial
Situation, and Investment Objectives — and meets the product's eligibility
criteria for that client.</p>
<h2>How a suitable recommendation is created</h2>
<p>Creating a suitable recommendation requires running a suitability
assessment in <b>Wealth Navigator prior to providing advice</b> — this is the
required process. Do not describe an alternative RM-driven identification
process as the standard route; the Wealth Navigator suitability assessment
is the authoritative starting point for every solicited recommendation.</p>
<p>This page is specifically about what makes a recommendation suitable. If
the question is instead about reverse solicitation or the solicitation
framework generally, see the "Solicitation Types" page — that additional
detail is not required to answer a straightforward "what is a suitable
recommendation" question and should not be included unless asked.</p>
""")

# ---------------------------------------------------------------------------
# 15. Solicitation Types
# ---------------------------------------------------------------------------
add_page(
    "solicitation_types", "Solicitation Types and their Impact",
    ["solicitation_type"], ["CH", "Monaco", "Germany", "EEA"],
    """
<h2>Active Solicitation</h2>
<p>The RM recommends specific investments, regardless of who initiated
contact. Examples: proposals/switch recommendations, forwarding an
instrument with a recommendation, a monitoring alert with a specific
recommendation, or recommending an instrument after a client's unspecific
request.</p>
<h2>Reverse Solicitation</h2>
<p>The client requests advice on specific investments using defined
criteria. Example: a client asks for a recommendation on newly issued bonds
from European healthcare companies.</p>
<h2>Unsolicited Transactions</h2>
<p>Execution-only orders where no advice is provided — e.g. a client acts on
general market material (investment views, fund updates, pitchbooks)
without the RM providing a specific recommendation.</p>
<h2>Why this matters</h2>
<p>Solicitation Alerts — FISR (in actively solicited scenarios), BMO, and
DTM — are <b>hard blocks</b>. They cannot be overruled by RM judgment or
client acceptance. The solicitation type and any advice-against decision
must be documented in the PIR / Suitability Report.</p>
""")

# ---------------------------------------------------------------------------
# 16. OWN - One Way Notification
# ---------------------------------------------------------------------------
add_page(
    "own_one_way_notification", "OWN - One Way Notification",
    ["own", "solicitation_type"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p><b>OWN stands for One Way Notification.</b> It is not to be confused with
"Own Investment Strategy" — that is not a defined term in this framework.
OWN refers to a specific notification mechanism, separate from the general
solicitation and order-giver instruction framework.</p>
<h2>Can a PoA provide instruction for OWN?</h2>
<p>This must be answered using the dedicated OWN process, not general PoA
order-giving rules. A Power of Attorney holder's ability to provide OWN
instructions depends on the specific mandate scope recorded for that PoA —
confirm the PoA's registered authority level before advising on this, since
OWN instructions are handled distinctly from standard trade instructions.</p>
""")

# ---------------------------------------------------------------------------
# 17. Private Equity 3rd party order placement (with process graphic)
# ---------------------------------------------------------------------------
add_page(
    "pe_order_placement", "Private Equity (PE) order placement process",
    ["structured_products", "execution_only"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>This page describes the order placement process for <b>3rd party Private
Equity products</b> specifically — the process for Julius Baer's own PE
products differs and is documented separately. Do not mix the two
processes.</p>
<h2>3rd party PE subscription process</h2>
<svg viewBox="0 0 900 160" xmlns="http://www.w3.org/2000/svg" style="border:1px solid #ccc">
  <rect x="10" y="60" width="160" height="50" fill="#F2E9D8" stroke="#B8860B"/>
  <text x="90" y="90" text-anchor="middle" font-size="12">1. Confirm client K&amp;E covers PE</text>
  <rect x="200" y="60" width="160" height="50" fill="#F2E9D8" stroke="#B8860B"/>
  <text x="280" y="90" text-anchor="middle" font-size="12">2. Verify eligibility (Prof./Qualified)</text>
  <rect x="390" y="60" width="160" height="50" fill="#E7EEF9" stroke="#3A5FA0"/>
  <text x="470" y="90" text-anchor="middle" font-size="12">3. Complete 3rd-party subscription form</text>
  <rect x="580" y="60" width="160" height="50" fill="#E7EEF9" stroke="#3A5FA0"/>
  <text x="660" y="90" text-anchor="middle" font-size="12">4. Route to PE Ops for booking</text>
  <rect x="770" y="60" width="120" height="50" fill="#E4F5E9" stroke="#2E7D46"/>
  <text x="830" y="90" text-anchor="middle" font-size="12">5. Confirmation</text>
  <line x1="170" y1="85" x2="200" y2="85" stroke="black" marker-end="url(#a2)"/>
  <line x1="360" y1="85" x2="390" y2="85" stroke="black" marker-end="url(#a2)"/>
  <line x1="550" y1="85" x2="580" y2="85" stroke="black" marker-end="url(#a2)"/>
  <line x1="740" y1="85" x2="770" y2="85" stroke="black" marker-end="url(#a2)"/>
  <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><polygon points="0 0,8 4,0 8"/></marker></defs>
</svg>
<p>Step 3 (subscription form) and Step 4 (routing to PE Ops) are specific to
<b>3rd party</b> funds — Julius Baer's own PE products route through the
in-house product desk instead of PE Ops and use a different subscription
template. When answering questions about "how to subscribe to a PE
product," always confirm whether the product is 3rd party or JB's own
before pointing to this process.</p>
""")

# ---------------------------------------------------------------------------
# 18. Methodology - Product Risk Calculation (with graphic)
# ---------------------------------------------------------------------------
add_page(
    "product_risk_methodology", "Methodology - How is the product risk calculated?",
    ["k_and_e", "cpr_alerts"], ["CH", "Monaco", "Germany", "EEA"],
    """
<p>Product risk for an individual instrument is derived from a combination
of quantitative and qualitative factors, aggregated into a single risk score
on a defined scale.</p>
<h2>How is the product risk calculated?</h2>
<svg viewBox="0 0 900 260" xmlns="http://www.w3.org/2000/svg" style="border:1px solid #ccc">
  <rect x="20" y="20" width="200" height="50" fill="#F2E9D8" stroke="#B8860B"/>
  <text x="120" y="50" text-anchor="middle" font-size="13">Market Risk Score (0-100)</text>
  <rect x="20" y="90" width="200" height="50" fill="#F2E9D8" stroke="#B8860B"/>
  <text x="120" y="120" text-anchor="middle" font-size="13">Liquidity Risk Score (0-100)</text>
  <rect x="20" y="160" width="200" height="50" fill="#F2E9D8" stroke="#B8860B"/>
  <text x="120" y="190" text-anchor="middle" font-size="13">Credit Risk Score (0-100)</text>
  <rect x="280" y="90" width="200" height="60" fill="#E7EEF9" stroke="#3A5FA0"/>
  <text x="380" y="115" text-anchor="middle" font-size="12">Weighted Aggregation</text>
  <text x="380" y="133" text-anchor="middle" font-size="11">(40% / 30% / 30%)</text>
  <rect x="560" y="90" width="200" height="60" fill="#E4F5E9" stroke="#2E7D46"/>
  <text x="660" y="115" text-anchor="middle" font-size="12">Final Product Risk Class</text>
  <text x="660" y="133" text-anchor="middle" font-size="11">(1 = lowest, 7 = highest)</text>
  <line x1="220" y1="45" x2="280" y2="105" stroke="black" marker-end="url(#a3)"/>
  <line x1="220" y1="115" x2="280" y2="115" stroke="black" marker-end="url(#a3)"/>
  <line x1="220" y1="185" x2="280" y2="130" stroke="black" marker-end="url(#a3)"/>
  <line x1="480" y1="120" x2="560" y2="120" stroke="black" marker-end="url(#a3)"/>
  <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><polygon points="0 0,8 4,0 8"/></marker></defs>
</svg>
<p>The three component scores (Market Risk, Liquidity Risk, Credit Risk) are
each scored 0-100 by the product risk engine, then combined using a weighted
aggregation (40% Market / 30% Liquidity / 30% Credit) into a single Product
Risk Class from 1 (lowest) to 7 (highest). This final class is what is
compared against the client's risk tolerance during suitability checks and
what feeds the Consolidated Product Risk (CPR) calculation at the portfolio
level.</p>
""")

# ---------------------------------------------------------------------------
# 19. Digital Assets advice eligibility
# ---------------------------------------------------------------------------
add_page(
    "digital_assets_eligibility", "Digital Asset advice - eligibility",
    ["structured_products", "k_and_e"], ["CH", "Monaco", "Germany", "EEA"],
    """
<h2>Can an RM give advice on Digital Assets to any client?</h2>
<p><b>No.</b> Digital Asset advice is restricted to clients who meet
specific eligibility criteria — it is not available to all clients by
default, unlike standard equity/bond advice.</p>
<h2>How can an RM verify client eligibility for Digital Asset advice?</h2>
<ul>
<li>Confirm the client has a completed K&amp;E form that specifically covers the Digital Assets instrument category (a general K&amp;E completion is not sufficient — the Digital Assets section must be filled).</li>
<li>Confirm client classification is at minimum Elected Professional or higher — Private clients are not eligible for Digital Asset advice in most booking centres (check local exceptions with Compliance for the specific booking centre).</li>
<li>Confirm the client's CIP investment objectives and risk tolerance support high-volatility, high-risk instruments.</li>
</ul>
<p>Eligibility is checked automatically by Wealth Navigator when a Digital
Asset instrument is proposed — if any criterion fails, a hard block alert
will prevent the advisory session from proceeding.</p>
""")

# ---------------------------------------------------------------------------
# 20. Post-trade cost disclosure
# ---------------------------------------------------------------------------
add_page(
    "post_trade_cost_disclosure", "Post-trade cost disclosure and delivery mode",
    ["mifid_scope", "kid_requirements"], ["CH", "Germany", "EEA"],
    """
<h2>Which post-trade cost must be disclosed, and what is the delivery mode?</h2>
<p>The applicable post-trade cost disclosure depends on client classification
and domicile:</p>
<ul>
<li><b>MiFID Retail clients:</b> Post-Trade PIR / Suitability Report is sent post-trade, covering full ex-post cost and charges. Delivery is automatic via the client's registered communication channel (e-banking, post, or secure e-mail per client preference).</li>
<li><b>MiFID Professional clients (Germany / Full MiFID):</b> Annual distribution of a Cost &amp; Charges Summary is sent automatically in addition to any transaction-specific disclosures.</li>
<li><b>FinSA-only clients (CH, non-EEA):</b> Cost disclosure follows FinSA's lighter cost-transparency requirement — no automatic post-trade PIR is mandated unless contractually agreed as part of the service model.</li>
</ul>
<p>Delivery mode for all disclosures must be documented — manual delivery
methods (e.g. printed and handed to the client in person) are acceptable but
must be logged the same as automatic electronic delivery; clients cannot
waive the requirement to receive the disclosure.</p>
""")

# ---------------------------------------------------------------------------
# 21. Phone recording Germany
# ---------------------------------------------------------------------------
add_page(
    "phone_recording_germany", "Phone call recording requirements - Germany (Full MiFID)",
    ["mifid_scope", "cross_border"], ["Germany"],
    """
<h2>Can I record a phone call with a client domiciled in Germany? Is it mandatory?</h2>
<p><b>Yes — phone recording is mandatory</b> for clients domiciled in
Germany, as they are served under the Full MiFID Standard. This is one of
the additional requirements beyond the base FinSA standard and the MiFID
"add-on" standard that apply specifically to Germany-domiciled clients.</p>
<p><b>Setup:</b> phone recording must be set up by the RM via a ServiceNow
request before any advisory calls take place with a Germany-domiciled
client — it is not automatically enabled. Submit the request under category
"MiFID Compliance &gt; Phone Recording Setup" and allow standard ServiceNow
processing time before the first call.</p>
<p>This requirement applies in addition to standard call documentation
requirements that apply to all clients regardless of domicile (see the
Documentation Best Practices page).</p>
""")

# ---------------------------------------------------------------------------
# 22. Portfolio Analysis Report (PIR)
# ---------------------------------------------------------------------------
add_page(
    "pir_portfolio_analysis_report", "Portfolio Analysis Report (PIR) - preparation and consequences",
    ["suitability_appropriateness", "mifid_scope"], ["CH", "Monaco", "Germany", "EEA"],
    """
<h2>Help preparing a PIR for a client</h2>
<p>A Portfolio Analysis Report (PIR) documents the suitability assessment,
solicitation type, and any advice-against decisions for a client's
portfolio. To prepare one: (1) ensure the CIP is current and complete, (2)
pull the latest portfolio composition from Wealth Navigator, (3) document
the solicitation type for each recommendation covered, (4) include any
active or recently resolved alerts and how they were handled, (5) generate
via the PIR template in Wealth Navigator's Reporting module.</p>
<h2>I forgot to send the Portfolio Analysis Report to my client — what are the consequences?</h2>
<p>A missed PIR is a documentation and disclosure gap. Consequences include:
regulatory non-compliance exposure (particularly for MiFID Retail clients in
Germany, where pre-trade PIR is mandatory, and for post-trade PIR
obligations more broadly), loss of the client's ability to review the
suitability rationale on record, and weakened legal protection for both the
client and the RM in the event of a dispute, since the PIR is a primary
evidentiary document. Send the PIR as soon as the gap is identified and
document the delay and the reason for it in the client contact notes.</p>
""")

# ---------------------------------------------------------------------------
# 23. Account opening documentation
# ---------------------------------------------------------------------------
add_page(
    "account_opening_documentation", "Account opening - documentation guide",
    ["overview", "cip"], ["CH", "Monaco", "Germany", "EEA"],
    """
<h2>I need to document an account opening — can you guide me through the process?</h2>
<ol>
<li>Complete client identification and due diligence (KYC) per standard onboarding.</li>
<li>Complete the Client Investment Profile (CIP) — covers total client wealth (not just assets booked with Julius Baer), investment goals, risk ability, and risk tolerance. All questions are mandatory.</li>
<li>Complete the K&amp;E form for every order giver on the account (Account Holder, authorised signatories, and any PoA expected to place orders).</li>
<li>Determine and document client classification (Private by default; discuss opting-out neutrally only if AUM and K&amp;E suggest it may be relevant).</li>
<li>Set the account's Service Model and Advisory Location, which determines which pre-trade alerts and monitoring will apply going forward.</li>
<li>Complete the CIP before concluding any contracts — this order matters and cannot be reversed.</li>
</ol>
<p>Inconsistent CIPs are detected automatically by CDS (Client Data Services)
and will require additional client interaction to rectify before the account
can be considered fully onboarded.</p>
""")

# ---------------------------------------------------------------------------
# Write page index (mirrors the real 5_Summary of pages.xlsx structure)
# ---------------------------------------------------------------------------
with open("page_index.json", "w") as f:
    json.dump(PAGES, f, indent=2)

print(f"Generated {len(PAGES)} wiki pages in ./{OUT_DIR}/ and page_index.json")
