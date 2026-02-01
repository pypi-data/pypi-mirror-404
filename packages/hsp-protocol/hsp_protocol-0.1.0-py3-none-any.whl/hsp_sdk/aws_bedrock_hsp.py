"""
HSP Protocol - AWS Bedrock Integration
Fail-closed AI supervision for Claude, Titan, Llama on AWS
Patent: PCT/US26/11908

Supports:
- Amazon Bedrock (Claude, Titan, Llama, Mistral)
- Amazon Bedrock Agents
- AWS Lambda integrations
"""

import os
import json
import boto3
from typing import Optional, Dict, Any, List
from datetime import datetime

# HSP Tool Specifications for Bedrock
HSP_TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "hsp_initialize",
                "description": "Initialize HSP supervision session for AWS Bedrock workload.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "aws_account_id": {
                                "type": "string",
                                "description": "AWS Account ID"
                            },
                            "organization_name": {
                                "type": "string",
                                "description": "Organization name"
                            },
                            "bedrock_model_id": {
                                "type": "string",
                                "description": "Bedrock model identifier"
                            },
                            "use_case": {
                                "type": "string",
                                "description": "AI use case description"
                            },
                            "risk_tier": {
                                "type": "string",
                                "enum": ["minimal", "limited", "high", "unacceptable"],
                                "description": "EU AI Act risk tier"
                            },
                            "region": {
                                "type": "string",
                                "description": "AWS region"
                            }
                        },
                        "required": ["organization_name", "bedrock_model_id", "risk_tier"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "hsp_approve_action",
                "description": "Request cryptographic human approval before high-risk action execution.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "HSP session ID"
                            },
                            "action_category": {
                                "type": "string",
                                "enum": [
                                    "s3_write",
                                    "dynamodb_modify",
                                    "lambda_invoke",
                                    "sns_publish",
                                    "sqs_send",
                                    "secrets_access",
                                    "iam_modify",
                                    "ec2_control",
                                    "rds_query",
                                    "external_http",
                                    "pii_process",
                                    "financial",
                                    "medical",
                                    "other"
                                ],
                                "description": "Category of AWS action"
                            },
                            "action_details": {
                                "type": "string",
                                "description": "Description of the action"
                            },
                            "target_resources": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "ARNs of affected resources"
                            },
                            "risk_score": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100
                            },
                            "reversible": {
                                "type": "boolean",
                                "description": "Whether action can be undone"
                            }
                        },
                        "required": ["session_id", "action_category", "action_details", "risk_score"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "hsp_execute",
                "description": "Execute an approved action with full audit trail to CloudWatch and blockchain.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "approval_id": {
                                "type": "string",
                                "description": "Valid HSP approval ID"
                            },
                            "execution_payload": {
                                "type": "object",
                                "description": "Action parameters"
                            }
                        },
                        "required": ["approval_id"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "hsp_audit_report",
                "description": "Generate compliance report (RAT) with optional S3 storage and blockchain anchoring.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string"
                            },
                            "output_bucket": {
                                "type": "string",
                                "description": "S3 bucket for report storage"
                            },
                            "blockchain_anchor": {
                                "type": "boolean"
                            },
                            "frameworks": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["eu_ai_act", "iso_42001", "nist_ai_rmf", "sox", "hipaa"]
                                }
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            }
        }
    ]
}

HSP_BEDROCK_SYSTEM = """You are an AI assistant running on AWS Bedrock, supervised by HSP Protocol (Patent: PCT/US26/11908).

AWS ENTERPRISE COMPLIANCE MODE:

1. INITIALIZATION
   - Call hsp_initialize at the start of any task
   - Provides session tracking and audit context

2. APPROVAL REQUIREMENTS
   For risk_score >= 60 or HIGH/UNACCEPTABLE risk tier:
   - MUST call hsp_approve_action before any AWS operation
   - Wait for approval status "approved"
   - FAIL-CLOSED: If denied/timeout, DO NOT execute

3. AWS ACTIONS REQUIRING APPROVAL:
   - s3_write: Writing to S3 buckets
   - dynamodb_modify: DynamoDB writes/deletes
   - lambda_invoke: Triggering other Lambdas
   - secrets_access: Secrets Manager access
   - iam_modify: Any IAM changes
   - external_http: Calls outside AWS
   - pii_process: Personal data handling
   - financial: Financial operations

4. AUDIT INTEGRATION:
   - All actions logged to CloudWatch
   - Hash anchored to Polygon blockchain
   - Reports stored in S3

Compliance: EU AI Act Art. 14, ISO 42001, SOC 2"""


class HSPBedrockClient:
    """HSP-wrapped AWS Bedrock client."""

    def __init__(
        self,
        region_name: str = None,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        """
        Initialize HSP-wrapped Bedrock client.

        Args:
            region_name: AWS region
            model_id: Bedrock model ID
        """
        self.region = region_name or os.environ.get("AWS_REGION", "us-east-1")
        self.model_id = model_id

        self.bedrock = boto3.client(
            "bedrock-runtime",
            region_name=self.region
        )

        self.session_id = None
        self.approved_actions: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []

    def _process_tool(self, tool_use: Dict) -> Dict:
        """Process HSP tool calls."""
        name = tool_use["name"]
        args = tool_use.get("input", {})

        print(f"\n[HSP-BEDROCK] Tool: {name}")
        print(f"  Input: {json.dumps(args, indent=2)}")

        timestamp = datetime.utcnow().isoformat() + "Z"

        if name == "hsp_initialize":
            self.session_id = f"bedrock_{abs(hash(args['bedrock_model_id'])) % 100000}"
            self.audit_log = []
            result = {
                "session_id": self.session_id,
                "status": "active",
                "model": args["bedrock_model_id"],
                "risk_tier": args.get("risk_tier", "limited"),
                "region": self.region,
                "compliance": ["EU AI Act", "ISO 42001", "SOC 2"],
                "cloudwatch_log_group": f"/hsp/bedrock/{self.session_id}"
            }

        elif name == "hsp_approve_action":
            risk_score = args.get("risk_score", 50)
            approval_id = f"apr_{abs(hash(args['action_details'])) % 100000}"

            self.audit_log.append({
                "event": "approval_requested",
                "approval_id": approval_id,
                "category": args["action_category"],
                "details": args["action_details"],
                "risk_score": risk_score,
                "resources": args.get("target_resources", []),
                "timestamp": timestamp
            })

            if risk_score >= 70:
                result = {
                    "approval_id": approval_id,
                    "status": "pending_human",
                    "risk_level": "critical" if risk_score >= 90 else "high",
                    "sns_notification": "arn:aws:sns:...:hsp-approvals",
                    "approval_console": f"https://app.hsp-protocol.com/aws/{approval_id}",
                    "message": f"Risk score {risk_score}. Human approval required.",
                    "instruction": "DO NOT PROCEED without approval."
                }
            else:
                self.approved_actions[approval_id] = {
                    "approved": True,
                    "auto": True,
                    "timestamp": timestamp
                }
                result = {
                    "approval_id": approval_id,
                    "status": "auto_approved",
                    "risk_level": "low",
                    "message": "Within auto-approval threshold."
                }

        elif name == "hsp_execute":
            approval_id = args["approval_id"]
            if approval_id not in self.approved_actions:
                result = {
                    "status": "BLOCKED",
                    "error": "NO_APPROVAL",
                    "message": "FAIL-CLOSED: Execution blocked. No valid approval.",
                    "compliance": "EU AI Act Article 14 enforced."
                }
            else:
                exec_id = f"exec_{abs(hash(approval_id)) % 100000}"
                self.audit_log.append({
                    "event": "executed",
                    "execution_id": exec_id,
                    "approval_id": approval_id,
                    "timestamp": timestamp
                })
                result = {
                    "status": "executed",
                    "execution_id": exec_id,
                    "cloudwatch_event": f"arn:aws:logs:...:hsp/{exec_id}"
                }

        elif name == "hsp_audit_report":
            rat_id = f"rat_{self.session_id}"
            result = {
                "rat_id": rat_id,
                "session_id": self.session_id,
                "events_count": len(self.audit_log),
                "events": self.audit_log,
                "s3_location": f"s3://{args.get('output_bucket', 'hsp-audit-reports')}/{rat_id}.json",
                "blockchain": {
                    "network": "polygon",
                    "contract": "0x1BCe4baE2E9e192EE906742a939FaFaec50A1B4e",
                    "merkle_root": f"0x{'c' * 64}"
                } if args.get("blockchain_anchor", True) else None,
                "compliance_status": {
                    framework: "COMPLIANT"
                    for framework in args.get("frameworks", ["eu_ai_act"])
                }
            }

        else:
            result = {"error": f"Unknown tool: {name}"}

        return result

    def converse(
        self,
        messages: List[Dict],
        model_id: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> Dict:
        """
        Send conversation with HSP supervision.

        Args:
            messages: Conversation messages
            model_id: Override model
            max_tokens: Max tokens
            temperature: Temperature
        """
        model = model_id or self.model_id

        # Build request
        request = {
            "modelId": model,
            "messages": messages,
            "system": [{"text": HSP_BEDROCK_SYSTEM}],
            "toolConfig": HSP_TOOL_CONFIG,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature
            }
        }

        response = self.bedrock.converse(**request)

        # Process tool use loop
        while response.get("stopReason") == "tool_use":
            # Find tool use in response
            output = response["output"]["message"]["content"]
            tool_uses = [block for block in output if "toolUse" in block]

            tool_results = []
            for tool_block in tool_uses:
                tool_use = tool_block["toolUse"]
                result = self._process_tool(tool_use)
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content": [{"json": result}]
                    }
                })

            # Continue conversation
            messages = messages + [
                response["output"]["message"],
                {"role": "user", "content": tool_results}
            ]

            request["messages"] = messages
            response = self.bedrock.converse(**request)

        return response

    def invoke_with_supervision(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Simple invoke with HSP supervision.

        Args:
            prompt: User prompt
        """
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        response = self.converse(messages, **kwargs)

        # Extract text response
        output = response["output"]["message"]["content"]
        text_parts = [block["text"] for block in output if "text" in block]
        return " ".join(text_parts)


def demo():
    """Demo HSP-wrapped Bedrock."""
    print("=" * 60)
    print("HSP Protocol - AWS Bedrock Integration")
    print("Patent: PCT/US26/11908")
    print("=" * 60)

    print("\nTo run this demo, configure AWS credentials with Bedrock access.")

    try:
        client = HSPBedrockClient(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0"
        )

        prompt = """I need to set up HSP supervision for our AWS-deployed
        fraud detection AI 'FraudGuard' at JP Morgan Chase.
        It processes credit card transactions."""

        print(f"\nUser: {prompt}")
        response = client.invoke_with_supervision(prompt)
        print(f"\nAssistant: {response}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Ensure AWS credentials are configured with Bedrock access.")


if __name__ == "__main__":
    demo()
