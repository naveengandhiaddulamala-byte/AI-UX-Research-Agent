import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


# ---------- LOAD ENVIRONMENT VARIABLES ----------
load_dotenv()


# ---------- TOOL 1: READ REVIEWS ----------
def read_reviews():
    """Read the UX research reviews from reviews.txt."""

    with open("reviews.txt", "r", encoding="utf-8") as file:
        return file.read()


# ---------- TOOL 2: PARSE REVIEWS ----------
def parse_reviews():
    """Read reviews.txt and separate each review into an individual user record."""

    reviews = []

    with open("reviews.txt", "r", encoding="utf-8") as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            # Split only at the first colon
            user, review = line.split(":", 1)

            reviews.append({
                "user": user.strip(),
                "review": review.strip()
            })

    return reviews


# ---------- TOOL 3: COUNT UX PROBLEMS ----------
def count_ux_problems(classifications):
    """Count how many users are affected by each UX problem."""

    problem_counts = {}

    for item in classifications:

        problem = item["problem"]

        if problem not in problem_counts:
            problem_counts[problem] = 0

        problem_counts[problem] += 1

    return problem_counts


# ---------- TOOL 4: CALCULATE PERCENTAGE ----------
def calculate_percentage(part, total):
    """Calculate the percentage of users affected."""

    if total == 0:
        return 0

    return (part / total) * 100


# ---------- TOOL 5: SAVE REPORT ----------
def save_report(report):
    """Save the final UX research report to report.txt."""

    with open("report.txt", "w", encoding="utf-8") as file:
        file.write(report)

    return "Report successfully saved to report.txt"


# ---------- GEMINI ----------
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

client = genai.Client(api_key=api_key)


# ---------- TOOL DEFINITIONS ----------
tools = types.Tool(
    function_declarations=[

        # TOOL 1: READ REVIEWS
        types.FunctionDeclaration(
            name="read_reviews",
            description="Reads the grocery app user reviews from reviews.txt.",
            parameters=types.Schema(
                type="OBJECT",
                properties={}
            )
        ),

        # TOOL 2: PARSE REVIEWS
        types.FunctionDeclaration(
            name="parse_reviews",
            description=(
                "Reads reviews.txt and separates the reviews into "
                "individual users and review text."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={}
            )
        ),

        # TOOL 3: COUNT UX PROBLEMS
        types.FunctionDeclaration(
            name="count_ux_problems",
            description=(
                "Counts how many users are affected by each UX problem "
                "using the AI's classifications."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "classifications": types.Schema(
                        type="ARRAY",
                        description=(
                            "List of users and the UX problem identified "
                            "in each review."
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
                                    description="UX problem identified in the review."
                                )
                            },
                            required=["user", "problem"]
                        )
                    )
                },
                required=["classifications"]
            )
        ),

        # TOOL 4: CALCULATE PERCENTAGE
        types.FunctionDeclaration(
            name="calculate_percentage",
            description=(
                "Calculates what percentage one number represents "
                "out of another."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "part": types.Schema(
                        type="NUMBER",
                        description="Number of users affected by an issue."
                    ),
                    "total": types.Schema(
                        type="NUMBER",
                        description="Total number of users."
                    )
                },
                required=["part", "total"]
            )
        ),

        # TOOL 5: SAVE REPORT
        types.FunctionDeclaration(
            name="save_report",
            description="Saves the final UX research report into report.txt.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "report": types.Schema(
                        type="STRING",
                        description="The complete final UX research report."
                    )
                },
                required=["report"]
            )
        )
    ]
)


# ---------- USER QUESTION ----------
user_question = input(
    "What would you like the UX agent to analyze? "
)


# ---------- AGENT INSTRUCTIONS ----------
prompt = f"""
You are an AI UX Research Agent.

Your job is to analyze grocery app user reviews
and answer the user's research question.

USER'S QUESTION:
{user_question}


FOLLOW THIS WORKFLOW:

1. Use the read_reviews tool to obtain the raw reviews.

2. Use the parse_reviews tool to separate the reviews
   into individual users.

3. Analyze every individual review.

4. Identify the UX problem described by each user.

5. Create classifications using this structure:

   [
       {{
           "user": "User 1",
           "problem": "Product Selection"
       }},
       {{
           "user": "User 2",
           "problem": "Pricing"
       }}
   ]

6. Use the count_ux_problems tool with these classifications.

7. Determine the total number of users/reviews.

8. For each major UX problem, use the
   calculate_percentage tool to calculate:

   affected users / total users * 100

9. Rank UX problems by the number of affected users.

10. Use only evidence from the actual reviews.

11. Do not invent users, numbers, problems, or quotes.

12. A user can belong to more than one UX problem
    if their review clearly describes multiple problems.

13. After completing the analysis, create a clear UX research report.

14. Use the save_report tool to save the final report
    into report.txt.


FINAL REPORT FORMAT:

===== UX RESEARCH REPORT =====

USER QUESTION:
[Repeat the user's question]

TOTAL USERS:
[Total number of users/reviews analyzed]


UX PROBLEMS:

1. [Problem name]

   Affected users: [number]
   Percentage: [percentage]%

   Users:
   - User [number]
   - User [number]

   Evidence:
   - User [number]: "[short quote]"
   - User [number]: "[short quote]"

   Priority: [HIGH / MEDIUM / LOW]


2. [Problem name]

   Affected users: [number]
   Percentage: [percentage]%

   Users:
   - User [number]
   - User [number]

   Evidence:
   - User [number]: "[short quote]"
   - User [number]: "[short quote]"

   Priority: [HIGH / MEDIUM / LOW]


===== TOP UX PRIORITY =====

Problem:
[Most important problem]

Affected users:
[number]

Percentage:
[percentage]%

Why it matters:
[Short explanation based on the reviews]


===== UX RECOMMENDATION =====

[Specific design recommendation based only on the research]


IMPORTANT:

- Use only information from the actual reviews.
- Do not invent users, numbers, or quotes.
- Every affected-user count must be traceable to an actual review.
- Every percentage must come from the calculate_percentage tool.
- Do not calculate percentages yourself.
- Use Python tools for counting and numerical calculations.
- Use Gemini to understand and classify the meaning of the reviews.
"""


# ---------- CONVERSATION HISTORY ----------
contents = [
    types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=prompt)
        ]
    )
]


# ---------- AGENT LOOP ----------
while True:

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            tools=[tools]
        )
    )

    # Add Gemini's response to conversation history
    contents.append(response.candidates[0].content)

    # If Gemini doesn't request a tool, analysis is finished
    if not response.function_calls:
        break

    # Store all tool responses
    tool_parts = []

    # Handle every requested tool
    for function_call in response.function_calls:

        # ---------- READ REVIEWS ----------
        if function_call.name == "read_reviews":

            print("📄 Agent is reading the reviews...")

            result = read_reviews()

            tool_parts.append(
                types.Part.from_function_response(
                    name="read_reviews",
                    response={
                        "result": result
                    }
                )
            )


        # ---------- PARSE REVIEWS ----------
        elif function_call.name == "parse_reviews":

            print("🔎 Agent is parsing individual reviews...")

            result = parse_reviews()

            print(f"👥 Parsed {len(result)} individual reviews.")

            tool_parts.append(
                types.Part.from_function_response(
                    name="parse_reviews",
                    response={
                        "result": result
                    }
                )
            )


        # ---------- COUNT UX PROBLEMS ----------
        elif function_call.name == "count_ux_problems":

            print("📊 Agent is counting users affected by each UX problem...")

            classifications = function_call.args["classifications"]

            result = count_ux_problems(classifications)

            print(f"📊 UX problem counts: {result}")

            tool_parts.append(
                types.Part.from_function_response(
                    name="count_ux_problems",
                    response={
                        "result": result
                    }
                )
            )


        # ---------- CALCULATE PERCENTAGE ----------
        elif function_call.name == "calculate_percentage":

            part = function_call.args["part"]
            total = function_call.args["total"]

            print(
                f"🧮 Agent is calculating: "
                f"{part} out of {total}"
            )

            result = calculate_percentage(part, total)

            print(f"📊 Result: {result}%")

            tool_parts.append(
                types.Part.from_function_response(
                    name="calculate_percentage",
                    response={
                        "result": result
                    }
                )
            )


        # ---------- SAVE REPORT ----------
        elif function_call.name == "save_report":

            report = function_call.args["report"]

            print("💾 Agent is saving the UX research report...")

            result = save_report(report)

            print("✅ Report saved successfully.")

            tool_parts.append(
                types.Part.from_function_response(
                    name="save_report",
                    response={
                        "result": result
                    }
                )
            )


    # Add tool results back to Gemini
    contents.append(
        types.Content(
            role="tool",
            parts=tool_parts
        )
    )


# ---------- FINAL RESULT ----------
print("\n===== UX RESEARCH AGENT =====\n")
print(response.text)