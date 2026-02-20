"""
Tests for the agentic tool-use loop in retrieve_and_stream().

Covers:
  - No tool use (direct answer)
  - Single round of tool use
  - Two sequential rounds of tool use (the agentic scenario)
  - Graceful handling of tool execution errors (is_error block)
  - Jalin's she/her identity preserved in _SYSTEM_PROMPT
  - System prompt passed to every Claude API call
"""

from unittest.mock import MagicMock, patch, call

import pytest

from app.rag import retrieve_and_stream, _SYSTEM_PROMPT, MAX_ROUNDS


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_doc(content: str = "Sample portfolio content."):
    doc = MagicMock()
    doc.page_content = content
    doc.metadata = {"source": "data/test.txt"}
    return doc


def _make_tool_use_response(tool_name: str, tool_input: dict, response_id: str = "toolu_01"):
    """Simulate a Claude response that calls a tool."""
    block = MagicMock()
    block.type = "tool_use"
    block.id = response_id
    block.name = tool_name
    block.input = tool_input

    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [block]
    return response


def _make_text_response(text: str):
    """Simulate a Claude response that ends with a text answer."""
    block = MagicMock()
    block.type = "text"
    block.text = text

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_mock_stream(text_chunks: list):
    """Simulate the context manager returned by client.messages.stream()."""
    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter(text_chunks)
    return stream


# ── Shared patches ─────────────────────────────────────────────────────────────

_PATCH_EMBEDDINGS = "app.rag.HuggingFaceEmbeddings"
_PATCH_CHROMA = "app.rag.Chroma"
_PATCH_ANTHROPIC = "app.rag.anthropic.Anthropic"
_PATCH_EXECUTE_TOOL = "app.rag.execute_tool"


def _mock_db(mock_chroma_cls, content="Sample content"):
    db = MagicMock()
    db.similarity_search.return_value = [_make_doc(content)]
    mock_chroma_cls.return_value = db
    return db


# ── Test 1: No tool use ────────────────────────────────────────────────────────

@patch(_PATCH_EXECUTE_TOOL)
@patch(_PATCH_CHROMA)
@patch(_PATCH_EMBEDDINGS)
@patch(_PATCH_ANTHROPIC)
def test_no_tool_use_yields_direct_answer(
    mock_anthropic_cls, mock_embeddings_cls, mock_chroma_cls, mock_execute_tool
):
    """When Claude returns end_turn immediately, text is yielded without any tool calls."""
    _mock_db(mock_chroma_cls)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_text_response("Jalin is a web designer.")
    mock_anthropic_cls.return_value = mock_client

    result = list(retrieve_and_stream("Who is Jalin?"))

    assert result == ["Jalin is a web designer."]
    mock_client.messages.create.assert_called_once()
    mock_client.messages.stream.assert_not_called()
    mock_execute_tool.assert_not_called()


# ── Test 2: Single round of tool use ──────────────────────────────────────────

@patch(_PATCH_EXECUTE_TOOL, return_value="KDF: custom CMS, donation integration.")
@patch(_PATCH_CHROMA)
@patch(_PATCH_EMBEDDINGS)
@patch(_PATCH_ANTHROPIC)
def test_single_round_tool_use(
    mock_anthropic_cls, mock_embeddings_cls, mock_chroma_cls, mock_execute_tool
):
    """
    Round 0 triggers a tool call; Round 1 returns the synthesis.
    No streaming call is needed — Claude ended naturally after seeing tool results.
    """
    _mock_db(mock_chroma_cls)

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_tool_use_response(
            "get_project_details",
            {"project_title": "Kurt Douglas Foundation"},
            "toolu_01",
        ),
        _make_text_response("KDF featured a custom CMS and donation integration."),
    ]
    mock_anthropic_cls.return_value = mock_client

    result = list(retrieve_and_stream("Tell me about the Kurt Douglas Foundation project."))

    assert result == ["KDF featured a custom CMS and donation integration."]
    assert mock_client.messages.create.call_count == 2
    mock_client.messages.stream.assert_not_called()
    mock_execute_tool.assert_called_once_with(
        "get_project_details", {"project_title": "Kurt Douglas Foundation"}
    )

    # Round 1's create() call must include the tool result in its messages
    round1_messages = mock_client.messages.create.call_args_list[1].kwargs["messages"]
    # [user_msg, assistant_tool_use, user_tool_result]
    assert len(round1_messages) == 3
    assert round1_messages[1]["role"] == "assistant"
    assert round1_messages[2]["role"] == "user"
    tool_result = round1_messages[2]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert tool_result["tool_use_id"] == "toolu_01"
    assert "custom CMS" in tool_result["content"]


# ── Test 3: Two sequential rounds (the agentic scenario) ──────────────────────

@patch(_PATCH_EXECUTE_TOOL, side_effect=[
    "KDF: Webflow CMS, custom donation integration.",
    "Team App Website also uses Webflow CMS for content management.",
])
@patch(_PATCH_CHROMA)
@patch(_PATCH_EMBEDDINGS)
@patch(_PATCH_ANTHROPIC)
def test_two_round_sequential_tool_use(
    mock_anthropic_cls, mock_embeddings_cls, mock_chroma_cls, mock_execute_tool
):
    """
    Scenario: 'Does the tech used in Kurt Douglas Foundation appear in other projects?'
      Round 0 → get_project_details('Kurt Douglas Foundation') → finds Webflow CMS
      Round 1 → get_project_details('Webflow CMS') → finds Team App Website
      Cap hit → streaming synthesis call with all accumulated context
    """
    _mock_db(mock_chroma_cls)

    mock_stream = _make_mock_stream(["Both KDF and Team App ", "use Webflow CMS."])

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_tool_use_response(
            "get_project_details",
            {"project_title": "Kurt Douglas Foundation"},
            "toolu_01",
        ),
        _make_tool_use_response(
            "get_project_details",
            {"project_title": "Webflow CMS"},
            "toolu_02",
        ),
    ]
    mock_client.messages.stream.return_value = mock_stream
    mock_anthropic_cls.return_value = mock_client

    result = list(
        retrieve_and_stream(
            "Does the tech used in Kurt Douglas Foundation appear in other projects?"
        )
    )

    assert result == ["Both KDF and Team App ", "use Webflow CMS."]
    assert mock_client.messages.create.call_count == MAX_ROUNDS
    mock_client.messages.stream.assert_called_once()
    assert mock_execute_tool.call_count == 2

    # Verify the two sequential tool calls used the expected inputs
    assert mock_execute_tool.call_args_list[0] == call(
        "get_project_details", {"project_title": "Kurt Douglas Foundation"}
    )
    assert mock_execute_tool.call_args_list[1] == call(
        "get_project_details", {"project_title": "Webflow CMS"}
    )

    # The streaming call's messages must contain both tool results
    stream_messages = mock_client.messages.stream.call_args.kwargs["messages"]
    # [user, assistant_0, tool_result_0, assistant_1, tool_result_1]
    assert len(stream_messages) == 5
    assert stream_messages[2]["content"][0]["tool_use_id"] == "toolu_01"
    assert stream_messages[4]["content"][0]["tool_use_id"] == "toolu_02"


# ── Test 4: Tool execution error — graceful degradation ───────────────────────

@patch(_PATCH_EXECUTE_TOOL, side_effect=Exception("Chroma connection failed"))
@patch(_PATCH_CHROMA)
@patch(_PATCH_EMBEDDINGS)
@patch(_PATCH_ANTHROPIC)
def test_tool_execution_error_is_graceful(
    mock_anthropic_cls, mock_embeddings_cls, mock_chroma_cls, mock_execute_tool
):
    """
    When a tool raises an exception, an is_error=True block is sent to Claude.
    The conversation continues rather than crashing the SSE stream.
    """
    _mock_db(mock_chroma_cls)

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_tool_use_response(
            "get_project_details",
            {"project_title": "Kurt Douglas Foundation"},
            "toolu_err",
        ),
        _make_text_response("I encountered an error retrieving the details, but here is what I know."),
    ]
    mock_anthropic_cls.return_value = mock_client

    # Must not raise
    result = list(retrieve_and_stream("Details of Kurt Douglas Foundation?"))

    assert len(result) > 0

    # The tool_result sent to Round 1 must carry is_error=True
    round1_messages = mock_client.messages.create.call_args_list[1].kwargs["messages"]
    tool_result_block = round1_messages[2]["content"][0]
    assert tool_result_block["is_error"] is True
    assert "Chroma connection failed" in tool_result_block["content"]
    assert tool_result_block["tool_use_id"] == "toolu_err"


# ── Test 5: Identity — she/her pronouns in system prompt ──────────────────────

def test_she_her_pronouns_in_system_prompt():
    """_SYSTEM_PROMPT must refer to Jalin as female with she/her pronouns."""
    prompt_lower = _SYSTEM_PROMPT.lower()
    assert "she/her" in prompt_lower or "female" in prompt_lower, (
        "System prompt must establish Jalin's she/her identity."
    )


# ── Test 6: System prompt passed to every API round ───────────────────────────

@patch(_PATCH_EXECUTE_TOOL, return_value="tool result")
@patch(_PATCH_CHROMA)
@patch(_PATCH_EMBEDDINGS)
@patch(_PATCH_ANTHROPIC)
def test_system_prompt_in_all_rounds(
    mock_anthropic_cls, mock_embeddings_cls, mock_chroma_cls, mock_execute_tool
):
    """
    _SYSTEM_PROMPT (containing she/her instructions) is sent to every
    non-streaming create() call and to the final streaming call.
    """
    _mock_db(mock_chroma_cls)

    mock_stream = _make_mock_stream(["Final synthesis."])
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_tool_use_response(
            "get_project_details", {"project_title": "KDF"}, "toolu_01"
        ),
        _make_tool_use_response(
            "get_project_details", {"project_title": "Webflow CMS"}, "toolu_02"
        ),
    ]
    mock_client.messages.stream.return_value = mock_stream
    mock_anthropic_cls.return_value = mock_client

    list(retrieve_and_stream("Cross-project tech analysis"))

    # Every non-streaming call must use _SYSTEM_PROMPT
    for api_call in mock_client.messages.create.call_args_list:
        assert api_call.kwargs["system"] == _SYSTEM_PROMPT, (
            "System prompt must be identical across all create() rounds."
        )

    # The final streaming call must also use _SYSTEM_PROMPT
    stream_system = mock_client.messages.stream.call_args.kwargs["system"]
    assert stream_system == _SYSTEM_PROMPT, (
        "System prompt must be passed to the streaming synthesis call."
    )
    # Confirm she/her is present in every round's system prompt
    assert "she/her" in _SYSTEM_PROMPT.lower() or "female" in _SYSTEM_PROMPT.lower()
