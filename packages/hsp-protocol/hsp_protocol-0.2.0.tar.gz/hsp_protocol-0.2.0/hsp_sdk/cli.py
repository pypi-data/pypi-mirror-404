#!/usr/bin/env python3
"""
HSP Protocol CLI - Command Line Interface
Patent: PCT/US26/11908

Commands:
    hsp health      Check API status
    hsp risk        Assess risk of an action
    hsp audit       Start audit session
    hsp report      Generate compliance report
    hsp version     Show version
"""

import argparse
import json
import sys
from . import __version__
from .unified import HSPClient, HSP_API_URL


def cmd_health(args):
    """Check HSP API health."""
    client = HSPClient(
        provider="gemini",
        organization="CLI",
        ai_system="CLI",
        quiet=True
    )
    result = client.health_check()
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "healthy" else 1


def cmd_risk(args):
    """Assess risk of an action."""
    if not args.action:
        print("Error: --action is required")
        return 1

    client = HSPClient(
        provider="gemini",
        organization=args.org or "CLI",
        ai_system=args.system or "CLI",
        quiet=True
    )

    result = client.assess_risk(args.action)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Action: {result['action']}")
        print(f"Risk Score: {result['risk_score']}/100")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Approval: {result['approval_requirement']}")

    return 0


def cmd_audit(args):
    """Start an audit session."""
    client = HSPClient(
        provider=args.provider or "gemini",
        organization=args.org or "CLI Audit",
        ai_system=args.system or "CLI Session",
        risk_level=args.risk_level or "limited",
        quiet=False
    )

    print("\nSession started. Use Ctrl+C to end and generate report.")
    print("Enter actions to assess (one per line):\n")

    try:
        while True:
            action = input("> ")
            if action.strip():
                result = client.assess_risk(action)
                print(f"  Risk: {result['risk_score']} ({result['risk_level']})")
    except (KeyboardInterrupt, EOFError):
        print("\n\nGenerating compliance report...")
        rat = client.generate_rat()
        print(f"\nReport ID: {rat['rat_id']}")
        print(f"Actions logged: {len(rat['actions'])}")
        print(f"Report URL: {rat['report_url']}")

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(rat, f, indent=2)
            print(f"Report saved to: {args.output}")

    return 0


def cmd_report(args):
    """Generate a compliance report."""
    client = HSPClient(
        provider="gemini",
        organization=args.org or "CLI",
        ai_system=args.system or "CLI",
        quiet=True
    )

    rat = client.generate_rat(
        anchor_blockchain=not args.no_blockchain,
        sign_ecdsa=not args.no_signature
    )

    if args.json:
        print(json.dumps(rat, indent=2))
    else:
        print(f"Report ID: {rat['rat_id']}")
        print(f"Session: {rat['session']['session_id']}")
        print(f"Organization: {rat['session']['organization']}")
        print(f"Actions: {len(rat['actions'])}")
        print(f"Merkle Root: {rat['merkle_root'][:16]}...")
        if rat['blockchain']:
            print(f"Blockchain TX: {rat['blockchain']['tx_hash'][:20]}...")
        print(f"\nCompliance Status:")
        for key, value in rat['compliance'].items():
            print(f"  {key}: {value}")
        print(f"\nReport URL: {rat['report_url']}")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(rat, f, indent=2)
        print(f"\nSaved to: {args.output}")

    return 0


def cmd_version(args):
    """Show version information."""
    print(f"HSP Protocol SDK v{__version__}")
    print(f"API Endpoint: {HSP_API_URL}")
    print("Patent: PCT/US26/11908")
    print("Copyright (c) 2024-2026 Jaqueline de Jesus")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='hsp',
        description='HSP Protocol - AI Governance CLI',
        epilog='Patent: PCT/US26/11908 | https://hsp-protocol.com'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # health command
    health_parser = subparsers.add_parser('health', help='Check API health status')

    # risk command
    risk_parser = subparsers.add_parser('risk', help='Assess risk of an action')
    risk_parser.add_argument('--action', '-a', help='Action to assess')
    risk_parser.add_argument('--org', '-o', help='Organization name')
    risk_parser.add_argument('--system', '-s', help='AI system name')
    risk_parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')

    # audit command
    audit_parser = subparsers.add_parser('audit', help='Start interactive audit session')
    audit_parser.add_argument('--provider', '-p', choices=['gemini', 'openai', 'azure', 'anthropic', 'bedrock'],
                              help='AI provider')
    audit_parser.add_argument('--org', '-o', help='Organization name')
    audit_parser.add_argument('--system', '-s', help='AI system name')
    audit_parser.add_argument('--risk-level', '-r', choices=['minimal', 'limited', 'high', 'unacceptable'],
                              help='Default risk level')
    audit_parser.add_argument('--output', '-O', help='Save report to file')

    # report command
    report_parser = subparsers.add_parser('report', help='Generate compliance report')
    report_parser.add_argument('--org', '-o', help='Organization name')
    report_parser.add_argument('--system', '-s', help='AI system name')
    report_parser.add_argument('--no-blockchain', action='store_true', help='Skip blockchain anchoring')
    report_parser.add_argument('--no-signature', action='store_true', help='Skip ECDSA signature')
    report_parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    report_parser.add_argument('--output', '-O', help='Save report to file')

    # version command
    version_parser = subparsers.add_parser('version', help='Show version information')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        'health': cmd_health,
        'risk': cmd_risk,
        'audit': cmd_audit,
        'report': cmd_report,
        'version': cmd_version,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
