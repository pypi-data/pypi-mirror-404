"""
souleyez.ai - AI-powered attack path recommendations and report generation
"""

from .claude_provider import (
    ANTHROPIC_AVAILABLE,
    ClaudeProvider,
    clear_claude_api_key,
    set_claude_api_key,
)
from .context_builder import ContextBuilder
from .llm_factory import LLMFactory
from .llm_provider import LLMProvider, LLMProviderType
from .ollama_provider import OllamaProvider
from .ollama_service import OLLAMA_AVAILABLE, OllamaService
from .recommender import AttackRecommender
from .report_context import ReportContextBuilder
from .report_service import AIReportService

__all__ = [
    "OllamaService",
    "ContextBuilder",
    "AttackRecommender",
    "OLLAMA_AVAILABLE",
    "LLMProvider",
    "LLMProviderType",
    "OllamaProvider",
    "ClaudeProvider",
    "ANTHROPIC_AVAILABLE",
    "set_claude_api_key",
    "clear_claude_api_key",
    "LLMFactory",
    "ReportContextBuilder",
    "AIReportService",
]
