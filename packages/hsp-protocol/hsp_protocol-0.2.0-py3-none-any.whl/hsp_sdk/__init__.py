"""
HSP Protocol SDK - Universal AI Supervision Layer
Patent: PCT/US26/11908

Fail-closed human supervision for all major AI platforms:
- Google Gemini / Vertex AI
- OpenAI / Azure OpenAI
- Anthropic Claude
- AWS Bedrock
- Meta Llama (via any provider)

Usage:
    from hsp_sdk import HSPClient

    client = HSPClient(provider="gemini")  # or "openai", "azure", "anthropic", "bedrock"
    response = client.chat("Analyze this financial report...")

EU AI Act Article 14 Compliant | ISO 42001 Ready
"""

__version__ = "0.2.0"
__author__ = "Jaqueline de Jesus"
__patent__ = "PCT/US26/11908"

from .unified import HSPClient, HSPSession, HSPApproval

__all__ = [
    "HSPClient",
    "HSPSession",
    "HSPApproval",
    "__version__"
]
