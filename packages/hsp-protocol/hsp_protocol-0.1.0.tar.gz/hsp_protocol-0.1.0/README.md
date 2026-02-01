# HSP Protocol SDK

**Fail-Closed AI Supervision for EU AI Act Compliance**

[![Patent](https://img.shields.io/badge/Patent-PCT%2FUS26%2F11908-blue)](https://hsp-protocol.com/patent)
[![License](https://img.shields.io/badge/License-Proprietary-red)](https://hsp-protocol.com/license)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green)](https://python.org)

## Overview

HSP Protocol provides the **only patented fail-closed architecture** for AI agent supervision that ensures EU AI Act Article 14 compliance.

Unlike probabilistic safety filters (RLHF, guardrails) that **fail open**, HSP implements cryptographic pre-execution approval that **fails closed** — no approval, no execution.

## Supported Providers

| Provider | Package | Status |
|----------|---------|--------|
| Google Gemini | `hsp-protocol[gemini]` | ✅ Production |
| OpenAI GPT | `hsp-protocol[openai]` | ✅ Production |
| Azure OpenAI | `hsp-protocol[openai]` | ✅ Production |
| Anthropic Claude | `hsp-protocol[anthropic]` | ✅ Production |
| AWS Bedrock | `hsp-protocol[bedrock]` | ✅ Production |

## Installation

```bash
# Core (minimal)
pip install hsp-protocol

# With specific provider
pip install hsp-protocol[gemini]
pip install hsp-protocol[openai]
pip install hsp-protocol[anthropic]
pip install hsp-protocol[bedrock]

# All providers
pip install hsp-protocol[all]
```

## Quick Start

```python
from hsp_sdk import HSPClient

# Initialize with any provider
client = HSPClient(
    provider="gemini",           # or "openai", "azure", "anthropic", "bedrock"
    organization="Acme Corp",
    ai_system="CustomerBot",
    risk_level="high"            # EU AI Act classification
)

# All interactions are now supervised
response = client.chat("Process refund for order #12345")

# Generate compliance report (RAT)
rat = client.generate_rat(anchor_blockchain=True)
print(f"Report: {rat['report_url']}")
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR AI AGENT                        │
│                         │                               │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │   HSP INTERCEPTOR   │ ◄── Patented       │
│              │   (Fail-Closed)     │                    │
│              └─────────────────────┘                    │
│                         │                               │
│         ┌───────────────┼───────────────┐               │
│         ▼               ▼               ▼               │
│   [Risk Score]   [Human Approval]  [Crypto Sign]        │
│         │               │               │               │
│         └───────────────┼───────────────┘               │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │  IMMUTABLE LEDGER   │ ◄── Polygon        │
│              │  (Proof of Superv.) │                    │
│              └─────────────────────┘                    │
│                         │                               │
│                         ▼                               │
│                 [EXECUTE / BLOCK]                       │
└─────────────────────────────────────────────────────────┘
```

## Risk-Based Approval

| Risk Score | Action | Quorum |
|------------|--------|--------|
| 0-40 | Auto-approve + log | 0 |
| 41-70 | Single human approval | 1 |
| 71-90 | Multi-sig approval | 2 |
| 91-100 | Critical review | 3+ |

## Provider-Specific Usage

### Google Gemini / Vertex AI

```python
from hsp_sdk import HSPClient

client = HSPClient(
    provider="gemini",
    organization="HealthPlus",
    ai_system="MedicalDiagnosis",
    api_key="your-gemini-key"  # or GOOGLE_API_KEY env var
)
```

### OpenAI

```python
client = HSPClient(
    provider="openai",
    organization="TradingCo",
    ai_system="AlphaTrader"
    # Uses OPENAI_API_KEY env var
)
```

### Azure OpenAI

```python
client = HSPClient(
    provider="azure",
    organization="Enterprise",
    ai_system="CopilotCustom",
    azure_endpoint="https://myresource.openai.azure.com/",
    deployment="gpt-4o"
)
```

### Anthropic Claude

```python
client = HSPClient(
    provider="anthropic",
    organization="LegalFirm",
    ai_system="ContractReview"
)
```

### AWS Bedrock

```python
client = HSPClient(
    provider="bedrock",
    organization="FinanceOrg",
    ai_system="FraudDetector",
    region="us-east-1"
)
```

## Compliance Reports (RAT)

Generate a Report of Action & Traceability:

```python
rat = client.generate_rat(
    anchor_blockchain=True,  # Polygon anchoring
    sign_ecdsa=True          # Cryptographic signature
)

print(rat)
# {
#   "rat_id": "rat_hsp_abc123",
#   "actions": [...],
#   "approvals": [...],
#   "blockchain": {
#     "network": "polygon",
#     "contract": "0x1BCe4baE...",
#     "tx_hash": "0x..."
#   },
#   "compliance": {
#     "eu_ai_act_art_14": "COMPLIANT",
#     "iso_42001": "COMPLIANT"
#   }
# }
```

## EU AI Act Compliance

HSP Protocol directly implements:

- **Article 14**: Human oversight with pre-execution approval
- **Article 29**: Transparency via immutable audit logs
- **Article 9**: Risk management through dynamic risk scoring
- **Annex IV**: Technical documentation via RAT reports

## Pricing

| Tier | Transactions/Month | Price |
|------|-------------------|-------|
| Starter | 10,000 | €499/mo |
| Business | 100,000 | €2,499/mo |
| Enterprise | Unlimited | €9,999/mo |

[Contact Sales](mailto:sales@hsp-protocol.com)

## Patent Information

HSP Protocol is protected by international patent:

- **PCT/US26/11908** (Priority Date: 2024)
- USPTO Pending: 63/948,692
- National phase entries: EP, CN, JP (2026-2027)

Commercial use requires licensing. [Learn more](https://hsp-protocol.com/license)

## Support

- Documentation: https://docs.hsp-protocol.com
- Email: support@hsp-protocol.com
- Enterprise: enterprise@hsp-protocol.com

---

**HSP Protocol** — *The only architecture that makes AI compliance defensible.*

Patent PCT/US26/11908 | © 2024-2026 Jaqueline de Jesus
