"""
Schema Model Tests
Validates model defaults, serialization, and helper behavior.
"""

from models.schemas import ExtractedIntelligence, AgentThought, ScamType, Strategy, APIRequest, APIResponse


def test_extracted_intelligence_actionable_and_format():
    """Reality check: actionable intel detection and GUVI mapping work."""
    intel = ExtractedIntelligence(upi_ids=["a@upi"])
    assert intel.has_actionable_intel() is True
    formatted = intel.to_guvi_format()
    assert formatted["upiIds"] == ["a@upi"]


def test_agent_thought_defaults_and_required_fields():
    """Reality check: AgentThought accepts required fields and defaults others."""
    thought = AgentThought(
        scam_detected=True,
        current_strategy=Strategy.STALLING,
        response="Okay, ek minute."
    )
    assert thought.scam_type == ScamType.UNKNOWN
    assert thought.is_conversation_complete is False


def test_api_request_defaults():
    """Reality check: APIRequest fills optional fields with defaults."""
    request = APIRequest(sessionId="s1", message={"text": "hello"})
    assert request.conversationHistory == []
    assert request.metadata is None


def test_api_response_defaults():
    """Reality check: APIResponse has stable default shape."""
    response = APIResponse()
    assert response.status == "success"
    assert response.reply == ""
