import os
from django.conf import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

INDEX_NAME = "historical_projects_index"


def _get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GOOGLE_API_KEY,
    )


def _get_index_path():
    os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)
    return str(settings.FAISS_INDEX_DIR / INDEX_NAME)


def build_or_update_index():
    """
    Rebuilds the FAISS index from ALL HistoricalProject rows in the database.
    Call this whenever historical projects are added/updated.
    """
    from knowledge_base.models import HistoricalProject

    projects = HistoricalProject.objects.all()

    if not projects.exists():
        raise ValueError("No historical projects found to index.")

    documents = []
    for project in projects:
        content = (
            f"Title: {project.title}\n"
            f"Project Type: {project.project_type}\n"
            f"Description: {project.description}\n"
            f"Tech Stack: {project.tech_stack}\n"
            f"Cost: {project.actual_cost}\n"
            f"Duration (weeks): {project.actual_duration_weeks}"
        )
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "id": project.id,
                    "title": project.title,
                    "project_type": project.project_type,
                    "actual_cost": str(project.actual_cost) if project.actual_cost else None,
                    "actual_duration_weeks": project.actual_duration_weeks,
                },
            )
        )

    embeddings = _get_embeddings()
    vector_store = FAISS.from_documents(documents, embeddings)

    index_path = _get_index_path()
    vector_store.save_local(index_path)

    # Mark all as indexed
    projects.update(is_indexed=True)

    return len(documents)


def search_similar_projects(query_text: str, top_k: int = 3):
    """
    Searches the FAISS index for the most similar historical projects
    given a query (usually the new RFP's extracted text/summary).
    Returns a list of dicts with content + metadata + similarity score.
    """
    index_path = _get_index_path()

    if not os.path.exists(index_path):
        raise FileNotFoundError("FAISS index not found. Run build_or_update_index() first.")

    embeddings = _get_embeddings()
    vector_store = FAISS.load_local(
        index_path, embeddings, allow_dangerous_deserialization=True
    )

    results = vector_store.similarity_search_with_score(query_text, k=top_k)

    output = []
    for doc, score in results:
        output.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "similarity_score": float(score),
        })

    return output