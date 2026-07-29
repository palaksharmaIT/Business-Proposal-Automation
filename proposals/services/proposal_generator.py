import json
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from knowledge_base.services.vector_store import search_similar_projects

PROPOSAL_PROMPT = """You are a senior business proposal writer at a software development company.
Using the RFP requirements and similar past projects below, generate a complete, professional business proposal.

RFP REQUIREMENTS (structured):
{rfp_requirements}

SIMILAR PAST PROJECTS (for reference — use these to inform realistic scope, tech stack, and tone, but do not copy verbatim):
{similar_projects}

Generate a proposal and return ONLY a valid JSON object (no markdown, no code fences, no extra text) with exactly these keys:

{{
  "executive_summary": "2-4 paragraph executive summary introducing the company's understanding of the client's needs and proposed solution",
  "scope_of_work": "detailed scope of work covering what will be built, in clear paragraphs or a description of phases",
  "technology_stack": "recommended technology stack with brief justification, based on the RFP requirements and similar past projects",
  "deliverables": "bullet-style list (as a single string with line breaks) of concrete deliverables the client will receive",
  "terms_and_conditions": "standard professional terms and conditions covering payment milestones, revisions, IP ownership, and support period"
}}

Return ONLY the JSON object. No explanations, no markdown formatting."""


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


def generate_proposal_content(rfp_requirements: dict, top_k: int = 3) -> dict:
    """
    Given structured RFP requirements, retrieves similar past projects from FAISS
    and uses Gemini to generate full proposal content.

    Returns a dict with:
      - proposal sections (executive_summary, scope_of_work, etc.)
      - referenced_project_ids (list of HistoricalProject ids used as context)
    """
    # Build a query string from the RFP requirements for similarity search
    query_text = json.dumps(rfp_requirements)

    try:
        similar_projects = search_similar_projects(query_text, top_k=top_k)
    except FileNotFoundError:
        similar_projects = []

    similar_projects_text = "\n\n".join(
        p["content"] for p in similar_projects
    ) if similar_projects else "No similar past projects found."

    referenced_project_ids = [
        p["metadata"]["id"] for p in similar_projects if "id" in p.get("metadata", {})
    ]

    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.4,
    )

    prompt = ChatPromptTemplate.from_template(PROPOSAL_PROMPT)
    chain = prompt | llm

    response = chain.invoke({
        "rfp_requirements": json.dumps(rfp_requirements, indent=2),
        "similar_projects": similar_projects_text,
    })

    raw_output = _extract_text_from_response(response)
    raw_output = _clean_json_output(raw_output)

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {raw_output}") from e

    parsed["referenced_project_ids"] = referenced_project_ids
    return parsed