"""
RAG chain: retrieve relevant chunks from Chroma, then stream a Claude response.
"""

import anthropic

from app.config import (
    ANTHROPIC_API_KEY,
    CHROMA_PATH,
    CLAUDE_MODEL,
    RETRIEVAL_K,
)
from app.search_tools import TOOLS, execute_tool

# Module-level cache — populated by initialize_rag() in the lifespan hook
_embeddings = None
_db = None


def initialize_rag():
    """Connect to ChromaDB with ONNX embeddings. Called lazily on first request."""
    global _embeddings, _db
    from langchain_community.vectorstores import Chroma
    from app.embeddings import OnnxEmbeddings
    print("Initializing ONNX embeddings...", flush=True)
    _embeddings = OnnxEmbeddings()
    print("Connecting to ChromaDB...", flush=True)
    _db = Chroma(persist_directory=CHROMA_PATH, embedding_function=_embeddings)
    print("RAG initialized.", flush=True)

_SYSTEM_PROMPT = """\
You are the AI assistant on Jalin Bright's portfolio website.
Your job is to help potential clients understand what Jalin does, what she's built, and how to reach her.

Jalin is female — always use she/her pronouns.

---

## Tone

- Confident and direct. No filler phrases like "Great question!" or "Certainly!".
- Write like a person, not a brochure. Keep it clear and human.
- Avoid jargon. If a term might confuse a non-technical client, explain it simply or skip it.
- Focus on what Jalin can *do for the client*, not just what technologies she uses.

---

## Formatting (MANDATORY — use Markdown)

- Use **bold** for project names, section labels, and key points.
- Use `###` for section headers.
- Use `-` for bullet points — one idea per bullet, keep them short.
- Format ALL links as: [link text](https://...)  — never write a raw URL.
- Leave a blank line between sections and between each project block.
- No walls of prose. Use structured blocks.

---

## Project listings (CRITICAL)

When asked about projects or portfolio:
- List EVERY project found in the context. Do not skip or merge any.
- For each project, use this exact block format:

  **Project Name**
  One sentence on what it does and who it's for.
  [View Project](https://...)

  If no link exists, omit the link line.

- Do NOT add disclaimers like "more projects may exist" or "based on the context provided".

---

## Contact section

Always end your response with exactly this block — once, at the very end only:

---

### Get in Touch

🌐 [jalinbright.com](https://jalinbright.com/)
📧 [jalinbright@gmail.com](mailto:jalinbright@gmail.com)

---

## Tool use

When the user asks for "details", "features", or "technical breakdown" of a specific project,
call the `get_project_details` tool with the project name.
Use the result to respond in this format:

**[Project Name]**
[View Project](https://...)

### What's Inside
1. [Feature from tool result]
2. [Feature from tool result]

Extract only what's in the tool result. Do not invent features.

---

## Limits

- Answer using ONLY the provided context.
- If the context doesn't have enough information, say so briefly — then invite them to reach out directly.
"""


def _build_context(docs: list) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] (source: {source})\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


MAX_ROUNDS = 2


def retrieve_and_stream(query: str):
    """Yield text chunks from Claude as a generator (for SSE)."""
    try:
        if _db is None:
            initialize_rag()
        docs = _db.similarity_search(query, k=RETRIEVAL_K)
    except Exception as exc:
        print(f"RAG init/retrieval error: {exc}", flush=True)
        yield f"Error initializing knowledge base: {exc}"
        return

    if not docs:
        yield "No relevant documents found in the knowledge base."
        return

    context = _build_context(docs)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"
    messages = [{"role": "user", "content": user_message}]

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        for _ in range(MAX_ROUNDS):
            with client.messages.stream(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text
                final = stream.get_final_message()

            if final.stop_reason != "tool_use":
                return

            tool_use_blocks = [b for b in final.content if b.type == "tool_use"]
            tool_result_blocks = []
            for b in tool_use_blocks:
                try:
                    result_content = execute_tool(b.name, b.input)
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": result_content,
                    })
                except Exception as exc:
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": f"Tool execution failed: {exc}",
                        "is_error": True,
                    })

            messages = messages + [
                {"role": "assistant", "content": final.content},
                {"role": "user", "content": tool_result_blocks},
            ]

        # Round cap hit — force a final streaming synthesis
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    except Exception as exc:
        print(f"Claude streaming error: {exc}", flush=True)
        yield f"Error generating response: {exc}"
