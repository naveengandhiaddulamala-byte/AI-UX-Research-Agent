import streamlit as st  # type: ignore[import-not-found]
import hashlib
from agent import (
    run_ux_research,
    match_ux_themes,
    build_ux_trend_comparison,
    suggest_project_workspace
)


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
    import csv
    import io

    reviews = []

    # Try CSV format first
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames:
        fieldnames = [name.strip().lower() for name in reader.fieldnames]

        if "user_id" in fieldnames and "feedback" in fieldnames:
            for row in reader:
                reviews.append({
                    "user": row["user_id"].strip(),
                    "review": row["feedback"].strip()
                })

            return reviews

    # Fall back to original TXT format
    for line in text.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        user, review = line.split(":", 1)

        reviews.append({
            "user": user.strip(),
            "review": review.strip()
        })

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
        "best for me",
        "too many products",
        "guidance to choose",
        "compare similar",
        "couldn't understand which",
        "could not understand which"
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

    research_gaps = {
        "Price Transparency": {
            "gap": (
                "What pricing information do users expect "
                "to see before checkout?"
            ),
            "methods": {
                "Survey": (
                    "Ask users what pricing information they "
                    "expect to see before checkout."
                ),
                "Usability Test": (
                    "Observe users moving from product selection "
                    "to checkout to identify where pricing "
                    "becomes unclear."
                ),
            },
            "usability_task": (
                 "Choose a grocery product you would normally buy, "
    "add it to your cart, and continue through the "
    "purchase journey until the checkout screen."
            ),
        }
    }

    # V4.9 — Research Gap Detection
    if (
        "research gap" in q
        or "research gaps" in q
        or "what don't we know" in q
        or "what do we not know" in q
        or "what is missing" in q
    ):
        if not matched_problem:
            return (
                "I can help with research gaps for a specific UX problem, "
                "such as Price Transparency."
            )

        gap_data = research_gaps.get(matched_problem["name"])

        if gap_data:
            methods_text = "\n".join(
                f"- {method}: {description}"
                for method, description in gap_data["methods"].items()
            )

            st.session_state["last_research_problem"] = (
                matched_problem["name"]
            )

            return (
                f"Research Gaps — {matched_problem['name']}\n\n"
                f"What we know:\n"
                f"{matched_problem['affected']} users "
                f"({matched_problem['percentage']}%) "
                f"experienced this problem.\n\n"

                f"What we still need to understand:\n"
                f"{gap_data['gap']}\n\n"

                f"Suggested Research Methods:\n"
                f"{methods_text}\n\n"

                f"Usability Test Task:\n"
                f"{gap_data['usability_task']}"
            )

        return (
            f"I don't have a defined research gap for "
            f"{matched_problem['name']} yet."
        )

    # V4.8 — Research Question Suggestions
    if (
        "what should i investigate" in q
        or "what should we investigate" in q
        or "what should i research" in q
        or "what should we research" in q
        or "what should i ask" in q
        or "what should we explore" in q
        or "what should i investigate next" in q
        or "what next" in q
    ):

        # Sort findings using the existing priority score.
        ranked_problems = sorted(
            problems,
            key=lambda x: (
                x["score"],
                x["affected"]
            ),
            reverse=True
        )

        top_problem = ranked_problems[0]

        second_problem = (
            ranked_problems[1]
            if len(ranked_problems) > 1
            else None
        )

        suggestions = [
            f"What evidence supports {top_problem['name']}?",
            f"Which users are affected by {top_problem['name']}?",
            f"What should I change in the UI for {top_problem['name']}?",
            f"Why should we improve {top_problem['name']}?"
        ]

        if second_problem:
            suggestions.append(
                f"Compare {top_problem['name']} and "
                f"{second_problem['name']}."
            )

        suggestion_text = "\n".join(
            f"{i}. {question}"
            for i, question in enumerate(suggestions, 1)
        )

        # Keep the top finding as conversation context.
        st.session_state["last_research_problem"] = (
            top_problem["name"]
        )

        return (
            f"Suggested Research Questions\n\n"
            f"Based on the current findings, "
            f"{top_problem['name']} has the highest current "
            f"priority score ({top_problem['score']}/30).\n\n"
            f"You could investigate:\n\n"
            f"{suggestion_text}"
        )
            # V4.7 — Compare UX Problems
    if "compare" in q:

        selected_problems = []

        for problem in problems:
            if problem["name"].lower() in q:
                selected_problems.append(problem)

        if len(selected_problems) == 2:

            problem_1 = selected_problems[0]
            problem_2 = selected_problems[1]

            evidence_1 = "\n".join(
                f'- "{evidence}"'
                for evidence in problem_1.get("evidence", [])
            )

            evidence_2 = "\n".join(
                f'- "{evidence}"'
                for evidence in problem_2.get("evidence", [])
            )

            comparison_points = []

            if problem_1["affected"] == problem_2["affected"]:
                comparison_points.append(
                    f"Both problems affect the same number of users "
                    f"({problem_1['affected']} users)."
                )
            else:
                comparison_points.append(
                    f"{problem_1['name']} affects "
                    f"{problem_1['affected']} users, while "
                    f"{problem_2['name']} affects "
                    f"{problem_2['affected']} users."
                )

            if problem_1["severity"] == problem_2["severity"]:
                comparison_points.append(
                    f"Both problems have the same severity score "
                    f"({problem_1['severity']}/10)."
                )
            else:
                comparison_points.append(
                    f"Severity scores: {problem_1['name']} "
                    f"{problem_1['severity']}/10 and "
                    f"{problem_2['name']} "
                    f"{problem_2['severity']}/10."
                )

            if problem_1["business_impact"] == problem_2["business_impact"]:
                comparison_points.append(
                    f"Both problems have the same business impact score "
                    f"({problem_1['business_impact']}/10)."
                )
            else:
                comparison_points.append(
                    f"Business impact scores: {problem_1['name']} "
                    f"{problem_1['business_impact']}/10 and "
                    f"{problem_2['name']} "
                    f"{problem_2['business_impact']}/10."
                )

            comparison_text = "\n".join(
                f"- {point}"
                for point in comparison_points
            )

            return (
                f"UX Problem Comparison\n\n"

                f"{problem_1['name']}\n"
                f"Affected Users: {problem_1['affected']} "
                f"({problem_1['percentage']}%)\n"
                f"Severity: {problem_1['severity']}/10\n"
                f"Business Impact: "
                f"{problem_1['business_impact']}/10\n"
                f"Priority Score: {problem_1['score']}/30\n"
                f"Priority: {problem_1['priority']}\n\n"

                f"VS\n\n"

                f"{problem_2['name']}\n"
                f"Affected Users: {problem_2['affected']} "
                f"({problem_2['percentage']}%)\n"
                f"Severity: {problem_2['severity']}/10\n"
                f"Business Impact: "
                f"{problem_2['business_impact']}/10\n"
                f"Priority Score: {problem_2['score']}/30\n"
                f"Priority: {problem_2['priority']}\n\n"

                f"Key Differences\n"
                f"{comparison_text}\n\n"

                f"Evidence — {problem_1['name']}\n"
                f"{evidence_1}\n\n"

                f"Evidence — {problem_2['name']}\n"
                f"{evidence_2}"
            )
        return (
            "Please mention exactly two UX problems to compare. "
            "For example: Compare Price Transparency and "
            "Delivery Information."
        )
    
        # V4.6 — Research Summary
    if (
        "research summary" in q
        or "summarize the research" in q
        or "summary of this research" in q
        or "what did we learn" in q
        or "summarise the research" in q
    ):
        top_problem = max(
            problems,
            key=lambda x: x["score"]
        )

        problem_summary = "\n".join(
            f"- {problem['name']}: "
            f"{problem['affected']} users "
            f"({problem['percentage']}%), "
            f"{problem['priority']} priority"
            for problem in problems
        )

        top_evidence = "\n".join(
            f"- {evidence}"
            for evidence in top_problem.get("evidence", [])
        )

        return (
            f"UX Research Summary\n\n"
            f"Total users analyzed: {total}\n\n"
            f"Key UX Problems:\n"
            f"{problem_summary}\n\n"
            f"Top Priority: {top_problem['name']}\n"
            f"Priority Score: {top_problem['score']}/30 "
            f"({top_problem['priority']})\n"
            f"Severity: {top_problem['severity']}/10\n"
            f"Business Impact: "
            f"{top_problem['business_impact']}/10\n\n"
            f"Supporting Evidence:\n"
            f"{top_evidence}\n\n"
            f"Recommended Next Step:\n"
            f"Prioritize {top_problem['name']} first, "
            f"review the supporting user evidence, "
            f"prototype an improved experience, and "
            f"validate the solution with users."
        )
        # V4.5 — Evidence-to-Design Reasoning
    if matched_problem and (
        "why should we" in q
        or "why should i" in q
        or "why this change" in q
        or "why this design" in q
        or "reason for this" in q
    ):
        st.session_state["last_research_problem"] = matched_problem["name"]

        evidence = matched_problem.get("evidence", [])

        if evidence:
            evidence_text = "\n\n".join(
                f"- {quote}"
                for quote in evidence
            )

            return (
                f"Research reasoning for {matched_problem['name']}:\n\n"
                f"The recommendation is supported by the following "
                f"user evidence:\n\n"
                f"{evidence_text}\n\n"
                f"These findings show that users are experiencing "
                f"friction related to {matched_problem['name']}. "
                f"The suggested UI changes are intended to directly "
                f"address the problems observed in this feedback."
            )

        return (
            f"There is not enough user evidence available to explain "
            f"the design reasoning for {matched_problem['name']}."
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

# ==========================================
# RESEARCH PROJECTS SESSION STATE
# ==========================================

if "creating_project" not in st.session_state:
    st.session_state.creating_project = False

if "project_setup_step" not in st.session_state:
    st.session_state.project_setup_step = 1

if "new_project_data" not in st.session_state:
    st.session_state.new_project_data = {
        "name": "",
        "type": "",
        "research_goal": "",
        "description": "",
        "workspace_sections": []
    }

if "workspace_ai_suggestion" not in st.session_state:
    st.session_state.workspace_ai_suggestion = None


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
# RESEARCH PROJECTS
# ---------------------------------------------------------

project_col, spacer_col = st.columns([1, 3])

with project_col:
    if st.button(
        "＋ New Research Project",
        type="primary",
        key="new_research_project"
    ):
        st.session_state.creating_project = True
        st.session_state.project_setup_step = 1

        st.session_state.new_project_data = {
            "name": "",
            "type": "",
            "research_goal": "",
            "description": "",
            "workspace_sections": []
        }

        st.session_state.workspace_ai_suggestion = None

        if "project_workspace_sections" in st.session_state:
            del st.session_state["project_workspace_sections"]

        st.rerun()

if (
    st.session_state.creating_project
    and st.session_state.project_setup_step == 1
):
    # ---------------------------------------------------------
    # PROJECT CREATION - STEP 1
    # ---------------------------------------------------------
    st.divider()

    st.subheader("Create New Research Project")
    st.caption("Step 1 of 4 — Project Details")

    project_name = st.text_input(
        "Project Name *",
        value=st.session_state.new_project_data["name"],
        placeholder="Example: Freshcart Checkout Redesign"
    )

    project_type = st.selectbox(
        "Project Type *",
        [
            "Select project type",
            "Mobile App",
            "Website",
            "SaaS Product",
            "E-commerce",
            "Service",
            "Other"
        ]
    )

    research_goal = st.text_area(
        "Research Goal *",
        value=st.session_state.new_project_data["research_goal"],
        placeholder="Example: Understand why users abandon checkout"
    )

    description = st.text_area(
        "Description",
        value=st.session_state.new_project_data["description"],
        placeholder="Describe what you want to research..."
    )

    if st.button("Continue →", type="primary"):
        if not project_name.strip():
            st.warning("Please enter a project name.")

        elif project_type == "Select project type":
            st.warning("Please select a project type.")

        elif not research_goal.strip():
            st.warning("Please enter a research goal.")

        else:
            st.session_state.new_project_data["name"] = project_name
            st.session_state.new_project_data["type"] = project_type
            st.session_state.new_project_data["research_goal"] = research_goal
            st.session_state.new_project_data["description"] = description

            st.session_state.project_setup_step = 2
            st.rerun()

# ---------------------------------------------------------
# PROJECT CREATION - STEP 2
# ---------------------------------------------------------

if (
    st.session_state.creating_project
    and st.session_state.project_setup_step == 2
):
    st.divider()

    st.subheader("Customize Research Workspace")
    st.caption("Step 2 of 4 — Research Workspace")

    st.write(
        "Choose what you want to track in this project. "
        "You can customize these sections later."
    )

    default_sections = [
        "Overview",
        "Research Data",
        "UX Findings",
        "Evidence",
        "Recommendations",
        "Trend Analysis",
    ]

    # Initialize workspace sections only once
    if not st.session_state.new_project_data.get("workspace_sections"):
        st.session_state.new_project_data["workspace_sections"] = list(
            default_sections
        )

    saved_sections = st.session_state.new_project_data["workspace_sections"]

    # Make sure custom / AI-renamed sections remain available
    workspace_options = list(dict.fromkeys(default_sections + saved_sections))

    # Rebuild widget state from our saved project state when needed
    if "project_workspace_sections" not in st.session_state:
        st.session_state.project_workspace_sections = list(saved_sections)

    selected_sections = st.multiselect(
        "Workspace Sections",
        workspace_options,
        key="project_workspace_sections",
    )

    # Save the current researcher selection
    st.session_state.new_project_data["workspace_sections"] = list(
        selected_sections
    )

        # -----------------------------------------
    # REORDER WORKSPACE SECTIONS
    # -----------------------------------------

    st.markdown("#### Reorder Sections")
    st.caption("Move sections up or down to organize your workspace.")

    for index, section in enumerate(selected_sections):
        name_col, up_col, down_col = st.columns([5, 1, 1])

        with name_col:
            st.write(section)

        with up_col:
            if st.button(
                "↑",
                key=f"move_section_up_{index}",
                disabled=(index == 0)
            ):
                updated_sections = list(selected_sections)

                updated_sections[index - 1], updated_sections[index] = (
                    updated_sections[index],
                    updated_sections[index - 1]
                )

                st.session_state.new_project_data[
                    "workspace_sections"
                ] = updated_sections

                if "project_workspace_sections" in st.session_state:
                    del st.session_state["project_workspace_sections"]

                st.session_state.workspace_ai_suggestion = None
                st.rerun()

        with down_col:
            if st.button(
                "↓",
                key=f"move_section_down_{index}",
                disabled=(index == len(selected_sections) - 1)
            ):
                updated_sections = list(selected_sections)

                updated_sections[index], updated_sections[index + 1] = (
                    updated_sections[index + 1],
                    updated_sections[index]
                )

                st.session_state.new_project_data[
                    "workspace_sections"
                ] = updated_sections

                if "project_workspace_sections" in st.session_state:
                    del st.session_state["project_workspace_sections"]

                st.session_state.workspace_ai_suggestion = None
                st.rerun()

       # -----------------------------------------
    # MANUAL RENAME SECTION
    # -----------------------------------------

    st.markdown("#### Rename a Section")

    rename_section = st.selectbox(
        "Choose section to rename",
        selected_sections,
        key="manual_rename_section",
    )

    new_section_name = st.text_input(
        "New section name",
        placeholder="Example: Customer Feedback",
        key="manual_rename_name",
    )

    if st.button(
        "Rename Section",
        key="manual_rename_button"
    ):
        clean_name = new_section_name.strip()

        if not clean_name:
            st.warning("Enter a new section name.")

        elif clean_name == rename_section:
            st.warning("Enter a different section name.")

        elif clean_name in selected_sections:
            st.warning("A section with this name already exists.")

        else:
            updated_sections = [
                clean_name if section == rename_section else section
                for section in selected_sections
            ]

            st.session_state.new_project_data[
                "workspace_sections"
            ] = updated_sections

            if "project_workspace_sections" in st.session_state:
                del st.session_state["project_workspace_sections"]

            st.session_state.workspace_ai_suggestion = None
            # Clear the rename form after successful rename
            if "manual_rename_section" in st.session_state:
                del st.session_state["manual_rename_section"]

            if "manual_rename_name" in st.session_state:
                del st.session_state["manual_rename_name"]

            st.rerun()

                # -----------------------------------------
    # MANUAL REMOVE SECTION
    # -----------------------------------------

    st.markdown("#### Remove a Section")

    remove_section = st.selectbox(
        "Choose section to remove",
        selected_sections,
        key="manual_remove_section"
    )

    if st.button(
        "Remove Section",
        key="manual_remove_button"
    ):
        if len(selected_sections) <= 1:
            st.warning(
                "Your workspace must contain at least one section."
            )

        else:
            updated_sections = [
                section
                for section in selected_sections
                if section != remove_section
            ]

            st.session_state.new_project_data[
                "workspace_sections"
            ] = updated_sections

            if "project_workspace_sections" in st.session_state:
                del st.session_state["project_workspace_sections"]

            # Clear old AI suggestions because workspace changed
            st.session_state.workspace_ai_suggestion = None

            # Reset remove selector
            if "manual_remove_section" in st.session_state:
                del st.session_state["manual_remove_section"]

            st.rerun()


    # -----------------------------------------
    # ADD CUSTOM SECTION
    # -----------------------------------------

    st.markdown("#### Add Your Own Section")

    custom_section = st.text_input(
        "Section name",
        placeholder="Example: User Interviews",
        key="custom_workspace_section",
    )

    if st.button("＋ Add Section", key="add_custom_workspace_section"):
        new_section = custom_section.strip()

        if not new_section:
            st.warning("Enter a section name first.")

        elif new_section in selected_sections:
            st.warning("This section already exists.")

        else:
            updated_sections = selected_sections + [new_section]

            st.session_state.new_project_data[
                "workspace_sections"
            ] = updated_sections

            # Remove the old widget state before rerunning.
            if "project_workspace_sections" in st.session_state:
                del st.session_state["project_workspace_sections"]

            st.rerun()

    if st.button(
        "✨ Suggest Workspace with AI",
        key="suggest_workspace_ai"
    ):
        st.session_state.new_project_data[
            "workspace_sections"
        ] = list(selected_sections)

        with st.spinner(
            "AI is reviewing your research workspace..."
        ):
            project = st.session_state.new_project_data

            workspace_suggestion = suggest_project_workspace(
                project_name=project["name"],
                project_type=project["type"],
                research_goal=project["research_goal"],
                description=project["description"],
                current_sections=selected_sections,
            )

            st.session_state.workspace_ai_suggestion = (
                workspace_suggestion
            )

# -----------------------------------------
# DISPLAY AI WORKSPACE SUGGESTIONS
# -----------------------------------------

    workspace_suggestion = st.session_state.get("workspace_ai_suggestion")

    if workspace_suggestion is not None:
        if workspace_suggestion.get("error"):
            st.warning(workspace_suggestion["error"])
        else:
            suggestions = workspace_suggestion.get("suggestions", [])

            if suggestions:
                st.markdown("### ✨ AI Suggested Changes")
                st.caption(
                    "AI suggestions are optional. "
                    "Review each change before applying it."
                )

                for index, suggestion in enumerate(suggestions):
                    action = suggestion.get("action", "rename")
                    current_section = suggestion.get("current_section")
                    suggested_section = suggestion.get("suggested_section")
                    reason = suggestion.get("reason", "")

                    with st.container(border=True):
                        if action == "rename":
                            st.markdown(
                                f"**Rename:** {current_section} → **{suggested_section}**"
                            )
                            apply_label = "✓ Apply Rename"

                        elif action == "remove":
                            st.markdown(
                                f"**Suggested removal:** {current_section}"
                            )
                            apply_label = "Remove Section"

                        elif action == "add":
                            st.markdown(
                                f"**Suggested addition:** {suggested_section}"
                            )
                            apply_label = "＋ Add Section"

                        else:
                            continue

                        if reason:
                            st.caption(reason)

                        apply_col, keep_col = st.columns(2)

                        with apply_col:
                            if st.button(
                                apply_label,
                                key=f"apply_workspace_{index}"
                            ):
                                updated_sections = list(selected_sections)

                                if action == "rename":
                                    updated_sections = [
                                        suggested_section
                                        if section == current_section
                                        else section
                                        for section in updated_sections
                                    ]

                                elif action == "remove":
                                    updated_sections = [
                                        section
                                        for section in updated_sections
                                        if section != current_section
                                    ]

                                elif action == "add":
                                    if suggested_section not in updated_sections:
                                        updated_sections.append(suggested_section)

                                # Save project data first. Do not directly modify
                                # a widget key after that widget was instantiated.
                                st.session_state.new_project_data[
                                    "workspace_sections"
                                ] = updated_sections

                                if "project_workspace_sections" in st.session_state:
                                    del st.session_state["project_workspace_sections"]

                                st.session_state.workspace_ai_suggestion = None
                                st.rerun()

                        with keep_col:
                            if st.button(
                                "Keep Mine",
                                key=f"keep_workspace_{index}"
                            ):
                                remaining = [
                                    item
                                    for i, item in enumerate(suggestions)
                                    if i != index
                                ]
                                st.session_state.workspace_ai_suggestion = {
                                    "suggestions": remaining
                                }
                                st.rerun()
            else:
                st.info(
                    "Your current workspace already fits the project well. "
                    "AI did not suggest any changes."
                )

    st.markdown("#### Your Workspace")

    for section in selected_sections:
        st.write(f"✓ {section}")


    back_col, continue_col = st.columns([1, 1])

    with back_col:
        if st.button("← Back", key="workspace_back"):
            st.session_state.new_project_data["workspace_sections"] = selected_sections
            st.session_state.project_setup_step = 1
            st.rerun()

    with continue_col:
        if st.button(
            "Continue →",
            type="primary",
            key="workspace_continue"
        ):
            if not selected_sections:
                st.warning("Please select at least one workspace section.")
            else:
                st.session_state.new_project_data["workspace_sections"] = selected_sections
                st.session_state.project_setup_step = 3
                st.rerun()

                # ---------------------------------------------------------
# STEP 3 — AI WORKSPACE DESIGNER
# ---------------------------------------------------------

if (
    st.session_state.creating_project
    and st.session_state.project_setup_step == 3
):
    st.markdown("## ✨ AI Workspace Designer")

    st.write(
        "Your research workspace is ready. "
        "Next, AI will help design how your workspace should look."
    )

    st.markdown("#### Selected Workspace")

    for section in st.session_state.new_project_data["workspace_sections"]:
        st.write(f"✓ {section}")

    if st.button("← Back to Workspace", key="designer_back"):
        st.session_state.project_setup_step = 2
        st.rerun()


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

        st.divider()

if st.button(
    "✨ Analyze with V5 AI",
    use_container_width=True
):
    try:
        with st.spinner("🧠 V5 AI is analyzing your UX research data..."):
            result = run_ux_research(
                "Analyze these user reviews and identify the UX problems.",
                reviews_text=reviews_text
            )

        st.session_state["analysis_ready"] = True
        st.session_state["analysis_result"] = result

        st.success("✅ V5 AI analysis complete!")

    except Exception as e:
        error_message = str(e).lower()

        if (
            "503" in error_message
            or "unavailable" in error_message
            or "high demand" in error_message
            or "overloaded" in error_message
        ):
            st.warning(
                "🧠 AI analysis is temporarily unavailable because the AI service "
                "is experiencing high demand. Your uploaded reviews are ready — "
                "please try again shortly."
            )

        elif (
            "429" in error_message
            or "resource_exhausted" in error_message
            or "quota" in error_message
        ):
            st.warning(
                "⚠️ The AI usage limit has been reached temporarily. "
                "Please try again later."
            )

        else:
            st.error(
                "Something went wrong while analyzing the reviews. "
                "Please try again."
            )
            print("V5 ERROR:", repr(e))

            # Temporary debugging — terminal only


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
            frequency_data = {
                p["name"]: p["affected"]
                for p in analysis["problems"]
            }

            st.bar_chart(
                frequency_data,
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
            priority_data = {
                "CRITICAL": analysis["critical"],
                "HIGH": analysis["high"],
                "MEDIUM": analysis["medium"],
                "LOW": analysis["low"],
            }

            st.bar_chart(
                priority_data,
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

# ==========================================
# UX TREND ANALYSIS
# ==========================================

st.divider()

# ==========================================
# TREND ANALYSIS SESSION STATE
# ==========================================

if "previous_trend_analysis" not in st.session_state:
    st.session_state.previous_trend_analysis = None

if "trend_theme_matches" not in st.session_state:
    st.session_state.trend_theme_matches = None

if "trend_match_signature" not in st.session_state:
    st.session_state.trend_match_signature = None

if "current_trend_analysis" not in st.session_state:
    st.session_state.current_trend_analysis = None

if "previous_trend_file_signature" not in st.session_state:
    st.session_state.previous_trend_file_signature = None

if "current_trend_file_signature" not in st.session_state:
    st.session_state.current_trend_file_signature = None

st.header("📈 UX Trend Analysis")

st.write(
    "Compare previous user feedback with current feedback "
    "to understand how UX problems are changing over time."
)



trend_col1, trend_col2 = st.columns(2)

with trend_col1:
    previous_file = st.file_uploader(
        "📂 Previous Dataset",
        type=["csv", "txt"],
        key="previous_trend_dataset"
    )

with trend_col2:
    current_file = st.file_uploader(
        "📂 Current Dataset",
        type=["csv", "txt"],
        key="current_trend_dataset"
    )

if previous_file is not None and current_file is not None:
    previous_text = previous_file.getvalue().decode("utf-8")
    current_text = current_file.getvalue().decode("utf-8")
    previous_signature = hashlib.sha256(
        previous_file.getvalue()
    ).hexdigest()

    current_signature = hashlib.sha256(
        current_file.getvalue()
    ).hexdigest()

    st.write(
        "Previous dataset loaded:",
        previous_file.name
    )
    if st.button(
        "📊 Compare UX Trends",
        use_container_width=True
    ):
        try:
            if (
                st.session_state.previous_trend_analysis is None
                or st.session_state.previous_trend_file_signature != previous_signature
            ):
                st.session_state.previous_trend_analysis = run_ux_research(
                    "Analyze these user reviews and identify the UX problems.",
                    reviews_text=previous_text,
                    return_analysis=True
                )

            st.session_state.previous_trend_file_signature = previous_signature

            if (
                st.session_state.current_trend_analysis is None
                or st.session_state.current_trend_file_signature != current_signature
            ):
                with st.spinner("Analyzing current UX dataset..."):
                    st.session_state.current_trend_analysis = run_ux_research(
                        "Analyze these user reviews and identify the UX problems.",
                        reviews_text=current_text,
                        return_analysis=True
                    )

            st.session_state.current_trend_file_signature = current_signature

            previous_analysis = st.session_state.previous_trend_analysis
            current_analysis = st.session_state.current_trend_analysis

            st.success("✅ Previous dataset analysis complete!")

            st.write(
                "Previous dataset users:",
                previous_analysis["total_users"]
            )

            st.write(
                "UX themes found:",
                len(previous_analysis["problems"])
            )

            st.write(
                "Current dataset loaded:",
                current_file.name
            )

            st.success("✅ Current dataset analysis complete!")

            st.write(
                "Current dataset users:",
                current_analysis["total_users"]
            )

            st.write(
                "Current UX themes found:",
                len(current_analysis["problems"])
            )

            previous_themes = [
                item["problem"]
                for item in previous_analysis["problems"]
            ]

            current_themes = [
                item["problem"]
                for item in current_analysis["problems"]
            ]

            trend_match_signature = (
                previous_signature + current_signature
            )

            if (
                st.session_state.trend_theme_matches is None
                or st.session_state.trend_match_signature != trend_match_signature
            ):
                with st.spinner("Matching UX themes across datasets..."):
                    st.session_state.trend_theme_matches = match_ux_themes(
                        previous_themes,
                        current_themes
                    )

                st.session_state.trend_match_signature = trend_match_signature

            theme_matches = st.session_state.trend_theme_matches

            st.success("✅ UX themes matched!")

           # st.write("Theme matching result:")
            #st.json(theme_matches)

            trend_results = build_ux_trend_comparison(
                previous_analysis,
                current_analysis,
                theme_matches
            )

            st.subheader("📊 Trend Overview")

            increasing_count = sum(
                1 for item in trend_results
                if item["trend"] == "INCREASING"
            )

            decreasing_count = sum(
                1 for item in trend_results
                if item["trend"] == "DECREASING"
            )

            new_count = sum(
                1 for item in trend_results
                if item["trend"] == "NEWLY OBSERVED"
            )

            not_observed_count = sum(
                1 for item in trend_results
                if item["trend"] == "NOT OBSERVED IN CURRENT DATASET"
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("📈 Increasing", increasing_count)
            col2.metric("📉 Decreasing", decreasing_count)
            col3.metric("🆕 Newly Observed", new_count)
            col4.metric("◯ Not Observed", not_observed_count)

            st.divider()
            st.subheader("UX Trend Details")
            st.caption(
                "Compare how frequently each UX issue appears across the two research datasets."
            )

            for item in trend_results:
                problem = item["problem"]
                previous_users = item["previous_users"]
                previous_percentage = item["previous_percentage"]
                current_users = item["current_users"]
                current_percentage = item["current_percentage"]
                change = item["change"]
                trend = item["trend"]
                match_reason = item["match_reason"]

                with st.container(border=True):
                    st.markdown(f"### {problem}")

                    if trend == "INCREASING":
                        st.info(
                            "This UX issue appeared more frequently in the current dataset."
                        )
                    elif trend == "DECREASING":
                        st.success(
                            "This UX issue appeared less frequently in the current dataset."
                        )
                    elif trend == "NEWLY OBSERVED":
                        st.warning(
                            "This UX issue was observed in the current dataset but not in the previous dataset."
                        )
                    else:
                        st.info(
                            "This UX issue was not observed in the current dataset."
                        )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Previous Dataset",
                        f"{previous_percentage}%",
                        f"{previous_users} users"
                    )

                    col2.metric(
                        "Current Dataset",
                        f"{current_percentage}%",
                        f"{current_users} users"
                    )

                    if change > 0:
                        change_text = f"+{change} pp"
                    elif change < 0:
                        change_text = f"{change} pp"
                    else:
                        change_text = "0 pp"

                    col3.metric(
                        "Change",
                        change_text,
                        help="Difference in percentage points between the previous and current datasets."
                    )

                    if trend == "INCREASING":
                        status_text = "📈 INCREASING"
                    elif trend == "DECREASING":
                        status_text = "📉 DECREASING"
                    elif trend == "NEWLY OBSERVED":
                        status_text = "🆕 NEWLY OBSERVED"
                    else:
                        status_text = "◯ NOT OBSERVED IN CURRENT DATASET"

                    st.markdown(f"**Status:** {status_text}")

                    st.caption(
                        f"Theme match: {match_reason}"
                    )

           # st.json(trend_results)
        except Exception as e:
            error_message = str(e)

            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):
                st.warning(
                    "⚠️ AI service is temporarily busy. "
                    "Your uploaded files are safe. Please try again shortly."
                )

            elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                st.warning(
                    "⚠️ AI usage limit has been reached temporarily. "
                    "Please try again later."
                )

            else:
                st.error(
                    "Something went wrong while comparing the UX datasets. "
                    "Please try again."
                )