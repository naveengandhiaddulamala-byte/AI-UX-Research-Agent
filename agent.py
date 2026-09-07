import os
from google import genai
from google.genai import types


# ---------- TOOL 1: READ REVIEWS ----------
def read_reviews():
    """Read the UX research reviews from reviews.txt."""
    with open("reviews.txt", "r", encoding="utf-8") as file:
        return file.read()
# ---------- TOOL 2: CALCULATE PERCENTAGE ----------
def calculate_percentage(part, total):
    """Calculate the percentage of users affected."""
    if total == 0:
        return 0

    return (part / total) * 100


# ---------- TOOL 3: SAVE REPORT ----------
def save_report(report):
    """Save the final UX research report to report.txt."""
    with open("report.txt", "w", encoding="utf-8") as file:
        file.write(report)

    return "Report successfully saved to report.txt"


# ---------- GEMINI ----------
api_key = os.environ.get("GEMINI_API_KEY")
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

        # TOOL 2: CALCULATE PERCENTAGE
        types.FunctionDeclaration(
            name="calculate_percentage",
            description="Calculates what percentage one number represents out of another.",
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

        # TOOL 3: SAVE REPORT
        types.FunctionDeclaration(
            name="save_report",
            description="Saves the final UX research report into report.txt.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "report": types.Schema(
                        type="STRING",
                        description="The complete final UX research report to save."
                    )
                },
                required=["report"]
            )
        )
    ]
)
user_question = input("What would you like the UX agent to analyze? ")

prompt = f"""
You are an AI UX Research Agent.

Your job is to analyze grocery app user reviews
and answer the user's research question.

USER'S QUESTION:
{user_question}

Follow this workflow:

1. Use read_reviews to obtain the reviews.
2. Determine the total number of users/reviews.
3. Identify every major UX problem found in the reviews.
4. For each problem, identify the specific users affected.
5. Count the affected users for each problem.
6. Use only evidence from the actual reviews.
7. Rank the problems by the number of affected users.
8. Create a clear UX research report.

Format the final answer like this:

===== UX RESEARCH REPORT =====

USER QUESTION:
[Repeat the user's question]

TOTAL USERS:
[Total number of users/reviews analyzed]

UX PROBLEMS:

1. [Problem name]
   Affected users: [number]
   Users: [user numbers]

   Evidence:
   - User [number]: "[short quote]"
   - User [number]: "[short quote]"

   Priority: [HIGH / MEDIUM / LOW]

2. [Problem name]
   Affected users: [number]
   Users: [user numbers]

   Evidence:
   - User [number]: "[short quote]"
   - User [number]: "[short quote]"

   Priority: [HIGH / MEDIUM / LOW]

[Continue for all major problems]

===== TOP UX PRIORITY =====

Problem:
[Most important problem]

Affected users:
[number]

Why it matters:
[Short explanation]

===== UX RECOMMENDATION =====

[Specific design recommendation]

IMPORTANT:
- Use only information from the reviews.
- Do not invent users, numbers, or quotes.
- Every affected-user count must be traceable to an actual review.
- A user can belong to more than one problem if their review clearly describes multiple problems.
- Do not calculate percentages yourself.
- Do not use the calculate_percentage tool for now.
- Give the final answer after completing the analysis.
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

    # Add Gemini's response to the conversation
    contents.append(response.candidates[0].content)

    # If Gemini doesn't request a tool, we're finished
    if not response.function_calls:
        break

    # Handle every requested tool
    tool_parts = []

    for function_call in response.function_calls:
        if function_call.name == "read_reviews":
            print("📄 Agent is reading the reviews...")
            result = read_reviews()
            tool_parts.append(
                types.Part.from_function_response(
                    name="read_reviews",
                    response={"result": result}
                )
            )

        elif function_call.name == "calculate_percentage":
            part = function_call.args["part"]
            total = function_call.args["total"]
            print(f"🧮 Agent is calculating: {part} out of {total}")
            result = calculate_percentage(part, total)
            print(f"📊 Result: {result}%")
            tool_parts.append(
                types.Part.from_function_response(
                    name="calculate_percentage",
                    response={"result": result}
                )
            )

        elif function_call.name == "save_report":
            report = function_call.args["report"]
            print("💾 Agent is saving the UX research report...")
            result = save_report(report)
            print("✅ Report saved successfully.")
            tool_parts.append(
                types.Part.from_function_response(
                    name="save_report",
                    response={"result": result}
                )
            )

    # Add tool results to the conversation
    contents.append(
        types.Content(
            role="tool",
            parts=tool_parts
        )
    )


# ---------- FINAL RESULT ----------
print("\n===== UX RESEARCH AGENT =====\n")
print(response.text)