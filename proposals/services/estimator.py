import json
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from knowledge_base.services.vector_store import search_similar_projects

BASE_PROJECT_COST = 1500   # planning/PM overhead, kept minimal & fixed
BASE_TIMELINE_WEEKS = 1

COST_ESTIMATION_PROMPT = """You are a senior technical project estimator at a software development agency. 
Given the full project context below, estimate a REALISTIC cost (in USD) and timeline (in weeks) for EACH required feature — considering the project type, its overall scale, and industry-standard software development rates.

PROJECT TYPE: {project_type}
PROJECT SUMMARY: {summary}
CLIENT-MENTIONED BUDGET (for reference/sanity-check only): {budget_range}
CLIENT-MENTIONED TIMELINE (for reference only): {timeline}

REQUIRED FEATURES:
{features}

Guidelines:
- Estimate each feature's cost based on ACTUAL implementation effort for THIS SPECIFIC project type, not a generic flat rate.
- A "payment gateway" for a simple e-commerce site costs less than a "payment gateway" with multi-currency, subscriptions, and fraud detection for an enterprise platform — infer the right scope from the project summary.
- Larger/more complex overall projects (e.g. ERP, enterprise systems) should have proportionally higher per-feature costs than small websites or MVPs.
- Costs should be in whole USD dollars, timeline in weeks (can be fractional, e.g. 1.5).

Return ONLY a valid JSON object (no markdown, no extra text) in this exact format:
{{
  "features": [
    {{"name": "exact feature name as given", "cost_usd": 1234, "weeks": 1.5, "reasoning": "one short phrase why"}}
  ]
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


def _get_per_feature_estimates(rfp_requirements: dict) -> list:
    """
    Asks Gemini to estimate cost/timeline per feature, grounded in the
    specific project's type and scale — not a flat generic rate.
    """
    features = rfp_requirements.get("required_features", []) or ["General project setup"]

    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2,
    )
    prompt = ChatPromptTemplate.from_template(COST_ESTIMATION_PROMPT)
    chain = prompt | llm

    response = chain.invoke({
        "project_type": rfp_requirements.get("project_type", "Software Project"),
        "summary": rfp_requirements.get("summary", ""),
        "budget_range": rfp_requirements.get("budget_range", "Not specified"),
        "timeline": rfp_requirements.get("timeline", "Not specified"),
        "features": json.dumps(features),
    })

    raw_output = _clean_json_output(_extract_text_from_response(response))

    try:
        parsed = json.loads(raw_output)
        return parsed.get("features", [])
    except json.JSONDecodeError:
        # Fallback: flat moderate estimate per feature if AI output is malformed
        return [{"name": f, "cost_usd": 1800, "weeks": 1, "reasoning": "fallback estimate"} for f in features]


def _get_historical_reference(rfp_requirements: dict):
    """
    Pulls average cost/duration from similar historical projects, if available.
    """
    query_text = json.dumps(rfp_requirements)
    try:
        similar = search_similar_projects(query_text, top_k=3)
    except FileNotFoundError:
        return None, None

    costs, durations = [], []
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
    Returns project-specific cost & timeline estimates, grounded in:
    1. AI's per-feature estimate based on THIS project's type/scale
    2. Blended with historical actuals from similar past projects
    """
    feature_estimates = _get_per_feature_estimates(rfp_requirements)

    cost_breakdown = {"base_setup_and_planning": BASE_PROJECT_COST}
    timeline_breakdown = {"planning_and_design": BASE_TIMELINE_WEEKS}

    total_cost = BASE_PROJECT_COST
    total_weeks = BASE_TIMELINE_WEEKS

    for item in feature_estimates:
        name = item.get("name", "Feature")
        cost = float(item.get("cost_usd", 1800))
        weeks = float(item.get("weeks", 1))

        cost_breakdown[name] = round(cost, 2)
        timeline_breakdown[name] = weeks

        total_cost += cost
        total_weeks += weeks

    timeline_breakdown["testing_and_deployment"] = 1
    total_weeks += 1

    # ---- Blend with historical data if available ----
    avg_hist_cost, avg_hist_duration = _get_historical_reference(rfp_requirements)

    if avg_hist_cost:
        total_cost = round((total_cost * 0.65) + (avg_hist_cost * 0.35), 2)

    if avg_hist_duration:
        total_weeks = round((total_weeks * 0.65) + (avg_hist_duration * 0.35))

    return {
        "estimated_cost": round(total_cost, 2),
        "cost_breakdown": cost_breakdown,
        "estimated_timeline_weeks": round(total_weeks),
        "timeline_breakdown": timeline_breakdown,
    }