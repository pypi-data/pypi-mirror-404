#!/usr/bin/env python3
"""
Risk Mirror CLI - API-Based Safety Scanner
===========================================
Scan prompts and files for PII, secrets, and injection risks.
All scans go through the Risk Mirror API for unified usage tracking.

Usage:
    risk-mirror scan "Your prompt text here"
    risk-mirror scan -f prompt.txt
    risk-mirror scan -f prompt.txt --json
    risk-mirror safe-share "sensitive string"
    risk-mirror safe-share -f secrets.txt --mode full
    risk-mirror --version
"""

import argparse
import json
import os
import sys
from typing import Optional, List

from .client import RiskMirror, RiskMirrorError

CLI_VERSION = "1.0.2"

# Exit codes
EXIT_SAFE = 0
EXIT_RISK = 1
EXIT_ERROR = 2


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="risk-mirror",
        description="Risk Mirror CLI - Deterministic AI Safety Scanner",
        epilog="Examples:\n"
               "  risk-mirror scan \"Check this prompt\"\n"
               "  risk-mirror scan -f prompt.txt --json\n"
               "  RISK_MIRROR_API_KEY=rm_xxx risk-mirror scan \"text\"\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"risk-mirror CLI {CLI_VERSION}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan text or file for safety issues",
        description="Scan text or file for PII, secrets, and prompt injection"
    )
    
    scan_parser.add_argument(
        "text",
        nargs="?",
        help="Text to scan (use -f for file input)"
    )
    
    scan_parser.add_argument(
        "-f", "--file",
        help="File to scan"
    )
    
    scan_parser.add_argument(
        "--api-key", "-k",
        help="API key (or set RISK_MIRROR_API_KEY env var)"
    )
    
    scan_parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    
    scan_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output verdict (for CI/CD)"
    )

    # Safe Share command
    safe_parser = subparsers.add_parser(
        "safe-share",
        help="Generate Safe Share burner text",
        description="Create non-reversible, format-preserving safe share text"
    )

    safe_parser.add_argument(
        "text",
        nargs="?",
        help="Text to transform (use -f for file input)"
    )

    safe_parser.add_argument(
        "-f", "--file",
        help="File to transform"
    )

    safe_parser.add_argument(
        "--mode",
        choices=["full", "selective"],
        default="selective",
        help="Replacement mode (default: selective)"
    )

    safe_parser.add_argument(
        "--no-secrets",
        action="store_true",
        help="Disable secrets replacement in selective mode"
    )

    safe_parser.add_argument(
        "--allow-valid",
        action="store_true",
        help="Allow valid-looking values (disables strict invalid generation)"
    )

    safe_parser.add_argument(
        "--api-key", "-k",
        help="API key (or set RISK_MIRROR_API_KEY env var)"
    )

    safe_parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    safe_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output the safe share text"
    )
    
    return parser


def format_result(result, as_json: bool = False) -> str:
    """Format scan result for display."""
    if as_json:
        return json.dumps({
            "verdict": result.verdict.value if hasattr(result.verdict, 'value') else str(result.verdict),
            "safe_output": result.safe_output,
            "findings_count": len(result.findings) if result.findings else 0,
        }, indent=2)
    
    verdict = result.verdict.value if hasattr(result.verdict, 'value') else str(result.verdict)
    emoji = {"SAFE": "✅", "REVIEW": "⚠️", "BLOCK": "🚨"}.get(verdict, "❓")
    
    lines = [
        f"\n{emoji} Verdict: {verdict}",
    ]
    
    if result.findings:
        lines.append(f"\n📋 Findings ({len(result.findings)}):")
        for f in result.findings:
            lines.append(f"   • {f.get('category', 'unknown')}: {f.get('count', 1)} occurrence(s)")
    
    if result.safe_output and result.safe_output != result.input_text:
        lines.append(f"\n🔒 Safe Output:\n{result.safe_output[:500]}{'...' if len(result.safe_output) > 500 else ''}")
    
    lines.append("\n🔐 Privacy: Stateless scan, no content stored")
    
    return "\n".join(lines)


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    if not parsed.command:
        parser.print_help()
        return EXIT_ERROR
    
    if parsed.command == "scan":
        return handle_scan(parsed)
    if parsed.command == "safe-share":
        return handle_safe_share(parsed)
    
    return EXIT_ERROR


def handle_scan(args: argparse.Namespace) -> int:
    """Handle scan command."""
    # Get API key
    api_key = args.api_key or os.environ.get("RISK_MIRROR_API_KEY")
    
    # Get input text
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
    return EXIT_ERROR


def handle_safe_share(args: argparse.Namespace) -> int:
    """Handle safe-share command."""
    api_key = args.api_key or os.environ.get("RISK_MIRROR_API_KEY")

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return EXIT_ERROR
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return EXIT_ERROR
    elif args.text:
        text = args.text
    else:
        if sys.stdin.isatty():
            print("Error: No input provided. Use -f FILE or provide text.", file=sys.stderr)
            return EXIT_ERROR
        text = sys.stdin.read()

    if not text.strip():
        print("Error: Empty input", file=sys.stderr)
        return EXIT_ERROR

    try:
        client = RiskMirror(api_key=api_key)
        result = client.safe_share(
            text,
            mode=args.mode,
            include_secrets=not args.no_secrets,
            strict_invalid=not args.allow_valid,
        )

        if args.quiet:
            print(result.safe_share_text)
            return EXIT_SAFE

        if args.json:
            print(json.dumps({
                "safe_share_text": result.safe_share_text,
                "mode": result.mode,
                "audit_summary": result.audit_summary,
            }, indent=2))
        else:
            print(result.safe_share_text)
            if result.audit_summary:
                print(f"\n🔐 Replaced spans: {result.audit_summary.get('spans_replaced', 0)}")
                print(f"🧩 Replaced chars: {result.audit_summary.get('chars_replaced', 0)}")
            print("\n🔐 Privacy: Stateless, no content stored")

        return EXIT_SAFE
    except RiskMirrorError as e:
        print(f"API Error: {e.message}", file=sys.stderr)
        if e.status_code == 401:
            print("Hint: Set RISK_MIRROR_API_KEY or use --api-key", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_ERROR
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return EXIT_ERROR
    elif args.text:
        text = args.text
    else:
        # Read from stdin
        if sys.stdin.isatty():
            print("Error: No input provided. Use -f FILE or provide text.", file=sys.stderr)
            return EXIT_ERROR
        text = sys.stdin.read()
    
    if not text.strip():
        print("Error: Empty input", file=sys.stderr)
        return EXIT_ERROR
    
    # Create client and scan
    try:
        client = RiskMirror(api_key=api_key)
        result = client.scan(text)
        
        if args.quiet:
            verdict = result.verdict.value if hasattr(result.verdict, 'value') else str(result.verdict)
            print(verdict)
        else:
            print(format_result(result, as_json=args.json))
        
        # Return exit code based on verdict
        verdict = result.verdict.value if hasattr(result.verdict, 'value') else str(result.verdict)
        return EXIT_SAFE if verdict == "SAFE" else EXIT_RISK
        
    except RiskMirrorError as e:
        print(f"API Error: {e.message}", file=sys.stderr)
        if e.status_code == 401:
            print("Hint: Set RISK_MIRROR_API_KEY or use --api-key", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
