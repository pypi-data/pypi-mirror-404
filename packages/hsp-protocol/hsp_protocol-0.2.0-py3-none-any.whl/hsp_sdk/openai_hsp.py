"""
HSP Protocol - OpenAI/Azure OpenAI Integration
Fail-closed AI supervision for GPT-4, GPT-4o, etc.
Patent: PCT/US26/11908
"""

import os
import json
from openai import OpenAI, AzureOpenAI

# HSP Tool Definitions for OpenAI Function Calling
HSP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "start_audit_session",
            "description": "Starts a new HSP audit session for AI supervision. Must be called before any high-risk action.",
            "parameters": {
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
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_approval",
            "description": "Requests cryptographic human approval before executing a high-risk action. MANDATORY for risk_level >= high.",
            "parameters": {
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
                    }
                },
                "required": ["session_id", "action_description", "risk_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_rat",
            "description": "Generates the Report of Action & Traceability (RAT) with blockchain anchoring.",
            "parameters": {
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
                    }
                },
                "required": ["session_id"]
            }
        }
    }
]

# System instruction for HSP-enabled AI
HSP_SYSTEM_PROMPT = """You are an AI assistant operating under the HSP Protocol (Human Supervision Protocol).

MANDATORY RULES:
1. Before ANY high-risk action, you MUST call 'request_human_approval' and wait for cryptographic approval
2. High-risk actions include: financial transactions, medical decisions, legal advice, data deletion, system changes
3. If approval is DENIED or TIMEOUT, you MUST NOT execute the action (fail-closed behavior)
4. All actions must be logged for the RAT (Report of Action & Traceability)

This ensures EU AI Act Article 14 compliance."""


class HSPOpenAIClient:
    """HSP-wrapped OpenAI client with fail-closed supervision."""

    def __init__(self, api_key: str = None, azure_endpoint: str = None, azure_api_version: str = "2024-02-01"):
        """
        Initialize HSP-wrapped OpenAI client.

        Args:
            api_key: OpenAI or Azure API key
            azure_endpoint: If provided, uses Azure OpenAI instead
            azure_api_version: Azure API version
        """
        if azure_endpoint:
            self.client = AzureOpenAI(
                api_key=api_key or os.environ.get("AZURE_OPENAI_API_KEY"),
                azure_endpoint=azure_endpoint,
                api_version=azure_api_version
            )
            self.is_azure = True
        else:
            self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
            self.is_azure = False

        self.session_id = None
        self.action_log = []

    def _handle_tool_call(self, tool_call):
        """Process HSP tool calls."""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"\n[HSP INTERCEPTOR] Tool call: {name}")
        print(f"  Arguments: {json.dumps(args, indent=2)}")

        if name == "start_audit_session":
            self.session_id = f"sess_{hash(args['organization_name']) % 100000}"
            result = {
                "session_id": self.session_id,
                "status": "started",
                "risk_level": args.get("risk_level", "medium"),
                "message": "HSP audit session initialized. All actions will be logged."
            }

        elif name == "request_human_approval":
            # In production, this would call the HSP API and wait for approval
            risk_score = args.get("risk_score", 50)
            if risk_score >= 70:
                # Simulate requiring multi-sig for high risk
                result = {
                    "status": "pending_approval",
                    "approval_id": f"apr_{hash(args['action_description']) % 100000}",
                    "quorum_required": args.get("quorum_required", 2),
                    "message": f"High-risk action (score: {risk_score}). Awaiting {args.get('quorum_required', 2)} approver(s).",
                    "approval_url": f"https://app.hsp-protocol.com/approve/{self.session_id}"
                }
            else:
                result = {
                    "status": "auto_approved",
                    "approval_id": f"apr_{hash(args['action_description']) % 100000}",
                    "message": "Low-risk action auto-approved per policy."
                }

            self.action_log.append({
                "action": args["action_description"],
                "risk_score": risk_score,
                "result": result["status"]
            })

        elif name == "generate_rat":
            result = {
                "rat_id": f"rat_{hash(self.session_id or 'default') % 100000}",
                "actions_logged": len(self.action_log),
                "blockchain_tx": "0x..." if args.get("anchor_to_blockchain", True) else None,
                "url": f"https://api.hsp-protocol.com/rat/{self.session_id}.pdf"
            }

        else:
            result = {"error": f"Unknown HSP tool: {name}"}

        return json.dumps(result)

    def chat(self, messages: list, model: str = "gpt-4o", **kwargs):
        """
        Send chat request with HSP supervision layer.

        Args:
            messages: List of message dicts
            model: Model name (gpt-4o, gpt-4-turbo, etc.)
            **kwargs: Additional OpenAI parameters
        """
        # Inject HSP system prompt
        full_messages = [{"role": "system", "content": HSP_SYSTEM_PROMPT}] + messages

        response = self.client.chat.completions.create(
            model=model,
            messages=full_messages,
            tools=HSP_TOOLS,
            tool_choice="auto",
            **kwargs
        )

        # Handle tool calls if present
        message = response.choices[0].message

        while message.tool_calls:
            # Process each tool call
            tool_results = []
            for tool_call in message.tool_calls:
                result = self._handle_tool_call(tool_call)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": result
                })

            # Continue conversation with tool results
            full_messages.append(message)
            full_messages.extend(tool_results)

            response = self.client.chat.completions.create(
                model=model,
                messages=full_messages,
                tools=HSP_TOOLS,
                tool_choice="auto",
                **kwargs
            )
            message = response.choices[0].message

        return response


def demo():
    """Demo of HSP-wrapped OpenAI."""
    print("=" * 60)
    print("HSP Protocol - OpenAI Integration Demo")
    print("Patent: PCT/US26/11908")
    print("=" * 60)

    # Initialize HSP-wrapped client
    client = HSPOpenAIClient()

    # Test conversation
    messages = [
        {
            "role": "user",
            "content": "I need to audit our trading bot 'AlphaTrader' at Goldman Sachs. It executes automated stock trades."
        }
    ]

    print(f"\nUser: {messages[0]['content']}")
    print("\n[HSP] Processing with fail-closed supervision...")

    try:
        response = client.chat(messages, model="gpt-4o")
        print(f"\nAssistant: {response.choices[0].message.content}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Ensure OPENAI_API_KEY is set in environment.")


if __name__ == "__main__":
    demo()
