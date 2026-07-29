import json
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from knowledge_base.services.vector_store import search_similar_projects

# ---- Predefined base pricing rules (per feature complexity) ----
FEATURE_RATE_CARD = {
    "simple": 800,      # e.g. static pages, basic forms
    "moderate": 1800,    # e.g. auth, catalog, dashboards
    "complex": 3500,     # e.g. payment integration, real-time tracking, ERP modules
}

BASE_PROJECT_COST = 2000  # covers planning, PM overhead, deployment setup
BASE_TIMELINE_WEEKS = 1   # baseline setup/planning week

COMPLEXITY_PROMPT = """You are a technical project estimator. Given this list of required features/requirements, classify EACH feature into one of these complexity levels: "simple", "moderate", or "complex".

FEATURES:
{features}

Return ONLY a valid JSON object (no markdown, no extra text) mapping each feature (exact text as given) to its complexity level. Example format:
{{
  "User authentication": "moderate",
  "Payment gateway": "complex"
}}"""


def _extract_text_from_response(response) -> str:
    content = response.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts).strip()
    raise ValueError(f"Unexpected response content type: {type(content)}")


def _clean_json_output(raw_output: str) -> str:
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`")
        if raw_output.lower().startswith("json"):
            raw_output = raw_output[4:].strip()
    return raw_output


def _classify_feature_complexity(features: list) -> dict:
    """
    Uses Gemini to classify each feature as simple/moderate/complex.
    Falls back to 'moderate' for any feature it fails to classify.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )
    prompt = ChatPromptTemplate.from_template(COMPLEXITY_PROMPT)
    chain = prompt | llm

    response = chain.invoke({"features": json.dumps(features)})
    raw_output = _clean_json_output(_extract_text_from_response(response))

    try:
        classification = json.loads(raw_output)
    except json.JSONDecodeError:
        classification = {}

    # Ensure every feature has a value, default to 'moderate'
    result = {}
    for f in features:
        result[f] = classification.get(f, "moderate")
    return result


def _get_historical_reference(rfp_requirements: dict):
    """
    Pulls average cost/duration from similar historical projects, if available.
    """
    query_text = json.dumps(rfp_requirements)
    try:
        similar = search_similar_projects(query_text, top_k=3)
    except FileNotFoundError:
        return None, None

    costs = []
    durations = []
    for p in similar:
        meta = p.get("metadata", {})
        if meta.get("actual_cost"):
            try:
                costs.append(float(meta["actual_cost"]))
            except (ValueError, TypeError):
                pass
        if meta.get("actual_duration_weeks"):
            durations.append(meta["actual_duration_weeks"])

    avg_cost = sum(costs) / len(costs) if costs else None
    avg_duration = sum(durations) / len(durations) if durations else None
    return avg_cost, avg_duration


def estimate_cost_and_timeline(rfp_requirements: dict) -> dict:
    """
    Returns a dict:
    {
        "estimated_cost": float,
        "cost_breakdown": {...},
        "estimated_timeline_weeks": int,
        "timeline_breakdown": {...}
    }
    """
    features = rfp_requirements.get("required_features", []) or []

    if not features:
        features = ["General project setup"]

    complexity_map = _classify_feature_complexity(features)

    # ---- Cost calculation ----
    cost_breakdown = {"base_setup_and_planning": BASE_PROJECT_COST}
    total_cost = BASE_PROJECT_COST

    for feature, level in complexity_map.items():
        rate = FEATURE_RATE_CARD.get(level, FEATURE_RATE_CARD["moderate"])
        cost_breakdown[feature] = rate
        total_cost += rate

    # ---- Timeline calculation ----
    # Rough rule: simple = 0.5 week, moderate = 1 week, complex = 2 weeks of dev effort
    TIMELINE_WEIGHTS = {"simple": 0.5, "moderate": 1, "complex": 2}
    timeline_breakdown = {"planning_and_design": BASE_TIMELINE_WEEKS}
    total_weeks = BASE_TIMELINE_WEEKS

    for feature, level in complexity_map.items():
        weeks = TIMELINE_WEIGHTS.get(level, 1)
        timeline_breakdown[feature] = weeks
        total_weeks += weeks

    # Add fixed QA + deployment buffer
    timeline_breakdown["testing_and_deployment"] = 1
    total_weeks += 1

    # ---- Blend with historical data if available ----
    avg_hist_cost, avg_hist_duration = _get_historical_reference(rfp_requirements)

    if avg_hist_cost:
        # Weighted average: 60% rule-based calc, 40% historical average
        total_cost = round((total_cost * 0.6) + (avg_hist_cost * 0.4), 2)

    if avg_hist_duration:
        total_weeks = round((total_weeks * 0.6) + (avg_hist_duration * 0.4))

    return {
        "estimated_cost": round(total_cost, 2),
        "cost_breakdown": {k: round(v, 2) if isinstance(v, (int, float)) else v for k, v in cost_breakdown.items()},
        "estimated_timeline_weeks": round(total_weeks),
        "timeline_breakdown": timeline_breakdown,
    }