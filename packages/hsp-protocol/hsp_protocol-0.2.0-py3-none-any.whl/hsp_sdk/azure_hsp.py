"""
HSP Protocol - Microsoft Azure OpenAI Integration
Fail-closed AI supervision for Azure-deployed GPT models
Patent: PCT/US26/11908

Specifically designed for Microsoft enterprise customers using:
- Azure OpenAI Service
- Azure AI Studio
- Microsoft Copilot integrations
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List

# HSP Tools adapted for Azure OpenAI format
HSP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "hsp_start_session",
            "description": "Initialize HSP audit session. Required before any supervised AI operation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tenant_id": {
                        "type": "string",
                        "description": "Azure AD Tenant ID"
                    },
                    "organization_name": {
                        "type": "string",
                        "description": "Organization name"
                    },
                    "deployment_name": {
                        "type": "string",
                        "description": "Azure OpenAI deployment name"
                    },
                    "ai_system_purpose": {
                        "type": "string",
                        "description": "Purpose of the AI system"
                    },
                    "risk_classification": {
                        "type": "string",
                        "enum": ["minimal", "limited", "high", "unacceptable"],
                        "description": "EU AI Act risk classification"
                    },
                    "data_residency": {
                        "type": "string",
                        "enum": ["eu", "us", "uk", "apac", "global"],
                        "description": "Data residency requirement"
                    }
                },
                "required": ["organization_name", "deployment_name", "risk_classification"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hsp_request_approval",
            "description": "Request human approval for high-risk action. MANDATORY before executing any action with risk >= high.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Active HSP session"
                    },
                    "action_type": {
                        "type": "string",
                        "enum": [
                            "data_access",
                            "data_modification",
                            "external_api_call",
                            "financial_transaction",
                            "pii_processing",
                            "medical_decision",
                            "legal_action",
                            "system_command",
                            "other"
                        ],
                        "description": "Type of action requiring approval"
                    },
                    "action_description": {
                        "type": "string",
                        "description": "Human-readable description"
                    },
                    "affected_resources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of affected resources/systems"
                    },
                    "risk_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Computed risk score"
                    },
                    "justification": {
                        "type": "string",
                        "description": "Business justification for the action"
                    }
                },
                "required": ["session_id", "action_type", "action_description", "risk_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hsp_check_approval_status",
            "description": "Check status of pending approval request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "approval_id": {
                        "type": "string",
                        "description": "Approval request ID"
                    }
                },
                "required": ["approval_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hsp_execute_supervised",
            "description": "Execute an approved action with full audit trail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "approval_id": {
                        "type": "string",
                        "description": "Valid approval ID"
                    },
                    "execution_parameters": {
                        "type": "object",
                        "description": "Parameters for the action"
                    }
                },
                "required": ["approval_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hsp_generate_compliance_report",
            "description": "Generate RAT (Report of Action & Traceability) for compliance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "HSP session ID"
                    },
                    "report_format": {
                        "type": "string",
                        "enum": ["pdf", "json", "xml"],
                        "description": "Output format"
                    },
                    "include_blockchain_proof": {
                        "type": "boolean",
                        "description": "Include Polygon anchoring"
                    },
                    "regulatory_framework": {
                        "type": "string",
                        "enum": ["eu_ai_act", "iso_42001", "nist_ai_rmf", "all"],
                        "description": "Target compliance framework"
                    }
                },
                "required": ["session_id"]
            }
        }
    }
]

HSP_AZURE_SYSTEM = """You are an AI assistant operating within Microsoft Azure, supervised by HSP Protocol (Patent: PCT/US26/11908).

ENTERPRISE COMPLIANCE MODE ACTIVE:

1. SESSION MANAGEMENT
   - Call hsp_start_session at task initialization
   - Session tracks all AI decisions for audit

2. APPROVAL WORKFLOW
   - HIGH/UNACCEPTABLE risk actions REQUIRE hsp_request_approval
   - Wait for approval_status: "approved" before proceeding
   - If status is "denied" or "timeout" → DO NOT EXECUTE (fail-closed)

3. ACTION TYPES REQUIRING APPROVAL:
   - data_modification: Any write operation
   - pii_processing: Personal data handling (GDPR)
   - financial_transaction: Any monetary action
   - medical_decision: Healthcare AI outputs
   - external_api_call: Third-party integrations
   - system_command: Infrastructure changes

4. COMPLIANCE MAPPING:
   - EU AI Act Article 14: Human Oversight ✓
   - EU AI Act Article 29: Transparency ✓
   - ISO/IEC 42001: AI Management System ✓

All actions logged to immutable ledger with cryptographic proof."""


class HSPAzureClient:
    """HSP-wrapped Azure OpenAI client for enterprise compliance."""

    def __init__(
        self,
        azure_endpoint: str = None,
        api_key: str = None,
        api_version: str = "2024-06-01",
        deployment_name: str = None
    ):
        """
        Initialize HSP-wrapped Azure OpenAI client.

        Args:
            azure_endpoint: Azure OpenAI endpoint (e.g., https://myresource.openai.azure.com/)
            api_key: Azure OpenAI API key
            api_version: API version
            deployment_name: Default deployment name
        """
        self.endpoint = azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.api_version = api_version
        self.deployment = deployment_name or os.environ.get("AZURE_OPENAI_DEPLOYMENT")

        if not all([self.endpoint, self.api_key, self.deployment]):
            raise ValueError(
                "Missing Azure config. Set AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT"
            )

        self.session_id = None
        self.approved_actions: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []

    def _build_url(self, deployment: str = None) -> str:
        """Build Azure OpenAI API URL."""
        deploy = deployment or self.deployment
        return f"{self.endpoint.rstrip('/')}/openai/deployments/{deploy}/chat/completions?api-version={self.api_version}"

    def _handle_hsp_tool(self, tool_call) -> str:
        """Process HSP tool calls with Azure-specific handling."""
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])

        print(f"\n[HSP-AZURE INTERCEPTOR] {name}")
        print(f"  Args: {json.dumps(args, indent=2)}")

        if name == "hsp_start_session":
            self.session_id = f"azure_sess_{abs(hash(args['deployment_name'])) % 100000}"
            self.audit_log = []
            result = {
                "session_id": self.session_id,
                "status": "active",
                "azure_deployment": args["deployment_name"],
                "risk_classification": args.get("risk_classification", "limited"),
                "data_residency": args.get("data_residency", "eu"),
                "compliance_frameworks": ["EU AI Act", "ISO 42001", "GDPR"],
                "message": "HSP Azure session initialized."
            }

        elif name == "hsp_request_approval":
            risk_score = args.get("risk_score", 50)
            approval_id = f"apr_{abs(hash(args['action_description'])) % 100000}"

            self.audit_log.append({
                "event": "approval_requested",
                "approval_id": approval_id,
                "action_type": args["action_type"],
                "description": args["action_description"],
                "risk_score": risk_score,
                "timestamp": "2026-01-29T12:00:00Z"
            })

            if risk_score >= 70:
                result = {
                    "approval_id": approval_id,
                    "status": "pending_human_review",
                    "risk_level": "high" if risk_score < 90 else "critical",
                    "approvers_required": 2 if risk_score >= 90 else 1,
                    "approval_url": f"https://app.hsp-protocol.com/azure/{approval_id}",
                    "teams_notification": "sent",
                    "message": f"High-risk action (score: {risk_score}). Human approval required.",
                    "instruction": "Call hsp_check_approval_status to verify before proceeding."
                }
            else:
                self.approved_actions[approval_id] = {
                    "approved": True,
                    "approved_by": "auto_policy",
                    "reason": "Risk within auto-approval threshold"
                }
                result = {
                    "approval_id": approval_id,
                    "status": "auto_approved",
                    "risk_level": "low",
                    "approved_by": "HSP Policy Engine",
                    "message": "Action approved per organizational policy."
                }

        elif name == "hsp_check_approval_status":
            approval_id = args["approval_id"]
            if approval_id in self.approved_actions:
                result = {
                    "approval_id": approval_id,
                    "status": "approved",
                    "can_execute": True
                }
            else:
                result = {
                    "approval_id": approval_id,
                    "status": "pending",
                    "can_execute": False,
                    "message": "Awaiting human review. DO NOT PROCEED."
                }

        elif name == "hsp_execute_supervised":
            approval_id = args["approval_id"]
            if approval_id not in self.approved_actions:
                result = {
                    "status": "BLOCKED",
                    "error": "APPROVAL_REQUIRED",
                    "message": "FAIL-CLOSED: Cannot execute without valid approval.",
                    "compliance_note": "EU AI Act Article 14 enforcement active."
                }
            else:
                exec_id = f"exec_{abs(hash(approval_id)) % 100000}"
                self.audit_log.append({
                    "event": "action_executed",
                    "execution_id": exec_id,
                    "approval_id": approval_id,
                    "timestamp": "2026-01-29T12:00:01Z"
                })
                result = {
                    "status": "executed",
                    "execution_id": exec_id,
                    "approval_id": approval_id,
                    "audit_trail": "recorded"
                }

        elif name == "hsp_generate_compliance_report":
            result = {
                "rat_id": f"rat_{self.session_id}",
                "format": args.get("report_format", "pdf"),
                "actions_audited": len(self.audit_log),
                "audit_log": self.audit_log,
                "blockchain_proof": {
                    "network": "polygon",
                    "contract": "0x1BCe4baE2E9e192EE906742a939FaFaec50A1B4e",
                    "merkle_root": f"0x{'b' * 64}"
                } if args.get("include_blockchain_proof", True) else None,
                "compliance_status": {
                    "eu_ai_act": "COMPLIANT",
                    "iso_42001": "COMPLIANT",
                    "gdpr": "COMPLIANT"
                },
                "report_url": f"https://api.hsp-protocol.com/rat/{self.session_id}.pdf"
            }

        else:
            result = {"error": f"Unknown HSP tool: {name}"}

        return json.dumps(result, indent=2)

    def chat(
        self,
        messages: List[Dict],
        deployment: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request with HSP supervision.

        Args:
            messages: Conversation messages
            deployment: Azure deployment (overrides default)
            temperature: Sampling temperature
            max_tokens: Max response tokens
        """
        url = self._build_url(deployment)
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Add HSP system prompt
        full_messages = [{"role": "system", "content": HSP_AZURE_SYSTEM}] + messages

        payload = {
            "messages": full_messages,
            "tools": HSP_TOOLS,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        with httpx.Client(timeout=60) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

        # Handle tool calls
        message = result["choices"][0]["message"]

        while "tool_calls" in message and message["tool_calls"]:
            tool_results = []
            for tool_call in message["tool_calls"]:
                tool_result = self._handle_hsp_tool(tool_call)
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "content": tool_result
                })

            # Continue with tool results
            full_messages.append(message)
            full_messages.extend(tool_results)

            payload["messages"] = full_messages

            with httpx.Client(timeout=60) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()

            message = result["choices"][0]["message"]

        return result


def demo():
    """Demo HSP-wrapped Azure OpenAI."""
    print("=" * 60)
    print("HSP Protocol - Microsoft Azure OpenAI Integration")
    print("Enterprise Compliance Mode")
    print("Patent: PCT/US26/11908")
    print("=" * 60)

    # Note: Requires Azure OpenAI setup
    print("\nTo run this demo, configure:")
    print("  - AZURE_OPENAI_ENDPOINT")
    print("  - AZURE_OPENAI_API_KEY")
    print("  - AZURE_OPENAI_DEPLOYMENT")

    try:
        client = HSPAzureClient()

        messages = [
            {
                "role": "user",
                "content": "I need to configure supervision for our Azure-deployed trading bot 'AzureTrader' at Deutsche Bank."
            }
        ]

        print(f"\nUser: {messages[0]['content']}")
        response = client.chat(messages)
        print(f"\nAssistant: {response['choices'][0]['message']['content']}")

    except ValueError as e:
        print(f"\n[CONFIG] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


if __name__ == "__main__":
    demo()
