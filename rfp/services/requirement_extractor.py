import json
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

EXTRACTION_PROMPT = """You are an expert business analyst. Analyze the following RFP (Request for Proposal) document text and extract structured information.

RFP TEXT:
{rfp_text}

Extract and return ONLY a valid JSON object (no markdown, no code fences, no extra text) with exactly these keys:

{{
  "project_type": "short category, e.g. E-commerce Website, Mobile App, ERP System",
  "client_name": "client or company name if mentioned, else null",
  "budget_range": "budget as mentioned in the text, else null",
  "timeline": "timeline/deadline as mentioned in the text, else null",
  "required_features": ["list", "of", "key", "features", "or", "requirements"],
  "summary": "2-3 sentence summary of what the client wants"
}}

Return ONLY the JSON object. No explanations, no markdown formatting."""


def _extract_text_from_response(response) -> str:
    """
    Handles both string and list-of-blocks response content
    (different Gemini model versions return different shapes).
    """
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


def extract_requirements_with_ai(rfp_text: str) -> dict:
    """
    Uses Gemini via LangChain to parse raw RFP text into structured requirement data.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
    chain = prompt | llm

    response = chain.invoke({"rfp_text": rfp_text})
    raw_output = _extract_text_from_response(response)

    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`")
        if raw_output.lower().startswith("json"):
            raw_output = raw_output[4:].strip()

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {raw_output}") from e

    return parsed


