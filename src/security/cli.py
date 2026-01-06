#!/usr/bin/env python
"""Command-line interface for the Security Audit Scanner.

This module provides a CLI entry point for running security audits on
repositories. It supports dry-run mode, custom output paths, and
configurable annotation behavior.

Usage:
    python -m src.security.cli [OPTIONS] [REPO_PATH]
    
Examples:
    # Run audit on current directory
    python -m src.security.cli
    
    # Run audit on specific directory
    python -m src.security.cli /path/to/repo
    
    # Dry run (no file modifications)
    python -m src.security.cli --dry-run
    
    # Skip annotation injection
    python -m src.security.cli --no-annotations
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.security.security_scanner import SecurityScanner


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the CLI.
    
    Args:
        verbose: If True, enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: Optional list of arguments (defaults to sys.argv)
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="security-audit",
        description="Security Audit Scanner - Scan repositories for security vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      Run audit on current directory
  %(prog)s /path/to/repo        Run audit on specific directory
  %(prog)s --dry-run            Preview without modifying files
  %(prog)s --no-annotations     Skip adding TODO comments
  %(prog)s -o report.md         Custom output file path
        """,
    )
    
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the repository to scan (default: current directory)",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run audit without modifying any files (no annotations)",
    )
    
    parser.add_argument(
        "--no-annotations",
        action="store_true",
        help="Skip injecting security annotations into source files",
    )
    
    parser.add_argument(
        "--no-verify-tests",
        action="store_true",
        help="Skip test verification after adding annotations",
    )
    
    parser.add_argument(
        "--test-command",
        type=str,
        default=None,
        help="Custom test command to run for verification (default: auto-detect)",
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output path for the security report (default: SECURITY_AUDIT.md in repo root)",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress console output (only write report)",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )
    
    return parser.parse_args(args)


def validate_repo_path(repo_path: str) -> Path:
    """Validate that the repository path exists and is a directory.
    
    Args:
        repo_path: Path to validate
        
    Returns:
        Resolved Path object
        
    Raises:
        SystemExit: If path is invalid
    """
    path = Path(repo_path).resolve()
    
    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        sys.exit(1)
    
    if not path.is_dir():
        print(f"Error: Path is not a directory: {path}", file=sys.stderr)
        sys.exit(1)
    
    return path


def run_audit(
    repo_path: Path,
    dry_run: bool = False,
    inject_annotations: bool = True,
    verify_tests: bool = True,
    test_command: Optional[str] = None,
    output_path: Optional[str] = None,
    quiet: bool = False,
) -> int:
    """Run the security audit.
    
    Args:
        repo_path: Path to the repository to scan
        dry_run: If True, don't modify files
        inject_annotations: If True, inject security annotations
        verify_tests: If True, verify tests after annotation
        test_command: Optional custom test command
        output_path: Optional custom output path
        quiet: If True, suppress console output
        
    Returns:
        Exit code (0 for success, 1 for findings, 2 for errors)
    """
    try:
        # Create scanner
        scanner = SecurityScanner(str(repo_path), dry_run=dry_run)
        
        if not quiet:
            print(f"\nScanning repository: {repo_path}")
            if dry_run:
                print("(Dry run mode - no files will be modified)")
            print()
        
        # Run full audit
        audit_report, report_path = scanner.run_full_audit(
            inject_annotations=inject_annotations and not dry_run,
            verify_tests=verify_tests,
            test_command=test_command,
            output_path=output_path,
        )
        
        # Print summary
        if not quiet:
            scanner.print_summary()
            print(f"Report written to: {report_path}\n")
        
        # Return appropriate exit code
        if audit_report.critical_count > 0:
            return 1  # Critical findings
        elif audit_report.high_count > 0:
            return 1  # High severity findings
        elif audit_report.total_findings > 0:
            return 0  # Only medium/low findings
        else:
            return 0  # No findings
            
    except KeyboardInterrupt:
        print("\nAudit cancelled by user.", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"\nError during audit: {e}", file=sys.stderr)
        logging.exception("Audit failed with exception")
        return 2


def main(args: Optional[list] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        args: Optional list of arguments (for testing)
        
    Returns:
        Exit code
    """
    parsed_args = parse_args(args)
    
    # Setup logging
    if not parsed_args.quiet:
        setup_logging(parsed_args.verbose)
    
    # Validate repository path
    repo_path = validate_repo_path(parsed_args.repo_path)
    
    # Determine annotation behavior
    inject_annotations = not parsed_args.no_annotations
    verify_tests = not parsed_args.no_verify_tests
    
    # Run audit
    return run_audit(
        repo_path=repo_path,
        dry_run=parsed_args.dry_run,
        inject_annotations=inject_annotations,
        verify_tests=verify_tests,
        test_command=parsed_args.test_command,
        output_path=parsed_args.output,
        quiet=parsed_args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
