"""
HSP Protocol - Anthropic Claude Integration
Fail-closed AI supervision for Claude 3.5, Claude 4, etc.
Patent: PCT/US26/11908
"""

import os
import json
from anthropic import Anthropic

# HSP Tool Definitions for Claude Tool Use
HSP_TOOLS = [
    {
        "name": "start_audit_session",
        "description": "Starts a new HSP audit session for AI supervision. Must be called before any high-risk action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "organization_name": {
                    "type": "string",
                    "description": "Name of the organization"
                },
                "ai_system_name": {
                    "type": "string",
                    "description": "Name of the AI system being supervised"
                },
                "ai_system_description": {
                    "type": "string",
                    "description": "Brief description of what the AI does"
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Risk classification per EU AI Act"
                }
            },
            "required": ["organization_name", "ai_system_name", "risk_level"]
        }
    },
    {
        "name": "request_human_approval",
        "description": "Requests cryptographic human approval before executing a high-risk action. MANDATORY for risk_level >= high. The AI MUST wait for approval before proceeding.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Active HSP session ID"
                },
                "action_description": {
                    "type": "string",
                    "description": "Description of the action requiring approval"
                },
                "risk_score": {
                    "type": "number",
                    "description": "Risk score 0-100"
                },
                "quorum_required": {
                    "type": "integer",
                    "description": "Number of approvers required (1-5)"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Timeout for approval (default: 300)"
                }
            },
            "required": ["session_id", "action_description", "risk_score"]
        }
    },
    {
        "name": "execute_action",
        "description": "Executes an approved action. Can ONLY be called after request_human_approval returns approved status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "approval_id": {
                    "type": "string",
                    "description": "Approval ID from request_human_approval"
                },
                "action_type": {
                    "type": "string",
                    "description": "Type of action to execute"
                },
                "parameters": {
                    "type": "object",
                    "description": "Action parameters"
                }
            },
            "required": ["approval_id", "action_type"]
        }
    },
    {
        "name": "generate_rat",
        "description": "Generates the Report of Action & Traceability (RAT) with blockchain anchoring for compliance proof.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "HSP session ID"
                },
                "sign_cryptographically": {
                    "type": "boolean",
                    "description": "Whether to sign with ECDSA"
                },
                "anchor_to_blockchain": {
                    "type": "boolean",
                    "description": "Whether to anchor hash to Polygon"
                },
                "include_full_transcript": {
                    "type": "boolean",
                    "description": "Include full conversation in RAT"
                }
            },
            "required": ["session_id"]
        }
    }
]

HSP_SYSTEM_PROMPT = """You are an AI assistant operating under the HSP Protocol (Human Supervision Protocol) - Patent PCT/US26/11908.

MANDATORY COMPLIANCE RULES:
1. You MUST call 'start_audit_session' at the beginning of any task involving sensitive operations
2. Before ANY high-risk action, you MUST call 'request_human_approval' and WAIT for approval
3. High-risk actions include:
   - Financial transactions (any amount)
   - Medical diagnosis or treatment recommendations
   - Legal advice or contract generation
   - Personal data processing
   - System administration commands
   - API calls to external services
   - Database modifications

4. FAIL-CLOSED BEHAVIOR: If approval is DENIED, TIMEOUT, or ERROR, you MUST NOT proceed with the action
5. All actions are logged to immutable ledger for EU AI Act Article 14 compliance

This protocol ensures legally defensible AI operations."""


class HSPAnthropicClient:
    """HSP-wrapped Anthropic client with fail-closed supervision."""

    def __init__(self, api_key: str = None):
        """
        Initialize HSP-wrapped Anthropic client.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.session_id = None
        self.approved_actions = {}
        self.action_log = []

    def _handle_tool_use(self, tool_use):
        """Process HSP tool calls with fail-closed logic."""
        name = tool_use.name
        args = tool_use.input

        print(f"\n[HSP INTERCEPTOR] Tool: {name}")
        print(f"  Input: {json.dumps(args, indent=2)}")

        if name == "start_audit_session":
            self.session_id = f"sess_{abs(hash(args['organization_name'])) % 100000}"
            self.action_log = []
            result = {
                "session_id": self.session_id,
                "status": "active",
                "risk_level": args.get("risk_level", "medium"),
                "organization": args["organization_name"],
                "ai_system": args["ai_system_name"],
                "compliance": ["EU AI Act Art. 14", "ISO 42001"],
                "message": "HSP session initialized. All actions will be supervised."
            }

        elif name == "request_human_approval":
            risk_score = args.get("risk_score", 50)
            action_desc = args["action_description"]
            approval_id = f"apr_{abs(hash(action_desc)) % 100000}"

            # Determine approval based on risk score
            # In production, this calls HSP API and waits for real approval
            if risk_score >= 80:
                # Critical risk - requires multi-sig
                quorum = args.get("quorum_required", 3)
                result = {
                    "status": "pending_multisig",
                    "approval_id": approval_id,
                    "risk_category": "critical",
                    "quorum_required": quorum,
                    "quorum_received": 0,
                    "message": f"CRITICAL RISK ({risk_score}/100). Requires {quorum} approvers.",
                    "approval_url": f"https://app.hsp-protocol.com/approve/{approval_id}",
                    "instruction": "DO NOT PROCEED until approval status is 'approved'"
                }
            elif risk_score >= 50:
                # High risk - single approval with review
                result = {
                    "status": "pending_review",
                    "approval_id": approval_id,
                    "risk_category": "high",
                    "message": f"High risk action ({risk_score}/100). Awaiting human review.",
                    "approval_url": f"https://app.hsp-protocol.com/approve/{approval_id}",
                    "instruction": "Action queued for human review"
                }
                # Simulate approval for demo
                self.approved_actions[approval_id] = True
            else:
                # Low risk - auto-approve with logging
                self.approved_actions[approval_id] = True
                result = {
                    "status": "approved",
                    "approval_id": approval_id,
                    "risk_category": "low",
                    "approved_by": "auto_policy",
                    "message": "Low-risk action auto-approved per organization policy."
                }

            self.action_log.append({
                "timestamp": "2026-01-29T12:00:00Z",
                "action": action_desc,
                "risk_score": risk_score,
                "approval_id": approval_id,
                "status": result["status"]
            })

        elif name == "execute_action":
            approval_id = args["approval_id"]
            if approval_id not in self.approved_actions:
                # FAIL-CLOSED: Block unapproved actions
                result = {
                    "status": "BLOCKED",
                    "error": "ACTION_NOT_APPROVED",
                    "message": "Cannot execute: No valid approval found. This is fail-closed behavior.",
                    "compliance": "EU AI Act Article 14 - Human Oversight"
                }
            else:
                result = {
                    "status": "executed",
                    "approval_id": approval_id,
                    "action_type": args["action_type"],
                    "execution_id": f"exec_{abs(hash(approval_id)) % 100000}",
                    "message": "Action executed with valid HSP approval."
                }

        elif name == "generate_rat":
            result = {
                "rat_id": f"rat_{abs(hash(self.session_id or 'none')) % 100000}",
                "session_id": self.session_id,
                "actions_logged": len(self.action_log),
                "actions": self.action_log,
                "blockchain_anchor": {
                    "network": "polygon",
                    "contract": "0x1BCe4baE2E9e192EE906742a939FaFaec50A1B4e",
                    "tx_hash": f"0x{'a' * 64}"
                } if args.get("anchor_to_blockchain", True) else None,
                "signature": "ECDSA_P256_SHA256:..." if args.get("sign_cryptographically", True) else None,
                "pdf_url": f"https://api.hsp-protocol.com/rat/{self.session_id}.pdf",
                "compliance_status": "EU_AI_ACT_COMPLIANT"
            }

        else:
            result = {"error": f"Unknown HSP tool: {name}"}

        return json.dumps(result, indent=2)

    def chat(self, messages: list, model: str = "claude-sonnet-4-20250514", max_tokens: int = 4096, **kwargs):
        """
        Send chat request with HSP supervision layer.

        Args:
            messages: List of message dicts
            model: Claude model name
            max_tokens: Maximum response tokens
            **kwargs: Additional Anthropic parameters
        """
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=HSP_SYSTEM_PROMPT,
            tools=HSP_TOOLS,
            messages=messages,
            **kwargs
        )

        # Process tool use in a loop until no more tool calls
        while response.stop_reason == "tool_use":
            # Find tool use blocks
            tool_uses = [block for block in response.content if block.type == "tool_use"]

            # Process each tool and build results
            tool_results = []
            for tool_use in tool_uses:
                result = self._handle_tool_use(tool_use)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result
                })

            # Continue conversation with tool results
            messages = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results}
            ]

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=HSP_SYSTEM_PROMPT,
                tools=HSP_TOOLS,
                messages=messages,
                **kwargs
            )

        return response


def demo():
    """Demo of HSP-wrapped Claude."""
    print("=" * 60)
    print("HSP Protocol - Anthropic Claude Integration Demo")
    print("Patent: PCT/US26/11908")
    print("=" * 60)

    client = HSPAnthropicClient()

    messages = [
        {
            "role": "user",
            "content": "I need to set up supervision for our medical imaging AI 'RadAssist' at Mayo Clinic. It analyzes X-rays and suggests diagnoses."
        }
    ]

    print(f"\nUser: {messages[0]['content']}")
    print("\n[HSP] Processing with fail-closed supervision...")

    try:
        response = client.chat(messages)
        # Extract text from response
        text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
        print(f"\nClaude: {' '.join(text_blocks)}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Ensure ANTHROPIC_API_KEY is set in environment.")


if __name__ == "__main__":
    demo()
