"""
Tool definitions and execution logic for Claude tool use.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import CHROMA_PATH, EMBED_MODEL


TOOLS = [
    {
        "name": "get_project_details",
        "description": (
            "Retrieve detailed information about a specific project from Jalin's portfolio. "
            "Use this tool when the user asks for details, features, technical breakdown, "
            "or technical specifications of a named project. "
            "The tool returns the project title, link, and a full description chunk from "
            "the knowledge base that you should use to produce a numbered Technical Breakdown."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_title": {
                    "type": "string",
                    "description": (
                        "The exact or approximate name of the project to look up. "
                        "Examples: 'Kurt Douglas Foundation', 'Pawfect Pet Grooming', "
                        "'Team App Website', 'Chat App Website', 'JalinBright Official Portfolio'."
                    ),
                }
            },
            "required": ["project_title"],
        },
    }
]


def _get_project_details(project_title: str) -> str:
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    docs = db.similarity_search(project_title, k=3)
    if not docs:
        return f"No information found for project: {project_title}"
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        parts.append(f"(source: {source})\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def execute_tool(name: str, inputs: dict) -> str:
    if name == "get_project_details":
        return _get_project_details(inputs["project_title"])
    return f"Unknown tool: {name}"
