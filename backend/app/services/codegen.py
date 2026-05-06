import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def generate_suggestions(profile: dict) -> list[dict]:
    """
    Step 1 — human readable suggestions explaining WHAT to do and WHY.
    This is the agentic reasoning step.
    """
    actual_columns = set(profile.get("columns", []))

    prompt = f"""
You are an expert data analyst reviewing a dataset profile.
Provide specific, actionable preprocessing suggestions.

DATASET PROFILE:
- Columns: {list(actual_columns)}
- Missing values: {json.dumps(profile.get("missing", {}))}
- High skew columns: {json.dumps(profile.get("skewness", {}))}
- Outlier columns: {json.dumps(profile.get("outliers", {}))}
- Duplicates: {profile.get("duplicates", 0)}
- Data types: {json.dumps(profile.get("dtypes", {}))}

For each issue found, provide a suggestion in this exact JSON format:
[
  {{
    "issue": "what the problem is",
    "column": "exact column name or 'all'",
    "action": "exactly what to do",
    "reason": "why this specific action",
    "priority": "high/medium/low"
  }}
]

RULES:
- Only reference columns from this list: {list(actual_columns)}
- Be specific — say 'apply np.log1p()' not just 'handle skew'
- Order by priority (high first)
- Return ONLY the JSON array, nothing else
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # extract JSON array
    json_match = re.search(r"\[.*\]", raw, re.DOTALL)
    if json_match:
        try:
            suggestions = json.loads(json_match.group())
            # hallucination guard on suggestions too
            actual_columns_list = list(actual_columns)
            for s in suggestions:
                if s.get("column") != "all" and s.get("column") not in actual_columns:
                    s["warning"] = f"Column '{s['column']}' not found in dataset"
            return suggestions
        except json.JSONDecodeError:
            return [{"error": "Could not parse suggestions", "raw": raw}]
    return []


def generate_preprocessing_code(profile: dict, suggestions: list[dict]) -> dict:
    """
    Step 2 — generate actual pandas code BASED ON the suggestions.
    Grounded on what was already reasoned in step 1.
    """
    actual_columns = set(profile.get("columns", []))

    # filter out any suggestions with warnings before sending to codegen
    clean_suggestions = [s for s in suggestions if "warning" not in s]

    prompt = f"""
You are a Python data preprocessing expert.
Generate clean, runnable pandas code based on these approved suggestions:

SUGGESTIONS TO IMPLEMENT:
{json.dumps(clean_suggestions, indent=2)}

AVAILABLE COLUMNS: {list(actual_columns)}

STRICT RULES:
1. Only use columns from: {list(actual_columns)}
2. Assume dataframe is called `df`
3. Use only pandas and numpy
4. Add a comment above each block explaining which suggestion it implements
5. Handle operations in order: duplicates → missing → outliers → skew → types
6. Return ONLY a python code block
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    code_match = re.search(r"```python\n(.*?)```", raw, re.DOTALL)
    code = code_match.group(1).strip() if code_match else raw

    # hallucination guard — scan all column references in generated code
    flagged = []
    for col in re.findall(r"\[['\"](.*?)['\"]\]", code):
        if col not in actual_columns:
            flagged.append(col)

    return {
        "code": code,
        "hallucination_check": {
            "passed": len(flagged) == 0,
            "invented_columns": list(set(flagged))
        }
    }