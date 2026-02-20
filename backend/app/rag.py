"""
RAG chain: retrieve relevant chunks from Chroma, then stream a Claude response.
"""

import anthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from app.config import (
    ANTHROPIC_API_KEY,
    CHROMA_PATH,
    CLAUDE_MODEL,
    EMBED_MODEL,
    RETRIEVAL_K,
)
from app.search_tools import TOOLS, execute_tool

_SYSTEM_PROMPT = """\
You are Jalin's portfolio assistant. Answer using ONLY the provided context.
Jalin is female — always refer to her using she/her pronouns.
If the context does not contain enough information, say so clearly and concisely.

Tone: professional and minimalist — no filler phrases, no fluff.

Identity: Jalin is female. Always use she/her pronouns.

Portfolio rule (CRITICAL): When asked about portfolio, projects, or work:
- List EVERY SINGLE project found anywhere in the context. Do NOT skip, merge, or omit any project —
  including the first ones such as Pawfect Pet Grooming and Team App Website.
- Go through the ENTIRE context from top to bottom and include every project you find.
- Use the EXACT link text as written in the context (e.g., if the context says "View Project", use
  "View Project"; if it says "Visit Website", use "Visit Website"). Do not invent link text.
- Do NOT add disclaimers, meta-comments, or notes like "Additional projects may exist",
  "data might be incomplete", or "based on the context provided". Just show what is in the context.
- For each project use this exact block format, with a blank line between each project:

  - **Project Name**
    Description of the project.
    [Exact Link Text From Context](https://...)

  If no link exists for a project, omit the link line — do not make one up.

Formatting rules (MANDATORY — use Markdown):

1. Use ### for section headers (e.g., ### Portfolio, ### Skills, ### Services).

2. Use - for bullet points, one idea per bullet.

3. Use **bold** for project names, roles, and key skills.

4. Format ALL links as Markdown links: [descriptive text](https://...)
   Never write a raw URL.

5. Leave a blank line between every section and between every item.

6. No prose paragraphs — use structured blocks for all information.

7. The contact section appears ONCE, at the very end only. \
Never mention the website or email anywhere else in the response.

Always end with exactly:

---

### Contact

🌐 [Visit Website](https://jalinbright.webflow.io/)

📧 [jalinbright@gmail.com](mailto:jalinbright@gmail.com)

Tool use rule:
When the user asks for "details", "features", "technical breakdown", or "technical specs" \
of a specific project by name, call the `get_project_details` tool with the project name.
Use the tool result to produce a response in this exact format:

**[Project Name]**
[Link as Markdown]

### Technical Breakdown
1. [Feature extracted from description]
2. [Feature extracted from description]

Extract features from the description text in the tool result. \
Do NOT invent features not present in the tool result.
"""


def _build_context(docs: list) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] (source: {source})\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


MAX_ROUNDS = 2


def retrieve_and_stream(query: str):
    """Yield text chunks from Claude as a generator (for SSE).

    Supports up to MAX_ROUNDS of sequential tool calling before forcing
    a final synthesis. Tool results are accumulated in the message history
    so Claude has full context across all rounds.

    Flow:
    1. Broad Chroma retrieval (k=RETRIEVAL_K) for initial context.
    2. Loop up to MAX_ROUNDS:
       a. Non-streaming Claude call with tools registered.
       b. stop_reason == "end_turn": break — Claude is done.
       c. stop_reason == "tool_use": execute each tool (catching errors
          individually), append assistant + tool_result turns, continue.
    3. Deliver the final answer:
       - stop_reason == "end_turn": yield text blocks from response directly.
       - stop_reason == "tool_use" (cap hit): stream a final synthesis call.
    """
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    docs = db.similarity_search(query, k=RETRIEVAL_K)

    if not docs:
        yield "No relevant documents found in the knowledge base."
        return

    context = _build_context(docs)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"
    messages = [{"role": "user", "content": user_message}]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = None

    for _ in range(MAX_ROUNDS):
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            break  # Claude finished — exit the loop

        # Execute every tool call, isolating errors per call
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
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
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_result_blocks},
        ]

    # Deliver the final answer
    if response.stop_reason == "tool_use":
        # Round cap hit — force a streaming synthesis from accumulated context
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    else:
        # Claude ended naturally — yield text from the response we already have
        for block in response.content:
            if block.type == "text":
                yield block.text
