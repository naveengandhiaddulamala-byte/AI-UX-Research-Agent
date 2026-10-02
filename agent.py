import os

from dotenv import load_dotenv

from google import genai

from google.genai import types





# =========================================================

# LOAD ENVIRONMENT VARIABLES

# =========================================================



load_dotenv()



api_key = os.environ.get("GEMINI_API_KEY")



# Streamlit Cloud fallback

if not api_key:

    try:

        import streamlit as st

        api_key = st.secrets.get("GEMINI_API_KEY")

    except Exception:

        api_key = None



if not api_key:

    raise ValueError(

        "GEMINI_API_KEY was not found."

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



def parse_reviews(reviews_text=None):

    """Parse reviews from either CSV or User: Review text format."""



    import csv

    import io



    reviews = []



    if reviews_text is not None:

        text = reviews_text

    else:

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





def process_ux_analysis(classifications, assessments, total_users=None):

    """

    Perform deterministic UX calculations in Python.



    Gemini supplies the understanding/classification and

    evidence-based severity/business-impact assessments.

    Python performs counting, percentages, frequency scores,

    and priority calculations.

    """



    if total_users is None:

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

        frequency_score = max(

    1,

    min(

        10,

        int(round(percentage / 10))

    )

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



    # =========================================================

# RESEARCH PROJECTS: AI WORKSPACE SUGGESTION

# =========================================================



def suggest_project_workspace(
    project_name,
    project_type,
    research_goal,
    description,
    current_sections
):
    """
    Suggest optional workspace improvements while keeping the researcher
    in control. Suggestions can rename, remove, or add sections.
    """
    import json

    prompt = """
You are assisting a UX researcher in organizing a research project workspace.

PROJECT CONTEXT

Project Name:
{project_name}

Project Type:
{project_type}

Research Goal:
{research_goal}

Description:
{description}

Current Workspace Sections:
{current_sections}

YOUR TASK

Review ALL current workspace sections, including custom sections created by
the researcher. Suggest changes only when they genuinely improve clarity,
organization, or fit with the stated research goal.

The researcher remains the final decision-maker. Never apply a change yourself.
Do not invent research findings, evidence, participants, metrics, or study results.
Keep section names short and professional. Avoid cosmetic renaming that adds no value.

You may use exactly these actions:
- "rename": improve the name of an existing section.
- "remove": recommend removing an existing section when it is not useful for this project.
- "add": recommend a genuinely missing section.

Trend Analysis should only be recommended when comparing datasets or research
across time is relevant.
Return ONLY valid JSON in this exact structure:

{{
  "suggestions": [
    {{
      "action": "rename",
      "current_section": "Data",
      "suggested_section": "User Feedback",
      "reason": "The current label is too broad for this research context.",
      "context_evidence": "Exact supporting words or phrase from the Research Goal or Description"
    }},
    {{
      "action": "remove",
      "current_section": "Trend Analysis",
      "suggested_section": null,
      "reason": "The current project does not indicate a need for longitudinal comparison.",
      "context_evidence": null
    }},
    {{
      "action": "add",
      "current_section": null,
      "suggested_section": "Usability Testing",
      "reason": "The research goal explicitly mentions usability testing.",
      "context_evidence": "Exact supporting words or phrase from the Research Goal or Description"
    }}
  ]
}}

EVIDENCE RULES:

- For "rename" suggestions that change the meaning of a vague section,
  context_evidence MUST contain an exact phrase copied from the Research Goal
  or Description that supports the new meaning.

- For "add" suggestions, context_evidence MUST contain an exact phrase copied
  from the Research Goal or Description that justifies adding that section.

- Project Type alone is NOT valid context evidence.

- Do not invent or paraphrase context_evidence.

- If there is no exact supporting evidence in the Research Goal or Description,
  do NOT make that semantic rename or addition.

- A simple clarity rename that preserves the existing meaning does not require
  new assumptions, but it should still avoid inventing what the section contains.

- "remove" suggestions may use null for context_evidence because removal can be
  based on the absence of a stated project requirement.

- Never claim a research method, participant type, persona, journey, methodology,
  deliverable, or activity exists unless it is supported by the supplied
  Research Goal or Description.

""".format(
        project_name=project_name,
        project_type=project_type,
        research_goal=research_goal,
        description=description,
        current_sections=current_sections,
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
    except Exception as e:
        if (
            "503" in str(e)
            or "UNAVAILABLE" in str(e)
            or "429" in str(e)
            or "RESOURCE_EXHAUSTED" in str(e)
        ):
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt
            )
        else:
            raise

    response_text = (response.text or "").strip()
    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "suggestions": [],
            "error": "AI returned an invalid workspace suggestion."
        }

    raw_suggestions = result.get("suggestions", [])
    if not isinstance(raw_suggestions, list):
        raw_suggestions = []

    current_set = {str(section).strip() for section in current_sections}

    default_workspace_sections = {
        "Overview",
        "Research Data",
        "UX Findings",
        "Evidence",
        "Recommendations",
        "Trend Analysis"
    }

    validated = []

    project_context = (
        f"{research_goal} {description}"
    ).strip().lower()

    for item in raw_suggestions:
        if not isinstance(item, dict):
            continue

        action = str(item.get("action", "")).strip().lower()
        current = item.get("current_section")
        suggested = item.get("suggested_section")
        reason = str(item.get("reason", "")).strip()
        context_evidence = item.get("context_evidence")

        current = current.strip() if isinstance(current, str) else None
        suggested = suggested.strip() if isinstance(suggested, str) else None

        context_evidence = (
            context_evidence.strip()
            if isinstance(context_evidence, str)
            else None
        )

        # Evidence is valid only when Gemini copied an exact phrase
        # that actually exists in the Research Goal or Description.
        evidence_is_valid = bool(
            context_evidence
            and context_evidence.lower() in project_context
        )

        if action == "rename":
            if (
                current in current_set
                and suggested
                and suggested not in current_set
                and suggested.lower() not in {"none", "remove", "delete"}
                and suggested != current
                and evidence_is_valid
            ):
                validated.append({
                    "action": action,
                    "current_section": current,
                    "suggested_section": suggested,
                    "reason": reason,
                    "context_evidence": context_evidence
                })
        elif action == "remove":
            # AI may recommend removing built-in sections because their
            # intended purpose is known.
            #
            # Researcher-created custom sections are protected.
            # If their meaning is unclear, AI must not assume they are
            # redundant or unnecessary.
            if (
                current in current_set
                and current in default_workspace_sections
            ):
                validated.append({
                    "action": action,
                    "current_section": current,
                    "suggested_section": None,
                    "reason": reason,
                    "context_evidence": None
                })
        elif action == "add":
            if (
                suggested
                and suggested not in current_set
                and suggested.lower() not in {"none", "remove", "delete"}
                and evidence_is_valid
            ):
                validated.append({
                    "action": action,
                    "current_section": None,
                    "suggested_section": suggested,
                    "reason": reason,
                    "context_evidence": context_evidence
                })

    return {"suggestions": validated}


# ==========================================
# UX TREND ANALYSIS

# ==========================================


def match_ux_themes(previous_themes, current_themes):
    """Use AI to identify semantically related UX themes between previous and current research datasets.

    Return structured data for Python trend analysis.
    """
    import json

    prompt = (
        "You are comparing UX research findings from two different datasets.\n\n"
        "PREVIOUS DATASET UX THEMES:\n"
        f"{previous_themes}\n\n"
        "CURRENT DATASET UX THEMES:\n"
        f"{current_themes}\n\n"
        "Determine which themes represent the same underlying UX problem,\n"
        "even when their names are different.\n\n"
        "Rules:\n\n"
        "1. Match themes based on the underlying UX problem,\n"
        "   not just similar wording.\n\n"
        "2. Do not match themes simply because they belong\n"
        "   to the same product area.\n\n"
        "3. Every current theme can match at most one previous theme.\n\n"
        "4. Every previous theme can match at most one current theme.\n\n"
        "5. If a current theme has no meaningful previous equivalent,\n"
        "   classify it as newly observed.\n\n"
        "6. If a previous theme has no meaningful current equivalent,\n"
        "   classify it as not observed in the current dataset.\n\n"
        "7. Do not invent a match when the relationship is weak.\n\n"
        "For matched themes, create a short common UX theme name\n"
        "and briefly explain why they represent the same problem.\n\n"
        "Return ONLY valid JSON.\n\n"
        "Use exactly this structure:\n\n"
        "{\n"
        "    \"matches\": [\n"
        "        {\n"
        "            \"previous_theme\": \"Previous theme name\",\n"
        "            \"current_theme\": \"Current theme name\",\n"
        "            \"common_theme\": \"Common UX theme name\",\n"
        "            \"reason\": \"Short explanation of why they match\"\n"
        "        }\n"
        "    ],\n"
        "    \"newly_observed\": [\n"
        "        \"Current theme with no previous match\"\n"
        "    ],\n"
        "    \"not_observed_current\": [\n"
        "        \"Previous theme with no current match\"\n"
        "    ]\n"
        "}\n\n"
        "Do not include markdown.\n"
        "Do not include *```json.*\n"
        "Do not include any text before or after the JSON.\n"
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
    except Exception as e:
        if any(code in str(e) for code in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")):
            print("Primary Gemini model unavailable or quota limited. Trying fallback model...")
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
            )
        else:
            raise

    response_text = (getattr(response, "text", "") or "").strip()
    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

    try:
        parsed = json.loads(response_text)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("Result is not a JSON object.", response_text, 0)
        return parsed
    except json.JSONDecodeError:
        return {
            "matches": [],
            "newly_observed": [],
            "not_observed_current": [],
            "error": "AI returned an invalid UX theme match."
        }


def validate_v5_classifications(classifications):

    """Validate the one-primary-problem-per-user rule."""

    users = [item["user"] for item in classifications]
    unique_users = set(users)
    duplicate_users = sorted({user for user in unique_users if users.count(user) > 1})

    return {
        "total_classifications": len(classifications),
        "unique_users": len(unique_users),
        "duplicate_users": duplicate_users,
        "is_valid": (
            len(classifications) == 30
            and len(unique_users) == 30
            and len(duplicate_users) == 0
        ),
    }



def build_ux_trend_comparison(previous_analysis, current_analysis, theme_matches):
    """Connect AI theme matching with deterministic Python percentage comparison."""

    previous_map = {
        item["problem"]: item
        for item in previous_analysis.get("problems", [])
    }

    current_map = {
        item["problem"]: item
        for item in current_analysis.get("problems", [])
    }

    comparison_items = []

    # Themes found in both datasets
    for match in theme_matches.get("matches", []):
        previous_theme = match.get("previous_theme")
        current_theme = match.get("current_theme")

        previous_item = previous_map.get(previous_theme)
        current_item = current_map.get(current_theme)

        if not previous_item or not current_item:
            continue

        comparison_items.append({
            "problem": match.get("common_theme"),
            "previous_percentage": previous_item.get("percentage", 0),
            "current_percentage": current_item.get("percentage", 0),
            "previous_users": previous_item.get("affected_users", 0),
            "current_users": current_item.get("affected_users", 0),
            "match_reason": match.get("reason", "Matched by AI theme comparison.")
        })

    # Themes appearing only in current research
    for theme in theme_matches.get("newly_observed", []):
        current_item = current_map.get(theme)
        if not current_item:
            continue

        comparison_items.append({
            "problem": theme,
            "previous_percentage": 0,
            "current_percentage": current_item.get("percentage", 0),
            "previous_users": 0,
            "current_users": current_item.get("affected_users", 0),
            "match_reason": "No equivalent theme was found in the previous dataset."
        })

    # Themes appearing only in previous research
    for theme in theme_matches.get("not_observed_current", []):
        previous_item = previous_map.get(theme)
        if not previous_item:
            continue

        comparison_items.append({
            "problem": theme,
            "previous_percentage": previous_item.get("percentage", 0),
            "current_percentage": 0,
            "previous_users": previous_item.get("affected_users", 0),
            "current_users": 0,
            "match_reason": "No equivalent theme was found in the current dataset."
        })

    trends = []
    for item in comparison_items:
        previous_percentage = item["previous_percentage"]
        current_percentage = item["current_percentage"]
        change = round(current_percentage - previous_percentage, 2)

        if previous_percentage == 0 and current_percentage > 0:
            trend = "NEWLY OBSERVED"
        elif previous_percentage > 0 and current_percentage == 0:
            trend = "NOT OBSERVED IN CURRENT DATASET"
        elif change > 0:
            trend = "INCREASING"
        elif change < 0:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        trends.append({
            "problem": item["problem"],
            "previous_percentage": previous_percentage,
            "current_percentage": current_percentage,
            "change": change,
            "trend": trend,
            "previous_users": item["previous_users"],
            "current_users": item["current_users"],
            "match_reason": item["match_reason"],
        })

    return trends





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





def run_ux_research(

    user_question,

    reviews_text=None,

    return_analysis=False

):

    """Run the optimized V4 UX research workflow."""



    # Use uploaded/sample reviews directly when supplied.

    # Otherwise fall back to the existing reviews.txt file.

    if reviews_text is not None:

        reviews = parse_reviews(reviews_text)

    else:

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

        if (

            "503" in str(e)

            or "UNAVAILABLE" in str(e)

            or "429" in str(e)

            or "RESOURCE_EXHAUSTED" in str(e)

        ):

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

            assessments,

            total_users=len(reviews)

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

    if return_analysis:

        return analysis

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



    if return_analysis:

        return analysis



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
