import streamlit as st
import pandas as pd
from agent import run_ux_research


# =========================================================
# LOCAL V4.3 DEMO ENGINE
# =========================================================
# This mode lets us continue building the dashboard without
# consuming Gemini API requests while the free-tier quota is
# exhausted. The logic mirrors the V3 structure: Python handles
# counting, percentages and priority calculations.

SAMPLE_REVIEWS = """User 1: I couldn't understand which grocery product was best for me.
User 2: The price shown on the product page was different from the final price.
User 3: I didn't know when my groceries would arrive.
User 4: There were too many products and no proper guidance to choose one.
User 5: Delivery charges appeared only at checkout.
User 6: I wanted to know the delivery time before placing the order.
User 7: Product search gave me too many irrelevant results.
User 8: The final amount was higher than I expected.
User 9: I couldn't easily compare similar products.
User 10: The estimated delivery time wasn't clearly visible."""


def parse_local_reviews(text):
    reviews = []
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        user, review = line.split(":", 1)
        reviews.append({"user": user.strip(), "review": review.strip()})
    return reviews


def classify_local_review(review):
    text = review.lower()
    problems = []

    if any(k in text for k in [
        "price", "pricing", "final amount", "higher than i expected",
        "delivery charges"
    ]):
        problems.append("Price Transparency")

    if any(k in text for k in [
        "arrive", "delivery time", "estimated delivery", "when my groceries"
    ]):
        problems.append("Delivery Information")

    if any(k in text for k in [
        "search", "irrelevant results"
    ]):
        problems.append("Search Functionality")

    if any(k in text for k in [
        "product", "best for me", "too many products",
        "guidance to choose", "compare similar"
    ]):
        problems.append("Product Selection")

    return problems or ["Other UX Issue"]


def priority_score(frequency_score, severity, business_impact):
    score = frequency_score + severity + business_impact
    if score >= 24:
        level = "CRITICAL"
    elif score >= 18:
        level = "HIGH"
    elif score >= 10:
        level = "MEDIUM"
    else:
        level = "LOW"
    return score, level


def run_local_demo(text):
    reviews = parse_local_reviews(text)
    total = len(reviews)
    classifications = []

    for item in reviews:
        for problem in classify_local_review(item["review"]):
            classifications.append({
                "user": item["user"],
                "review": item["review"],
                "problem": problem
            })

    grouped = {}
    for item in classifications:
        grouped.setdefault(item["problem"], []).append(item)

    # Evidence-based demo scores matching the V3 sample analysis.
    score_map = {
        "Price Transparency": (7, 9),
        "Product Selection": (7, 7),
        "Delivery Information": (6, 7),
        "Search Functionality": (5, 6),
        "Other UX Issue": (5, 5),
    }

    problems = []
    for name, items in grouped.items():
        affected = len({x["user"] for x in items})
        percentage = round((affected / total) * 100, 1) if total else 0
        frequency_score = round(percentage / 10)
        severity, impact = score_map.get(name, (5, 5))
        score, level = priority_score(frequency_score, severity, impact)

        problems.append({
            "name": name,
            "affected": affected,
            "percentage": percentage,
            "frequency_score": frequency_score,
            "severity": severity,
            "business_impact": impact,
            "score": score,
            "priority": level,
            "users": [x["user"] for x in items],
            "evidence": [x["review"] for x in items],
        })

    problems.sort(key=lambda x: (-x["score"], -x["affected"], x["name"]))

    critical = sum(1 for x in problems if x["priority"] == "CRITICAL")
    high = sum(1 for x in problems if x["priority"] == "HIGH")
    medium = sum(1 for x in problems if x["priority"] == "MEDIUM")
    low = sum(1 for x in problems if x["priority"] == "LOW")

    return {
        "total": total,
        "problems": problems,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "mode": "LOCAL V4.3 DEMO",
    }
def answer_research_question(question, data):
    """Answer UX research questions using the existing analysis data."""
    q = question.lower().strip()
    if not data or not data.get("problems"):
        return "I don't have enough research data to answer that question yet."

    problems = data["problems"]
    total = data["total"]
    matched_problem = None

    for problem in problems:
        if problem["name"].lower() in q:
            matched_problem = problem
            break

    # V4.1 — context-aware follow-up questions.
    follow_up_words = {"it", "this", "that"}
    question_words = set(q.replace("?", "").replace(".", "").split())
    if matched_problem is None and follow_up_words.intersection(question_words):
        previous_problem = st.session_state.get("last_research_problem")
        if previous_problem:
            for problem in problems:
                if problem["name"] == previous_problem:
                    matched_problem = problem
                    break

    if "total" in q and "user" in q:
        return f"There are {total} users in the research dataset."

    if matched_problem and (
    "how many" in q
    or (
        "affected" in q
        and "which users" not in q
    )
):
        st.session_state["last_research_problem"] = matched_problem["name"]
        return (
            f"{matched_problem['name']} affects {matched_problem['affected']} "
            f"out of {total} users ({matched_problem['percentage']}%)."
        )

    if matched_problem and ("why" in q or "priority" in q or "important" in q):
        st.session_state["last_research_problem"] = matched_problem["name"]
        return (
            f"{matched_problem['name']} is rated {matched_problem['priority']} priority "
            f"with a priority score of {matched_problem['score']}/30. "
            f"It affects {matched_problem['affected']} users "
            f"({matched_problem['percentage']}%). Its severity is "
            f"{matched_problem['severity']}/10 and its business impact is "
            f"{matched_problem['business_impact']}/10."
        )
        # V4.3 — Which users are affected?
    if matched_problem and (
        "which users" in q
        or "who" in q
        or "show users" in q
    ):
        st.session_state["last_research_problem"] = matched_problem["name"]

        users = ", ".join(matched_problem["users"])

        return (
            f"{matched_problem['name']} affects "
            f"{matched_problem['affected']} users: {users}."
        )

    # V4.3 — Show research evidence
    if matched_problem and (
        "evidence" in q
        or "quotes" in q
        or "feedback" in q
        or "what did they say" in q
    ):
        st.session_state["last_research_problem"] = matched_problem["name"]

        evidence_lines = []

        for user, evidence in zip(
            matched_problem["users"],
            matched_problem["evidence"]
        ):
            evidence_lines.append(
                f'{user}: "{evidence}"'
            )

        return (
            f"Evidence for {matched_problem['name']}:\n\n"
            + "\n\n".join(evidence_lines)
        )
        # V4.4 — Design Action Plan
    if matched_problem and (
        "change in the ui" in q
        or "change in ui" in q
        or "design action" in q
        or "design plan" in q
        or "ui changes" in q
        or "redesign" in q
        or "what should i change" in q
    ):
        st.session_state["last_research_problem"] = matched_problem["name"]

        design_actions = {
            "Price Transparency": [
                "Product Page: Show the complete product price clearly before users add the item to the cart.",
                "Cart: Display delivery charges and additional fees before checkout.",
                "Checkout: Show an itemized final-price breakdown.",
                "Consistency: Keep the displayed price consistent across product, cart, and payment screens.",
                "Validation: Test the redesigned pricing flow with users who experienced price confusion."
            ],

            "Delivery Information": [
                "Product Page: Show the estimated delivery time before users add the product to the cart.",
                "Cart: Keep the delivery estimate visible while users review their order.",
                "Checkout: Confirm the expected delivery time before payment.",
                "Status Visibility: Clearly communicate delivery timing and possible delays.",
                "Validation: Test whether users can find the delivery estimate before ordering."
            ],

            "Search Functionality": [
                "Search: Improve the relevance of search results.",
                "Filters: Add useful filters to help users narrow down products.",
                "Suggestions: Provide autocomplete and useful search suggestions.",
                "No Results: Suggest alternatives or corrected search terms.",
                "Validation: Test common grocery search tasks with users."
            ],

            "Product Selection": [
                "Product Cards: Highlight important information for quick decision-making.",
                "Comparison: Allow users to compare similar products.",
                "Guidance: Add clearer categories, labels, and product information.",
                "Recommendations: Help users choose when many similar options are available.",
                "Validation: Test whether users can confidently choose between similar products."
            ]
        }

        actions = design_actions.get(
            matched_problem["name"],
            [
                "Review the evidence behind the UX problem.",
                "Identify the main interface friction point.",
                "Create a redesigned solution.",
                "Prototype the improved experience.",
                "Validate the prototype with users."
            ]
        )

        action_list = "\n\n".join(
            f"{i}. {action}"
            for i, action in enumerate(actions, 1)
        )

        return (
            f"Design Action Plan for {matched_problem['name']}:\n\n"
            f"{action_list}"
        )

    # V4.2 — UX recommendations.
    if matched_problem and (
        "recommend" in q or "recommendation" in q or "solution" in q
        or "solve" in q or "improve" in q or "fix" in q
        or "what should we do" in q
    ):
        st.session_state["last_research_problem"] = matched_problem["name"]
        recommendations = {
            "Price Transparency": (
                "Show the complete price breakdown earlier in the journey, including "
                "delivery charges and other fees before checkout. Keep the displayed "
                "price consistent from product selection through payment."
            ),
            "Delivery Information": (
                "Show the estimated delivery time before the user places the order. "
                "Keep the ETA clearly visible on the product, cart, and checkout screens."
            ),
            "Search Functionality": (
                "Improve search relevance and filtering so users see results that better "
                "match what they are looking for."
            ),
            "Product Selection": (
                "Add clearer product guidance and comparison support so users can understand "
                "differences between similar products and choose confidently."
            ),
        }
        recommendation = recommendations.get(
            matched_problem["name"],
            "Review the evidence behind this problem, identify the main friction point, "
            "prototype an improved experience, and validate the solution with users before implementation."
        )
        return f"Recommendation for {matched_problem['name']}: {recommendation}"

    if "most" in q or "highest" in q or "biggest" in q or "fix first" in q:
        top = max(problems, key=lambda x: x["affected"])
        st.session_state["last_research_problem"] = top["name"]
        return (
            f"The most widely affected problem is {top['name']}, affecting "
            f"{top['affected']} out of {total} users ({top['percentage']}%)."
        )

    if "problems" in q or "issues" in q:
        problem_list = ", ".join(
            f"{p['name']} ({p['affected']} users, {p['percentage']}%)" for p in problems
        )
        return f"The identified UX problems are: {problem_list}."

    return (
        "I can answer questions about total users, affected users, UX problems, priority, "
        "severity, business impact, and UX recommendations."
    )


def build_local_report(data):
    lines = [
        "===== UX RESEARCH REPORT =====",
        "",
        "MODE: LOCAL V4.3 DEMO",
        f"TOTAL USERS: {data['total']}",
        "",
        "UX PROBLEMS (HIGHEST TO LOWEST PRIORITY):",
    ]

    for i, p in enumerate(data["problems"], 1):
        lines.extend([
            "",
            f"{i}. {p['name']}",
            f"Affected users: {p['affected']}",
            f"Percentage: {p['percentage']}%",
            f"Frequency Score: {p['frequency_score']}/10",
            f"Severity: {p['severity']}/10",
            f"Business Impact: {p['business_impact']}/10",
            f"Priority Score: {p['score']}/30",
            f"Priority: {p['priority']}",
            "Users: " + ", ".join(p["users"]),
            "Evidence:",
        ])
        for evidence in p["evidence"]:
            lines.append(f"- {evidence}")

    if data["problems"]:
        top = data["problems"][0]
        lines.extend([
            "",
            "===== TOP UX PRIORITY =====",
            f"Problem: {top['name']}",
            f"Affected users: {top['affected']}",
            f"Percentage: {top['percentage']}%",
            f"Priority: {top['score']}/30 ({top['priority']})",
            "",
            "===== UX RECOMMENDATION =====",
            f"Prioritize improvements to {top['name']} first, then address the remaining issues in priority order.",
        ])

    return "\n".join(lines)


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI UX Researcher",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.html("""
<style>

.stApp {
    background: #f6f8fc;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

/* ---------- SIDEBAR ---------- */

[data-testid="stSidebar"] {
    background: #111827;
}

[data-testid="stSidebar"] * {
    color: #f9fafb;
}

.brand {
    padding: 10px 5px 30px 5px;
}

.brand-title {
    font-size: 23px;
    font-weight: 700;
}

.brand-subtitle {
    color: #9ca3af !important;
    font-size: 13px;
    line-height: 1.5;
    margin-top: 5px;
}

.nav-item {
    padding: 12px 14px;
    border-radius: 10px;
    margin: 5px 0;
    color: #d1d5db !important;
    font-size: 14px;
}

.nav-active {
    background: #273449;
    color: white !important;
}

.sidebar-bottom {
    margin-top: 80px;
    padding: 15px;
    border: 1px solid #374151;
    border-radius: 12px;
    background: #1f2937;
}


/* ---------- HERO ---------- */

.hero {
    background: linear-gradient(
        135deg,
        #ffffff 0%,
        #eef2ff 100%
    );
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    padding: 35px;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 42px;
    line-height: 1.15;
    font-weight: 750;
    color: #111827;
    margin-bottom: 12px;
}

.hero-text {
    font-size: 16px;
    color: #6b7280;
    max-width: 650px;
    line-height: 1.6;
}

.hero-badge {
    display: inline-block;
    background: #e0e7ff;
    color: #4338ca;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 15px;
}


/* ---------- STAT CARDS ---------- */

.stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
    min-height: 145px;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
}

.stat-label {
    color: #6b7280;
    font-size: 13px;
}

.stat-number {
    color: #111827;
    font-size: 30px;
    font-weight: 750;
    margin-top: 8px;
}

.stat-icon {
    font-size: 22px;
}


/* ---------- SECTION ---------- */

.section-title {
    font-size: 21px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 3px;
}

.section-subtitle {
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 15px;
}


/* ---------- PROBLEM CARDS ---------- */

.problem-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 12px;
}

.problem-name {
    font-size: 16px;
    font-weight: 700;
    color: #111827;
}

.problem-meta {
    color: #6b7280;
    font-size: 13px;
    margin-top: 5px;
}

.priority-high {
    background: #fee2e2;
    color: #b91c1c;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
}

.priority-medium {
    background: #fef3c7;
    color: #92400e;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
}


/* ---------- AI CHAT ---------- */

.chat-box {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
    min-height: 360px;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
}

.ai-message {
    background: #f1f5f9;
    padding: 14px;
    border-radius: 12px;
    color: #374151;
    font-size: 13px;
    line-height: 1.6;
    margin: 12px 0;
}

.user-message {
    background: #eef2ff;
    padding: 12px;
    border-radius: 12px;
    color: #3730a3;
    font-size: 13px;
    margin: 12px 0;
    text-align: right;
}


/* ---------- FOOTER ---------- */

.cta {
    background: linear-gradient(
        90deg,
        #ecfdf5,
        #eff6ff
    );
    border: 1px solid #d1fae5;
    border-radius: 16px;
    padding: 18px 22px;
    margin-top: 25px;
}

</style>
""")


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "analysis_ready" not in st.session_state:
    st.session_state["analysis_ready"] = False

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "sample_reviews" not in st.session_state:
    st.session_state["sample_reviews"] = None

if "sample_selected" not in st.session_state:
    st.session_state["sample_selected"] = False

if "analysis_data" not in st.session_state:
    st.session_state["analysis_data"] = None

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "last_research_problem" not in st.session_state:
    st.session_state["last_research_problem"] = None


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.html("""
    <div class="brand">
        <div class="brand-title">🤖 AI UX Researcher</div>
        <div class="brand-subtitle">
            Turn user feedback into better experiences.
        </div>
    </div>
    """)

    st.html(
        '<div class="nav-item nav-active">🏠 &nbsp; Home</div>'
    )

    st.html(
        '<div class="nav-item">🔍 &nbsp; Analyze Reviews</div>'
    )

    st.html(
        '<div class="nav-item">📊 &nbsp; Results</div>'
    )

    st.html(
        '<div class="nav-item">🎯 &nbsp; Priorities</div>'
    )

    st.html(
        '<div class="nav-item">💡 &nbsp; Insights</div>'
    )

    st.html(
        '<div class="nav-item">💬 &nbsp; AI Chat</div>'
    )

    st.html(
        '<div class="nav-item">📄 &nbsp; Export Report</div>'
    )

    st.html(
        '<div class="nav-item">⚙️ &nbsp; Settings</div>'
    )

    st.html("""
    <div class="sidebar-bottom">
        <b>Built by Naveen</b><br>
        <span style="color:#9ca3af;font-size:12px;">
            Exploring the future of UX with AI.
        </span>
    </div>
    """)


# ---------------------------------------------------------
# HERO
# ---------------------------------------------------------

st.html("""
<div class="hero">
    <div class="hero-badge">✦ AI-POWERED UX RESEARCH</div>

    <div class="hero-title">
        Turn User Feedback into<br>
        Actionable UX Insights
    </div>

    <div class="hero-text">
        Upload customer reviews and let AI identify UX problems,
        measure their impact, prioritize what to fix,
        and generate actionable recommendations.
    </div>
</div>
""")


# ---------------------------------------------------------
# UPLOAD AREA
# ---------------------------------------------------------

st.html(
    '<div class="section-title">📄 Analyze User Reviews</div>'
)

st.html(
    '<div class="section-subtitle">'
    'Upload customer feedback and start your UX research analysis'
    '</div>'
)


upload_col, sample_col = st.columns([3, 1])


# ---------------------------------------------------------
# UPLOAD REVIEWS
# ---------------------------------------------------------

with upload_col:

    uploaded_file = st.file_uploader(
        "Upload your reviews",
        type=["txt", "csv"],
        help="Upload a TXT or CSV file containing user feedback."
    )

    if uploaded_file is not None:

        reviews_text = uploaded_file.read().decode("utf-8")

        st.success(
            f"✓ {uploaded_file.name} is ready for analysis"
        )

        if st.button(
            "🧪 Analyze Locally (No API)",
            use_container_width=True,
            type="primary"
        ):

            with st.spinner("🧮 Python is analyzing your reviews..."):
                data = run_local_demo(reviews_text)
                result = build_local_report(data)

            st.session_state["analysis_ready"] = True
            st.session_state["analysis_result"] = result
            st.session_state["analysis_data"] = data

            st.success("✅ Local V4.3 analysis complete!")

        st.caption("Gemini mode is temporarily paused because the API free-tier quota is exhausted.")


# ---------------------------------------------------------
# SAMPLE DATA
# ---------------------------------------------------------

with sample_col:

    st.write("")

    if st.button(
        "🧪 Try Sample Data",
        use_container_width=True
    ):

        st.session_state["sample_selected"] = True

        st.session_state["sample_reviews"] = """User 1: I couldn't understand which grocery product was best for me.
User 2: The price shown on the product page was different from the final price.
User 3: I didn't know when my groceries would arrive.
User 4: There were too many products and no proper guidance to choose one.
User 5: Delivery charges appeared only at checkout.
User 6: I wanted to know the delivery time before placing the order.
User 7: Product search gave me too many irrelevant results.
User 8: The final amount was higher than I expected.
User 9: I couldn't easily compare similar products.
User 10: The estimated delivery time wasn't clearly visible."""

        st.info(
            "🧪 Sample grocery review dataset selected."
        )


# ---------------------------------------------------------
# SAMPLE ANALYSIS BUTTON
# ---------------------------------------------------------

if st.session_state["sample_selected"]:

    if st.button(
        "🔍 Analyze Sample Reviews (Local Demo)",
        use_container_width=True,
        type="primary"
    ):

        with st.spinner("🧮 Running V4.3 local analysis..."):
            data = run_local_demo(st.session_state["sample_reviews"])
            result = build_local_report(data)

        st.session_state["analysis_ready"] = True
        st.session_state["analysis_result"] = result
        st.session_state["analysis_data"] = data

        st.success("✅ Sample analysis complete — no Gemini API request used.")


# SHOW REAL AGENT RESULT
# ---------------------------------------------------------

if st.session_state["analysis_result"]:

    st.html(
        '<div class="section-title">🤖 AI Research Result</div>'
    )

    st.html(
        '<div class="section-subtitle">'
        'Raw result returned by your V3 UX Research Agent'
        '</div>'
    )

    st.code(
        st.session_state["analysis_result"],
        language="text"
    )


st.divider()


# ---------------------------------------------------------
# RESEARCH OVERVIEW
# ---------------------------------------------------------

st.html(
    '<div class="section-title">Research Overview</div>'
)

st.html(
    '<div class="section-subtitle">'
    'Your UX research at a glance'
    '</div>'
)


# ---------------------------------------------------------
# STAT CARDS
# ---------------------------------------------------------

analysis = st.session_state.get("analysis_data")
review_count = analysis["total"] if analysis else 0
critical_count = analysis["critical"] if analysis else 0
high_count = analysis["high"] if analysis else 0
problem_count = len(analysis["problems"]) if analysis else 0

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.html(f"""
    <div class=\"stat-card\">
        <div class=\"stat-icon\">👥</div>
        <div class=\"stat-label\">Reviews Analyzed</div>
        <div class=\"stat-number\">{review_count if analysis else '—'}</div>
        <div style=\"color:#16a34a;font-size:12px;margin-top:5px;\">
            {analysis['mode'] if analysis else 'Run an analysis'}
        </div>
    </div>
    """)

with c2:
    st.html(f"""
    <div class=\"stat-card\">
        <div class=\"stat-icon\">🔴</div>
        <div class=\"stat-label\">Critical Issues</div>
        <div class=\"stat-number\">{critical_count if analysis else '—'}</div>
        <div style=\"color:#dc2626;font-size:12px;margin-top:5px;\">
            Based on priority score
        </div>
    </div>
    """)

with c3:
    st.html(f"""
    <div class=\"stat-card\">
        <div class=\"stat-icon\">🎯</div>
        <div class=\"stat-label\">High Priority</div>
        <div class=\"stat-number\">{high_count if analysis else '—'}</div>
        <div style=\"color:#ea580c;font-size:12px;margin-top:5px;\">
            Based on priority score
        </div>
    </div>
    """)

with c4:
    st.html(f"""
    <div class=\"stat-card\">
        <div class=\"stat-icon\">💡</div>
        <div class=\"stat-label\">UX Problems</div>
        <div class=\"stat-number\">{problem_count if analysis else '—'}</div>
        <div style=\"color:#2563eb;font-size:12px;margin-top:5px;\">
            Unique problems identified
        </div>
    </div>
    """)

st.write("")


# ---------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------

left, right = st.columns([1.7, 1])


# ---------------------------------------------------------
# TOP UX PROBLEMS
# ---------------------------------------------------------

with left:

    st.html(
        '<div class="section-title">🎯 Top UX Problems</div>'
    )

    st.html(
        '<div class="section-subtitle">'
        'Problems ranked by priority score'
        '</div>'
    )

    analysis = st.session_state.get("analysis_data")

    if analysis:
        for i, p in enumerate(analysis["problems"], 1):
            badge_class = "priority-high" if p["priority"] in ["CRITICAL", "HIGH"] else "priority-medium"
            st.html(f"""
            <div class=\"problem-card\">
                <div style=\"display:flex;justify-content:space-between;align-items:center;\">
                    <div>
                        <div class=\"problem-name\">{i}. {p['name']}</div>
                        <div class=\"problem-meta\">
                            {p['affected']} users · {p['percentage']}% affected · Score {p['score']}/30
                        </div>
                    </div>
                    <span class=\"{badge_class}\">{p['priority']}</span>
                </div>
                <div class=\"problem-meta\">
                    Frequency {p['frequency_score']}/10 · Severity {p['severity']}/10 · Business Impact {p['business_impact']}/10
                </div>
            </div>
            """)
    else:
        st.info("Run the Local V4.3 Demo to populate the real UX problems.")


# ---------------------------------------------------------
# UX ANALYTICS
# ---------------------------------------------------------

with left:

    st.write("")

    chart_left, chart_right = st.columns(2)


    # -----------------------------------------------------
    # PROBLEM FREQUENCY
    # -----------------------------------------------------

    with chart_left:

        st.html(
            '<div class="section-title">📊 UX Problem Frequency</div>'
        )

        st.html(
            '<div class="section-subtitle">'
            'Will be populated from the real AI analysis'
            '</div>'
        )

        if analysis and analysis["problems"]:
            frequency_df = pd.DataFrame(
                {
                    "UX Problem": [p["name"] for p in analysis["problems"]],
                    "Affected Users": [p["affected"] for p in analysis["problems"]],
                }
            ).set_index("UX Problem")

            st.bar_chart(
                frequency_df,
                use_container_width=True
            )
        else:
            st.info("Run the Local V4.3 Demo to see the real frequency chart.")


    # -----------------------------------------------------
    # PRIORITY DISTRIBUTION
    # -----------------------------------------------------

    with chart_right:

        st.html(
            '<div class="section-title">🎯 Priority Distribution</div>'
        )

        st.html(
            '<div class="section-subtitle">'
            'Will be populated from the real AI analysis'
            '</div>'
        )

        if analysis:
            priority_df = pd.DataFrame(
                {
                    "Priority": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                    "Issues": [
                        analysis["critical"],
                        analysis["high"],
                        analysis["medium"],
                        analysis["low"],
                    ],
                }
            ).set_index("Priority")

            st.bar_chart(
                priority_df,
                use_container_width=True
            )
        else:
            st.info("Run the Local V4.3 Demo to see the real priority chart.")


# ---------------------------------------------------------
# AI ASSISTANT
# ---------------------------------------------------------

with right:

    st.html("""
    <div class="chat-box">

        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:18px;
        ">

            <div style="
                display:flex;
                align-items:center;
                gap:10px;
            ">

                <div style="
                    width:38px;
                    height:38px;
                    border-radius:12px;
                    background:#eef2ff;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:20px;
                ">
                    🤖
                </div>

                <div>

                    <div class="section-title" style="font-size:17px;">
                        AI Research Assistant
                    </div>

                    <div style="
                        color:#16a34a;
                        font-size:11px;
                        margin-top:2px;
                    ">
                        ● Online
                    </div>

                </div>

            </div>

        </div>

        <div class="ai-message">

            <b>👋 Hi Naveen!</b>

            <br><br>

            I'm your AI UX Research Assistant. I can help you
            understand your research findings, explain priority
            scores and suggest improvements.

        </div>

        <div style="
            font-size:12px;
            font-weight:600;
            color:#6b7280;
            margin-top:18px;
        ">
            ASK YOUR QUESTION
        </div>

    </div>
    """)

    # Conversation history
    if st.session_state["chat_history"]:

        for chat in st.session_state["chat_history"]:

            st.markdown(
                f"**You:** {chat['question']}"
            )

            st.markdown(
                f"**🤖 AI Researcher:** {chat['answer']}"
            )

            st.divider()

    # Question input
    with st.form("research_chat_form", clear_on_submit=True):
        question = st.text_input(
            "Ask your research question",
            placeholder="Ask anything about your UX research..."
        )
        ask_clicked = st.form_submit_button(
            "Ask AI Researcher",
            use_container_width=True
        )

    if ask_clicked and question.strip():
        answer = answer_research_question(
            question,
            st.session_state["analysis_data"]
        )

        st.session_state["chat_history"].append({
            "question": question,
            "answer": answer
        })
        st.rerun()

    q1 = st.button(
        "🎯 Why is Price Transparency high priority?",
        use_container_width=True
    )

    q2 = st.button(
        "💡 What should we fix first?",
        use_container_width=True
    )

    q3 = st.button(
        "📊 Explain the research results",
        use_container_width=True
    )


    if q1:

        st.html("""
        <div class="user-message">
            Why is Price Transparency high priority?
        </div>

        <div class="ai-message">

            <b>Price Transparency</b> can be evaluated using
            frequency, severity and business impact.

            <br><br>

            The final explanation will come from the
            real AI research result.

        </div>
        """)


    elif q2:

        st.html("""
        <div class="user-message">
            What should we fix first?
        </div>

        <div class="ai-message">

            The first issue should be determined from the
            priority ranking generated by the UX research agent.

        </div>
        """)


    elif q3:

        st.html("""
        <div class="user-message">
            Explain the research results.
        </div>

        <div class="ai-message">

            The AI research agent analyzes the reviews,
            identifies UX problems, measures frequency,
            and generates research findings.

        </div>
        """)
# ---------------------------------------------------------
# FOOTER CTA
# ---------------------------------------------------------

st.html("""
<div class="cta">

    <div style="
        display:flex;
        justify-content:space-between;
        align-items:center;
    ">

        <div>

            <div style="
                font-size:17px;
                font-weight:700;
                color:#111827;
            ">
                🎯 Ready to improve your product?
            </div>

            <div style="
                color:#6b7280;
                font-size:13px;
                margin-top:4px;
            ">
                Generate a complete UX research report
                with prioritized recommendations.
            </div>

        </div>

    </div>

</div>
""")