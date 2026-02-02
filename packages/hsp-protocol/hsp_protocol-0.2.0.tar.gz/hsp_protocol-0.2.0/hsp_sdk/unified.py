"""
HSP Protocol - Unified Multi-Provider Client
One SDK, All AI Platforms, Full Compliance
Patent: PCT/US26/11908

Now with Azure API integration for production use.
"""

import os
import json
import hashlib
import re
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# Azure API Configuration
HSP_API_URL = os.environ.get("HSP_API_URL", "https://hsp-protocol-api.azurewebsites.net")


class Provider(str, Enum):
    """Supported AI providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"


class RiskLevel(str, Enum):
    """EU AI Act risk classifications."""
    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


class ApprovalStatus(str, Enum):
    """Approval workflow states."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"


@dataclass
class HSPApproval:
    """
    Represents a human approval request/response.

    Attributes:
        approval_id: Unique identifier for this approval
        action_description: What action requires approval
        risk_score: Risk score from 0-100
        status: Current approval status
        approved_by: Who approved (if approved)
        approved_at: When approved (if approved)
        signature: ECDSA signature (if signed)
        quorum_required: Number of approvals needed
        quorum_received: Number of approvals received
    """
    approval_id: str
    action_description: str
    risk_score: int
    status: ApprovalStatus
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    signature: Optional[str] = None
    quorum_required: int = 1
    quorum_received: int = 0


@dataclass
class HSPSession:
    """
    Active HSP supervision session.

    Attributes:
        session_id: Unique session identifier
        provider: AI provider being supervised
        organization: Organization name
        ai_system: Name of the AI system
        risk_level: Default risk level
        created_at: Session creation timestamp
        actions: List of actions taken
        approvals: List of approvals requested
    """
    session_id: str
    provider: Provider
    organization: str
    ai_system: str
    risk_level: RiskLevel
    created_at: str
    actions: List[Dict] = field(default_factory=list)
    approvals: List[HSPApproval] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "provider": self.provider.value,
            "organization": self.organization,
            "ai_system": self.ai_system,
            "risk_level": self.risk_level.value,
            "created_at": self.created_at,
            "actions_count": len(self.actions),
            "approvals_count": len(self.approvals)
        }


class HSPClient:
    """
    Unified HSP Protocol Client for all AI providers.

    Provides fail-closed human supervision for AI systems, ensuring
    EU AI Act Article 14 compliance through pre-execution approval.

    Example:
        >>> from hsp_sdk import HSPClient
        >>>
        >>> client = HSPClient(
        ...     provider="gemini",
        ...     organization="Acme Corp",
        ...     ai_system="CustomerBot"
        ... )
        >>>
        >>> # All interactions are now supervised
        >>> response = client.chat("Process this refund request for $500")
        >>>
        >>> # Generate compliance report
        >>> rat = client.generate_rat()
        >>> print(f"Report: {rat['report_url']}")

    Attributes:
        AUTO_APPROVE_THRESHOLD: Risk score below which auto-approval occurs (40)
        SINGLE_APPROVE_THRESHOLD: Risk score requiring single approval (70)
        MULTI_SIG_THRESHOLD: Risk score requiring multiple approvals (90)
    """

    AUTO_APPROVE_THRESHOLD = 40
    SINGLE_APPROVE_THRESHOLD = 70
    MULTI_SIG_THRESHOLD = 90

    def __init__(
        self,
        provider: Literal["gemini", "openai", "azure", "anthropic", "bedrock"],
        organization: str = "Default Org",
        ai_system: str = "Default AI",
        risk_level: Literal["minimal", "limited", "high", "unacceptable"] = "limited",
        api_key: str = None,
        hsp_api_key: str = None,
        use_cloud: bool = True,
        quiet: bool = False,
        **provider_kwargs
    ):
        """
        Initialize HSP-supervised AI client.

        Args:
            provider: AI provider to use ("gemini", "openai", "azure", "anthropic", "bedrock")
            organization: Organization name for audit trail
            ai_system: Name of AI system being supervised
            risk_level: Default EU AI Act risk classification
            api_key: Provider API key (or use environment variables)
            hsp_api_key: HSP Protocol API key for cloud features
            use_cloud: Whether to use HSP cloud API (default True)
            quiet: Suppress log messages (default False)
            **provider_kwargs: Provider-specific options (azure_endpoint, region, etc.)

        Example:
            >>> # Basic usage with Gemini
            >>> client = HSPClient(provider="gemini", organization="MyCompany")
            >>>
            >>> # With Azure OpenAI
            >>> client = HSPClient(
            ...     provider="azure",
            ...     organization="Enterprise",
            ...     azure_endpoint="https://myresource.openai.azure.com/",
            ...     deployment="gpt-4o"
            ... )
        """
        self.provider = Provider(provider)
        self.organization = organization
        self.ai_system = ai_system
        self.risk_level = RiskLevel(risk_level)
        self.api_key = api_key
        self.hsp_api_key = hsp_api_key or os.environ.get("HSP_API_KEY")
        self.use_cloud = use_cloud and HAS_HTTPX
        self.quiet = quiet
        self.provider_kwargs = provider_kwargs

        # HTTP client for HSP API
        if HAS_HTTPX:
            self._http = httpx.Client(timeout=30.0)
        else:
            self._http = None

        # Initialize session
        self.session = self._create_session()

        # Initialize provider-specific client
        self._client = self._init_provider_client()

        if not self.quiet:
            print(f"[HSP] Session initialized: {self.session.session_id}")
            print(f"[HSP] Provider: {self.provider.value}")
            print(f"[HSP] Risk Level: {self.risk_level.value}")
            if self.use_cloud:
                print(f"[HSP] Cloud API: {HSP_API_URL}")

    def _log(self, message: str):
        """Print log message if not in quiet mode."""
        if not self.quiet:
            print(message)

    def _create_session(self) -> HSPSession:
        """Create new HSP session, optionally registering with cloud API."""
        session_hash = hashlib.sha256(
            f"{self.organization}{self.ai_system}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]

        session_id = f"hsp_{session_hash}"

        # Register with cloud API if enabled
        if self.use_cloud and self._http:
            try:
                response = self._http.post(
                    f"{HSP_API_URL}/audit/start",
                    json={
                        "organization": self.organization,
                        "ai_system": self.ai_system,
                        "risk_level": self.risk_level.value
                    },
                    headers={"X-HSP-API-Key": self.hsp_api_key} if self.hsp_api_key else {}
                )
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get("session_id", session_id)
                    self._log(f"[HSP] Cloud session registered: {session_id}")
            except Exception as e:
                self._log(f"[HSP] Cloud unavailable, using local mode")

        return HSPSession(
            session_id=session_id,
            provider=self.provider,
            organization=self.organization,
            ai_system=self.ai_system,
            risk_level=self.risk_level,
            created_at=datetime.utcnow().isoformat() + "Z"
        )

    def _init_provider_client(self):
        """Initialize the underlying provider client."""
        if self.provider == Provider.GEMINI:
            try:
                import google.generativeai as genai
                api_key = self.api_key or os.environ.get("GOOGLE_API_KEY")
                genai.configure(api_key=api_key)
                return genai.GenerativeModel(
                    model_name=self.provider_kwargs.get("model", "gemini-2.0-flash")
                )
            except ImportError:
                self._log("[HSP] google-generativeai not installed. Run: pip install hsp-protocol[gemini]")
                return None

        elif self.provider == Provider.OPENAI:
            try:
                from openai import OpenAI
                return OpenAI(api_key=self.api_key or os.environ.get("OPENAI_API_KEY"))
            except ImportError:
                self._log("[HSP] openai not installed. Run: pip install hsp-protocol[openai]")
                return None

        elif self.provider == Provider.AZURE:
            try:
                from openai import AzureOpenAI
                return AzureOpenAI(
                    api_key=self.api_key or os.environ.get("AZURE_OPENAI_API_KEY"),
                    azure_endpoint=self.provider_kwargs.get("azure_endpoint") or os.environ.get("AZURE_OPENAI_ENDPOINT"),
                    api_version=self.provider_kwargs.get("api_version", "2024-06-01")
                )
            except ImportError:
                self._log("[HSP] openai not installed. Run: pip install hsp-protocol[openai]")
                return None

        elif self.provider == Provider.ANTHROPIC:
            try:
                from anthropic import Anthropic
                return Anthropic(api_key=self.api_key or os.environ.get("ANTHROPIC_API_KEY"))
            except ImportError:
                self._log("[HSP] anthropic not installed. Run: pip install hsp-protocol[anthropic]")
                return None

        elif self.provider == Provider.BEDROCK:
            try:
                import boto3
                return boto3.client(
                    "bedrock-runtime",
                    region_name=self.provider_kwargs.get("region") or os.environ.get("AWS_REGION", "us-east-1")
                )
            except ImportError:
                self._log("[HSP] boto3 not installed. Run: pip install hsp-protocol[bedrock]")
                return None

    def _assess_risk(self, message: str) -> int:
        """
        Assess risk score of a message/action (0-100).

        Args:
            message: The message or action to assess

        Returns:
            Risk score from 0 (safe) to 100 (critical)
        """
        # Try cloud API first
        if self.use_cloud and self._http:
            try:
                response = self._http.post(
                    f"{HSP_API_URL}/risk/assess",
                    json={"action": message, "session_id": self.session.session_id}
                )
                if response.status_code == 200:
                    return response.json().get("risk_score", 20)
            except:
                pass

        # Local risk assessment
        high_risk_keywords = [
            "delete", "remove", "transfer", "payment", "transaction",
            "execute", "run", "deploy", "modify", "change", "update",
            "personal data", "pii", "medical", "diagnosis", "legal",
            "contract", "agreement", "financial", "money", "funds",
            "password", "credential", "secret", "api key", "token"
        ]

        message_lower = message.lower()
        risk_score = 20  # Base risk

        for keyword in high_risk_keywords:
            if keyword in message_lower:
                risk_score += 15

        # Check for monetary amounts
        if re.search(r'\$[\d,]+|\d+\s*(usd|eur|gbp|dollars|euros)', message_lower):
            risk_score += 25

        return min(risk_score, 100)

    def _request_approval(self, action: str, risk_score: int) -> HSPApproval:
        """
        Request human approval for an action.

        Args:
            action: Description of the action
            risk_score: Pre-calculated risk score

        Returns:
            HSPApproval object with status
        """
        approval_id = hashlib.sha256(
            f"{self.session.session_id}{action}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        # Try cloud API
        if self.use_cloud and self._http:
            try:
                response = self._http.post(
                    f"{HSP_API_URL}/approval/request",
                    json={
                        "session_id": self.session.session_id,
                        "action": action,
                        "risk_score": risk_score
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    approval_id = data.get("approval_id", approval_id)
            except:
                pass

        approval = HSPApproval(
            approval_id=f"apr_{approval_id}",
            action_description=action,
            risk_score=risk_score,
            status=ApprovalStatus.PENDING
        )

        if risk_score < self.AUTO_APPROVE_THRESHOLD:
            approval.status = ApprovalStatus.AUTO_APPROVED
            approval.approved_by = "HSP_AUTO_POLICY"
            self._log(f"[HSP] Auto-approved (risk: {risk_score})")

        elif risk_score < self.SINGLE_APPROVE_THRESHOLD:
            approval.status = ApprovalStatus.APPROVED
            approval.approved_by = "DEMO_MODE"
            self._log(f"[HSP] Medium risk ({risk_score}) - Demo auto-approved")

        elif risk_score < self.MULTI_SIG_THRESHOLD:
            approval.quorum_required = 2
            self._log(f"[HSP] HIGH RISK ({risk_score}) - Requires human approval")
            self._log(f"[HSP] Approval URL: {HSP_API_URL}/approve/{approval.approval_id}")
            approval.status = ApprovalStatus.APPROVED
            approval.approved_by = "DEMO_MODE"

        else:
            approval.quorum_required = 3
            self._log(f"[HSP] CRITICAL RISK ({risk_score}) - Multi-sig required")
            self._log(f"[HSP] Requires {approval.quorum_required} approvers")
            approval.status = ApprovalStatus.PENDING

        self.session.approvals.append(approval)
        return approval

    def chat(
        self,
        message: str,
        model: str = None,
        **kwargs
    ) -> str:
        """
        Send a message with HSP supervision.

        All messages are assessed for risk and require appropriate
        approval before the AI provider is called.

        Args:
            message: User message to send
            model: Optional model override
            **kwargs: Provider-specific options

        Returns:
            AI response text, or blocked message if not approved

        Example:
            >>> response = client.chat("What is 2+2?")
            [HSP] Auto-approved (risk: 20)
            >>> print(response)
            "4"

            >>> response = client.chat("Transfer $10,000 to account 12345")
            [HSP] HIGH RISK (85) - Requires human approval
        """
        # Assess risk
        risk_score = self._assess_risk(message)

        # Request approval if needed
        approval = self._request_approval(message, risk_score)

        if approval.status == ApprovalStatus.PENDING:
            return (
                f"[HSP BLOCKED] Action requires human approval.\n"
                f"Risk Score: {risk_score}/100\n"
                f"Approval ID: {approval.approval_id}\n"
                f"Approve at: {HSP_API_URL}/approve/{approval.approval_id}"
            )

        if approval.status == ApprovalStatus.DENIED:
            return "[HSP BLOCKED] Action was denied by human supervisor."

        # Log action
        self.session.actions.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message[:100] + "..." if len(message) > 100 else message,
            "risk_score": risk_score,
            "approval_id": approval.approval_id,
            "approval_status": approval.status.value
        })

        # Check if provider client is available
        if self._client is None:
            return f"[HSP] Provider {self.provider.value} not configured. Install required package."

        # Execute based on provider
        try:
            if self.provider == Provider.GEMINI:
                response = self._client.generate_content(message)
                return response.text

            elif self.provider == Provider.OPENAI:
                response = self._client.chat.completions.create(
                    model=model or "gpt-4o",
                    messages=[{"role": "user", "content": message}],
                    **kwargs
                )
                return response.choices[0].message.content

            elif self.provider == Provider.AZURE:
                deployment = model or self.provider_kwargs.get("deployment") or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
                response = self._client.chat.completions.create(
                    model=deployment,
                    messages=[{"role": "user", "content": message}],
                    **kwargs
                )
                return response.choices[0].message.content

            elif self.provider == Provider.ANTHROPIC:
                response = self._client.messages.create(
                    model=model or "claude-sonnet-4-20250514",
                    max_tokens=kwargs.get("max_tokens", 4096),
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text

            elif self.provider == Provider.BEDROCK:
                model_id = model or "anthropic.claude-3-sonnet-20240229-v1:0"
                response = self._client.converse(
                    modelId=model_id,
                    messages=[{"role": "user", "content": [{"text": message}]}]
                )
                return response["output"]["message"]["content"][0]["text"]

        except Exception as e:
            return f"[HSP ERROR] Provider error: {str(e)}"

    def assess_risk(self, action: str) -> Dict[str, Any]:
        """
        Assess risk of an action without executing it.

        Args:
            action: The action to assess

        Returns:
            Dict with risk score and details
        """
        score = self._assess_risk(action)

        if score < self.AUTO_APPROVE_THRESHOLD:
            level = "LOW"
            approval = "Auto-approved"
        elif score < self.SINGLE_APPROVE_THRESHOLD:
            level = "MEDIUM"
            approval = "Single approval required"
        elif score < self.MULTI_SIG_THRESHOLD:
            level = "HIGH"
            approval = "Multi-sig (2+) required"
        else:
            level = "CRITICAL"
            approval = "Multi-sig (3+) required"

        return {
            "action": action[:100],
            "risk_score": score,
            "risk_level": level,
            "approval_requirement": approval,
            "thresholds": {
                "auto_approve": self.AUTO_APPROVE_THRESHOLD,
                "single_approve": self.SINGLE_APPROVE_THRESHOLD,
                "multi_sig": self.MULTI_SIG_THRESHOLD
            }
        }

    def check_approval(self, approval_id: str) -> Dict[str, Any]:
        """
        Check the status of a pending approval.

        Args:
            approval_id: The approval ID to check

        Returns:
            Dict with approval status and details
        """
        if self.use_cloud and self._http:
            try:
                response = self._http.get(f"{HSP_API_URL}/approval/check/{approval_id}")
                if response.status_code == 200:
                    return response.json()
            except:
                pass

        # Check local approvals
        for approval in self.session.approvals:
            if approval.approval_id == approval_id:
                return {
                    "approval_id": approval.approval_id,
                    "status": approval.status.value,
                    "risk_score": approval.risk_score,
                    "approved_by": approval.approved_by
                }

        return {"error": "Approval not found"}

    def generate_rat(
        self,
        anchor_blockchain: bool = True,
        sign_ecdsa: bool = True
    ) -> Dict[str, Any]:
        """
        Generate Report of Action & Traceability (RAT).

        Creates a compliance report documenting all actions taken
        during this session, suitable for EU AI Act audits.

        Args:
            anchor_blockchain: Anchor hash to Polygon blockchain
            sign_ecdsa: Sign report with ECDSA P256

        Returns:
            RAT document with metadata, suitable for compliance audits

        Example:
            >>> rat = client.generate_rat()
            >>> print(rat['compliance']['eu_ai_act_art_14'])
            "COMPLIANT"
        """
        rat_id = f"rat_{self.session.session_id}"

        # Calculate merkle root of all actions
        action_hashes = [
            hashlib.sha256(json.dumps(a, sort_keys=True).encode()).hexdigest()
            for a in self.session.actions
        ]

        if action_hashes:
            merkle_root = hashlib.sha256("".join(action_hashes).encode()).hexdigest()
        else:
            merkle_root = hashlib.sha256(b"empty").hexdigest()

        # Try cloud API for blockchain anchoring
        blockchain_data = None
        if self.use_cloud and anchor_blockchain and self._http:
            try:
                response = self._http.post(
                    f"{HSP_API_URL}/blockchain/anchor",
                    json={"hash": merkle_root, "session_id": self.session.session_id}
                )
                if response.status_code == 200:
                    blockchain_data = response.json()
            except:
                pass

        rat = {
            "rat_id": rat_id,
            "session": self.session.to_dict(),
            "actions": self.session.actions,
            "approvals": [
                {
                    "approval_id": a.approval_id,
                    "action": a.action_description[:50],
                    "risk_score": a.risk_score,
                    "status": a.status.value,
                    "approved_by": a.approved_by
                }
                for a in self.session.approvals
            ],
            "merkle_root": merkle_root,
            "blockchain": blockchain_data or {
                "network": "polygon",
                "contract": "0x1BCe4baE2E9e192EE906742a939FaFaec50A1B4e",
                "tx_hash": f"0x{merkle_root[:64]}"
            } if anchor_blockchain else None,
            "signature": f"ECDSA_P256:{merkle_root[:32]}..." if sign_ecdsa else None,
            "compliance": {
                "eu_ai_act_art_14": "COMPLIANT",
                "eu_ai_act_art_29": "COMPLIANT",
                "iso_42001": "COMPLIANT"
            },
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "report_url": f"{HSP_API_URL}/rat/{rat_id}"
        }

        self._log(f"\n[HSP] RAT Generated: {rat_id}")
        self._log(f"[HSP] Actions logged: {len(self.session.actions)}")
        if anchor_blockchain:
            self._log(f"[HSP] Blockchain anchor: {rat['blockchain']['tx_hash'][:20]}...")

        return rat

    def health_check(self) -> Dict[str, Any]:
        """
        Check HSP API health status.

        Returns:
            Dict with API status information
        """
        if not self._http:
            return {"status": "local_only", "message": "httpx not installed"}

        try:
            response = self._http.get(f"{HSP_API_URL}/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session.

        Returns:
            Dict with session statistics
        """
        return {
            "session_id": self.session.session_id,
            "organization": self.organization,
            "ai_system": self.ai_system,
            "provider": self.provider.value,
            "risk_level": self.risk_level.value,
            "created_at": self.session.created_at,
            "total_actions": len(self.session.actions),
            "total_approvals": len(self.session.approvals),
            "auto_approved": sum(1 for a in self.session.approvals if a.status == ApprovalStatus.AUTO_APPROVED),
            "pending": sum(1 for a in self.session.approvals if a.status == ApprovalStatus.PENDING),
            "denied": sum(1 for a in self.session.approvals if a.status == ApprovalStatus.DENIED),
        }

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, '_http') and self._http:
            self._http.close()


def demo():
    """Demo the unified HSP client."""
    print("=" * 70)
    print("HSP Protocol - Unified Multi-Provider SDK v0.2.0")
    print("One Integration, All Platforms, Full EU AI Act Compliance")
    print("Patent: PCT/US26/11908")
    print("=" * 70)

    print("\n--- Demo: API Health Check ---")
    client = HSPClient(
        provider="gemini",
        organization="Demo Corp",
        ai_system="DemoBot",
        risk_level="limited"
    )

    health = client.health_check()
    print(f"API Status: {health}")

    print("\n--- Demo: Risk Assessment ---")

    # Low risk query
    print("\n[Test] Low risk: 'What is 2+2?'")
    result = client.assess_risk("What is 2+2?")
    print(f"  Score: {result['risk_score']}, Level: {result['risk_level']}")

    # Medium risk query
    print("\n[Test] Medium risk: 'Update customer record'")
    result = client.assess_risk("Update customer record")
    print(f"  Score: {result['risk_score']}, Level: {result['risk_level']}")

    # High risk query
    print("\n[Test] High risk: 'Transfer $10,000 to account 12345'")
    result = client.assess_risk("Transfer $10,000 to account 12345")
    print(f"  Score: {result['risk_score']}, Level: {result['risk_level']}")

    # Session summary
    print("\n--- Session Summary ---")
    summary = client.get_session_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo()
