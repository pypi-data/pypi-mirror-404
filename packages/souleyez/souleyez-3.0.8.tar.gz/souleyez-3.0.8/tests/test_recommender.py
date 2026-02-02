#!/usr/bin/env python3
"""
Unit tests for AI attack recommender
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from souleyez.ai.recommender import AttackRecommender


def test_recommender_initialization():
    """Test basic initialization works"""
    with patch("souleyez.ai.recommender.LLMFactory") as mock_factory:
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.service = Mock()  # Simulate OllamaProvider with service attr
        mock_factory.get_available_provider.return_value = mock_provider

        recommender = AttackRecommender()
        assert recommender.provider is not None
        assert recommender.context_builder is not None


def test_suggest_next_step_provider_not_available():
    """Test recommendation fails gracefully when provider not available"""
    mock_provider = Mock()
    mock_provider.is_available.return_value = False

    recommender = AttackRecommender(provider=mock_provider)
    result = recommender.suggest_next_step(engagement_id=1)

    assert result is not None
    assert "error" in result
    assert "not available" in result["error"]
    assert result["action"] is None


def test_suggest_next_step_context_build_fails():
    """Test recommendation handles context build failure"""
    mock_provider = Mock()
    mock_provider.is_available.return_value = True

    recommender = AttackRecommender(provider=mock_provider)

    # Mock context builder to raise exception
    recommender.context_builder.build_context = Mock(side_effect=Exception("DB error"))

    result = recommender.suggest_next_step(engagement_id=1)

    assert result is not None
    assert "error" in result
    assert "engagement data" in result["error"].lower()


def test_suggest_next_step_llm_returns_empty():
    """Test recommendation handles empty LLM response"""
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    mock_provider.generate.return_value = None

    recommender = AttackRecommender(provider=mock_provider)
    recommender.context_builder.build_context = Mock(return_value="test context")
    recommender.context_builder.get_state_summary = Mock(return_value="state summary")

    result = recommender.suggest_next_step(engagement_id=1)

    assert result is not None
    assert "error" in result
    assert "empty" in result["error"].lower()


def test_suggest_next_step_llm_generation_fails():
    """Test recommendation handles LLM exception"""
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    mock_provider.generate.side_effect = Exception("Timeout")

    recommender = AttackRecommender(provider=mock_provider)
    recommender.context_builder.build_context = Mock(return_value="test context")
    recommender.context_builder.get_state_summary = Mock(return_value="state summary")

    result = recommender.suggest_next_step(engagement_id=1)

    assert result is not None
    assert "error" in result
    assert "generation failed" in result["error"].lower()


def test_suggest_next_step_success():
    """Test successful recommendation generation and parsing"""
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    mock_provider.generate.return_value = """
ACTION: Test SSH with credential msfadmin:msfadmin
TARGET: 10.0.0.82:22
RATIONALE: We have discovered an untested credential and SSH is open
EXPECTED: Gain shell access to the target system
RISK: medium
"""

    recommender = AttackRecommender(provider=mock_provider)
    recommender.context_builder.build_context = Mock(return_value="test context")
    recommender.context_builder.get_state_summary = Mock(return_value="state summary")

    result = recommender.suggest_next_step(engagement_id=1)

    assert result is not None
    assert result.get("error") is None
    assert result["action"] == "Test SSH with credential msfadmin:msfadmin"
    assert result["target"] == "10.0.0.82:22"
    assert "credential" in result["rationale"].lower()
    assert "shell" in result["expected_outcome"].lower()
    assert result["risk_level"] == "medium"


def test_parse_response_missing_fields():
    """Test response parsing fails when fields missing"""
    with patch("souleyez.ai.recommender.LLMFactory") as mock_factory:
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_factory.get_available_provider.return_value = mock_provider

        recommender = AttackRecommender()

        # Missing TARGET field
        malformed = """
ACTION: Test something
RATIONALE: Because reasons
EXPECTED: Good things
RISK: low
"""

        with pytest.raises(ValueError) as exc_info:
            recommender._parse_response(malformed)

        assert "TARGET" in str(exc_info.value)


def test_parse_response_all_fields():
    """Test response parsing extracts all fields correctly"""
    with patch("souleyez.ai.recommender.LLMFactory") as mock_factory:
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_factory.get_available_provider.return_value = mock_provider

        recommender = AttackRecommender()

        response = """
ACTION: Run nmap full port scan
TARGET: 10.0.0.82
RATIONALE: Quick scan found SSH/HTTP, need full enumeration
EXPECTED: Discover additional services and attack surface
RISK: low
"""

        result = recommender._parse_response(response)

        assert result["action"] == "Run nmap full port scan"
        assert result["target"] == "10.0.0.82"
        assert "enumeration" in result["rationale"]
        assert "services" in result["expected_outcome"]
        assert result["risk_level"] == "low"


def test_parse_response_multiline_values():
    """Test parsing handles multiline field values"""
    with patch("souleyez.ai.recommender.LLMFactory") as mock_factory:
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_factory.get_available_provider.return_value = mock_provider

        recommender = AttackRecommender()

        response = """
ACTION: Test credentials against multiple services
TARGET: 10.0.0.82 (SSH:22, MySQL:3306, SMB:445)
RATIONALE: We have valid credentials msfadmin:msfadmin.
Testing against all services increases chance of access.
EXPECTED: Gain access to database or file shares.
May reveal additional information.
RISK: medium
"""

        result = recommender._parse_response(response)

        assert "multiple" in result["action"].lower()
        assert "10.0.0.82" in result["target"]
        assert "credentials" in result["rationale"].lower()
        assert "database" in result["expected_outcome"].lower()
        assert result["risk_level"] == "medium"


def test_parse_response_invalid_risk_level():
    """Test parsing handles invalid risk level gracefully"""
    with patch("souleyez.ai.recommender.LLMFactory") as mock_factory:
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_factory.get_available_provider.return_value = mock_provider

        recommender = AttackRecommender()

        response = """
ACTION: Test something
TARGET: 10.0.0.1
RATIONALE: Because
EXPECTED: Results
RISK: super-high
"""

        result = recommender._parse_response(response)

        # Should default to medium
        assert result["risk_level"] == "medium"


def test_parse_response_case_insensitive():
    """Test parsing is case-insensitive for field names"""
    with patch("souleyez.ai.recommender.LLMFactory") as mock_factory:
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_factory.get_available_provider.return_value = mock_provider

        recommender = AttackRecommender()

        response = """
action: Test something
target: 10.0.0.1
rationale: Because reasons
expected: Good outcomes
risk: high
"""

        result = recommender._parse_response(response)

        assert result["action"] == "Test something"
        assert result["target"] == "10.0.0.1"
        assert result["risk_level"] == "high"


def test_prompt_includes_context():
    """Test that generated prompt includes engagement context"""
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    mock_provider.generate.return_value = """
ACTION: Test
TARGET: 10.0.0.1
RATIONALE: Test
EXPECTED: Test
RISK: low
"""

    recommender = AttackRecommender(provider=mock_provider)
    test_context = "ENGAGEMENT: Test\nHOSTS: 10.0.0.82"
    recommender.context_builder.build_context = Mock(return_value=test_context)
    recommender.context_builder.get_state_summary = Mock(return_value="State summary")

    result = recommender.suggest_next_step(engagement_id=1)

    # Verify generate was called with prompt containing our context
    mock_provider.generate.assert_called_once()
    call_args = mock_provider.generate.call_args
    # Get the prompt from args or kwargs
    if call_args.args:
        prompt = call_args.args[0]
    else:
        prompt = call_args.kwargs.get("prompt", "")

    assert test_context in prompt
    assert "expert penetration tester" in prompt.lower()


def test_recommendation_returns_none_on_malformed_response():
    """Test that malformed LLM response is handled"""
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    mock_provider.generate.return_value = "This is garbage output from LLM"

    recommender = AttackRecommender(provider=mock_provider)
    recommender.context_builder.build_context = Mock(return_value="test")
    recommender.context_builder.get_state_summary = Mock(return_value="state")

    result = recommender.suggest_next_step(engagement_id=1)

    assert result is not None
    assert "error" in result
    assert "parse" in result["error"].lower()
    assert "raw_response" in result
