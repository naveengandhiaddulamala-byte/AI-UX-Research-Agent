import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

client = genai.Client(api_key=api_key)


# =========================================================
# TOOL 1: READ REVIEWS
# =========================================================

def read_reviews():
    """Read UX research reviews from reviews.txt."""

    with open("reviews.txt", "r", encoding="utf-8") as file:
        return file.read()


# =========================================================
# TOOL 2: PARSE REVIEWS
# =========================================================

def parse_reviews():
    """Parse reviews from either CSV or User: Review text format."""

    import csv
    import io

    reviews = []

    with open("reviews.txt", "r", encoding="utf-8") as file:
        text = file.read()

    # -----------------------------------------
    # Try CSV format first
    # -----------------------------------------
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames:
        field_map = {
            name.strip().lower(): name
            for name in reader.fieldnames
            if name
        }

        if "user_id" in field_map and "feedback" in field_map:

            user_column = field_map["user_id"]
            feedback_column = field_map["feedback"]

            for row in reader:

                user = (row.get(user_column) or "").strip()
                review = (row.get(feedback_column) or "").strip()

                if user and review:
                    reviews.append({
                        "user": user,
                        "review": review
                    })

            return reviews

    # -----------------------------------------
    # Fall back to original TXT format
    # -----------------------------------------
    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if ":" not in line:
            continue

        user, review = line.split(":", 1)

        user = user.strip()
        review = review.strip()

        if user and review:
            reviews.append({
                "user": user,
                "review": review
            })

    return reviews


# =========================================================
# TOOL 3: COUNT UX PROBLEMS
# =========================================================

def count_ux_problems(classifications):
    """Count how many users are affected by each UX problem."""

    problem_counts = {}

    for item in classifications:
        problem = item["problem"]

        if problem not in problem_counts:
            problem_counts[problem] = 0

        problem_counts[problem] += 1

    return problem_counts


# =========================================================
# TOOL 4: CALCULATE PERCENTAGE
# =========================================================

def calculate_percentage(part, total):
    """Calculate the percentage of users affected."""

    if total == 0:
        return 0

    return round((part / total) * 100, 2)


# =========================================================
# TOOL 5: SAVE REPORT
# =========================================================

def save_report(report):
    """Save the final UX research report to report.txt."""

    with open("report.txt", "w", encoding="utf-8") as file:
        file.write(report)

    return "Report successfully saved to report.txt"


# =========================================================
# TOOL 6: CALCULATE PRIORITY SCORE
# =========================================================

def calculate_priority_score(frequency_score, severity, business_impact):
    """Calculate the UX problem priority score."""

    frequency_score = int(frequency_score)
    severity = int(severity)
    business_impact = int(business_impact)

    score = frequency_score + severity + business_impact

    if score >= 24:
        priority = "CRITICAL"
    elif score >= 18:
        priority = "HIGH"
    elif score >= 10:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {
        "score": score,
        "priority": priority
    }


# =========================================================
# TOOL 7: PROCESS UX ANALYSIS
# =========================================================


def process_ux_analysis(classifications, assessments):
    """
    Perform deterministic UX calculations in Python.

    Gemini supplies the understanding/classification and
    evidence-based severity/business-impact assessments.
    Python performs counting, percentages, frequency scores,
    and priority calculations.
    """

    reviews = parse_reviews()
    total_users = len(reviews)

    problem_counts = count_ux_problems(classifications)

    assessment_map = {
        item["problem"]: item
        for item in assessments
    }

    results = []

    for problem, affected_users in problem_counts.items():

        percentage = calculate_percentage(
            affected_users,
            total_users
        )

        # Convert percentage to the 0-10 frequency score.
        frequency_score = min(
            10,
            int(round(percentage / 10))
        )

        assessment = assessment_map.get(problem, {})

        severity = max(
            1,
            min(10, int(assessment.get("severity", 5)))
        )

        business_impact = max(
            1,
            min(10, int(assessment.get("business_impact", 5)))
        )

        priority_result = calculate_priority_score(
            frequency_score,
            severity,
            business_impact
        )

        users = [
            item["user"]
            for item in classifications
            if item["problem"] == problem
        ]

        secondary_observations = [
            {
                "user": item["user"],
                "observations": item.get("secondary_observations", [])
            }
            for item in classifications
            if item["problem"] == problem
            and item.get("secondary_observations")
        ]

        results.append({
            "problem": problem,
            "affected_users": affected_users,
            "percentage": percentage,
            "frequency_score": frequency_score,
            "severity": severity,
            "business_impact": business_impact,
            "priority_score": priority_result["score"],
            "priority": priority_result["priority"],
            "users": users,
            "secondary_observations": secondary_observations
        })

    results.sort(
        key=lambda item: item["priority_score"],
        reverse=True
    )

    return {
        "total_users": total_users,
        "problems": results
    }

def validate_v5_classifications(classifications):
    """Validate the one-primary-problem-per-user rule."""

    users = [
        item["user"]
        for item in classifications
    ]

    unique_users = set(users)

    duplicate_users = [
        user
        for user in unique_users
        if users.count(user) > 1
    ]

    return {
        "total_classifications": len(classifications),
        "unique_users": len(unique_users),
        "duplicate_users": duplicate_users,
        "is_valid": (
            len(classifications) == 30
            and len(unique_users) == 30
            and len(duplicate_users) == 0
        )
    }


# =========================================================
# GEMINI TOOL DEFINITION
# =========================================================

analysis_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="process_ux_analysis",
            description=(
                "Processes Gemini's UX classifications and evidence-based "
                "severity/business-impact assessments. Python calculates "
                "affected-user counts, percentages, frequency scores, "
                "priority scores, and priority levels."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "classifications": types.Schema(
                        type="ARRAY",
                       description=(
    "One primary UX problem classification for every user. "
    "Each user must appear exactly once. If a review contains "
    "multiple issues, choose the primary problem using both "
    "task impact and strength of complaint. Closely related "
    "problems across users should share one broader UX theme."
),
                        items=types.Schema(
                            type="OBJECT",
                            properties={
                                "user": types.Schema(
                                    type="STRING",
                                    description="User identifier."
                                ),
                                "problem": types.Schema(
                                    type="STRING",
                                    description="UX problem identified."
                                ),
                                "secondary_observations": types.Schema(
                                    type="ARRAY",
                                    description=(
                                        "Other genuine UX issues mentioned in the user's review "
                                        "that were not selected as the primary problem. "
                                        "These are preserved as supporting observations and "
                                        "must not be counted as primary UX problems."
                                    ),
                                    items=types.Schema(
                                        type="STRING"
                                    )
                                )
                            },
                            required=["user", "problem"]
                        )
                    ),
                    "assessments": types.Schema(
                        type="ARRAY",
                        description=(
                            "One evidence-based assessment for every major "
                            "UX problem identified."
                        ),
                        items=types.Schema(
                            type="OBJECT",
                            properties={
                                "problem": types.Schema(
                                    type="STRING",
                                    description="UX problem name."
                                ),
                                "severity": types.Schema(
                                    type="NUMBER",
                                    description="Severity from 1 to 10."
                                ),
                                "business_impact": types.Schema(
                                    type="NUMBER",
                                    description="Business impact from 1 to 10."
                                )
                            },
                            required=[
                                "problem",
                                "severity",
                                "business_impact"
                            ]
                        )
                    )
                },
                required=["classifications", "assessments"]
            )
        )
    ]
)


# =========================================================
# MAIN AGENT FUNCTION
# =========================================================


def run_ux_research(user_question, reviews_text=None):
    """Run the optimized V4 UX research workflow."""

    # If Streamlit supplied uploaded/sample reviews,
    # save them so the existing Python tools can process them.
    if reviews_text:
        with open("reviews.txt", "w", encoding="utf-8") as file:
            file.write(reviews_text)

    reviews = parse_reviews()
    

    if not reviews:
        raise ValueError("No valid reviews were found to analyze.")

    review_text = "\n".join(
        f'{item["user"]}: {item["review"]}'
        for item in reviews
    )

    # =====================================================
    # STEP 1: GEMINI UNDERSTANDS THE REVIEWS
    # =====================================================

    prompt = f"""
You are an AI UX Research Agent.

Analyze the following user reviews and answer the research question.

USER'S QUESTION:
{user_question}

ACTUAL REVIEWS:
{review_text}

Your first job is to understand the meaning of every review.

Identify ALL genuine UX problems described by the reviews.
Do not invent problems that are not supported by the reviews.

For each user, identify ONE primary UX problem.

If a review describes multiple issues, consider:
1. Which issue has the greatest impact on the user's ability to complete their task.
2. Which issue the user expresses most strongly.

Use a combination of task impact and strength of complaint to select
the primary UX problem.

Do not count the same user under multiple primary UX problems.

Closely related primary problems across different users should be
grouped under one clear broader UX theme.

Do not use a predefined list of UX problem names.
Create themes dynamically from the evidence in the uploaded reviews.

Even if only one user reports a unique genuine UX problem,
keep that problem visible instead of hiding or merging it into
an unrelated theme.

Then assess EVERY major UX problem using:

1. Severity: 1-10
   - Base this only on evidence from the reviews.
   - Measure how strongly the problem affects the user's ability
     to complete their task.

   Scoring guide:
   1-3 = Minor friction.
         The user can still complete the task with little difficulty.

   4-6 = Moderate friction.
         The problem causes confusion, delay, or extra effort,
         but the task can still be completed.

   7-8 = Major friction.
         The problem seriously disrupts the task or creates
         a significant negative experience.

   9-10 = Critical failure.
          The user cannot complete the task, loses money,
          receives an incorrect outcome, or experiences another
          severe failure supported by the review evidence.

          2. Business Impact: 1-10
   - Base this only on evidence from the reviews and the user's journey.
   - Measure the potential impact of the UX problem on important
     business outcomes.

   Consider evidence related to:
   - purchase or order completion
   - cancellations
   - refunds
   - payment failures
   - repeat usage
   - customer trust
   - support burden

   Scoring guide:
   1-3 = Low business impact.
         Mostly minor inconvenience with little evidence of impact
         on important business outcomes.

   4-6 = Moderate business impact.
         May create additional support needs, reduce satisfaction,
         or introduce friction that could affect continued usage.

   7-8 = High business impact.
         Directly affects important outcomes such as completed orders,
         cancellations, refunds, payments, or customer trust.

   9-10 = Critical business impact.
          Strong evidence of lost transactions, failed payments,
          significant financial consequences, or serious damage
          to customer trust.

   Do not assume business impact that is not supported by the reviews.

IMPORTANT:
- Do not calculate affected-user counts yourself.
- Do not calculate percentages yourself.
- Do not calculate priority scores yourself.
- Python will perform those calculations.
- Do not invent users, reviews, numbers, or quotes.

You MUST call the process_ux_analysis tool once after completing
all classifications and assessments.

The tool will calculate:
- affected users
- percentage
- frequency score
- priority score
- priority level
"""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]

    print("🧠 Gemini is understanding the user reviews...")

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[analysis_tool]
            )
        )
    except Exception as e:
        if "503" in str(e) or "UNAVAILABLE" in str(e):
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[analysis_tool]
                )
            )
        else:
            raise

    # =====================================================
    # STEP 2: PYTHON CALCULATES
    # =====================================================

    if not response.function_calls:
        raise RuntimeError(
            "Gemini did not call the UX analysis tool."
        )

    contents.append(response.candidates[0].content)

    tool_parts = []

    for function_call in response.function_calls:

        if function_call.name != "process_ux_analysis":
            continue

        classifications = function_call.args["classifications"]
        assessments = function_call.args["assessments"]

        print("🧮 Python is calculating UX metrics...")
        print(f"👥 Classifications received: {len(classifications)}")

        analysis = process_ux_analysis(
            classifications,
            assessments
        )

        for item in analysis["problems"]:
            print(
                f"🎯 {item['problem']}: "
                f"{item['percentage']}% → "
                f"{item['priority_score']}/30 → "
                f"{item['priority']}"
            )

        tool_parts.append(
            types.Part.from_function_response(
                name="process_ux_analysis",
                response={"result": analysis}
            )
        )

    if not tool_parts:
        raise RuntimeError(
            "Gemini did not provide valid UX analysis data."
        )

    contents.append(
        types.Content(
            role="user",
            parts=tool_parts
        )
    )
    # =====================================================
    # STEP 3: GEMINI EXPLAINS THE RESULTS
    # =====================================================

    explanation_prompt = """
Using the Python-calculated UX analysis returned by the tool,
write the final UX research report.

Do NOT change any Python-calculated numbers.
Do NOT recalculate percentages or priority scores.

Explain why each severity and business-impact assessment makes sense
using only evidence from the actual reviews.

Rank all UX problems from highest priority to lowest priority.

For every problem provide:
- affected users
- percentage
- users affected
- evidence from reviews
- secondary observations mentioned by affected users, when available
- frequency score
- severity
- business impact
- priority score
- priority level
- why this priority matters
- a specific UX recommendation

Use this format:

===== UX RESEARCH REPORT =====

USER QUESTION:
[question]

TOTAL USERS:
[number]

UX PROBLEMS:

1. [Problem name]

Affected users: [number]
Percentage: [percentage]%

Users:
- User [number]

Evidence:
- User [number]: "[short quote]"

Secondary Observations:
- User [number]: [secondary issue]
- If none exist, write "None"

Frequency Score: [0-10]
Severity: [1-10]
Business Impact: [1-10]
Priority Score: [score]/30
Priority: [CRITICAL / HIGH / MEDIUM / LOW]

Why this priority:
[Explanation]

UX Recommendation:
[Specific recommendation]

Repeat for ALL identified problems.

===== TOP UX PRIORITY =====

Problem: [highest priority problem]
Affected users: [number]
Percentage: [percentage]%
Why it matters: [short explanation]

===== END REPORT =====
"""

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=explanation_prompt)]
        )
    )

    print("💡 Gemini is explaining the calculated results...")

    final_response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=contents
    )

    final_report = final_response.text

    save_report(final_report)

    print("💾 Report saved successfully.")

    return final_report


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    result = run_ux_research(
        "Analyze the UX problems in these reviews"
    )

    print("\n===== UX RESEARCH AGENT =====\n")
    print(result)
