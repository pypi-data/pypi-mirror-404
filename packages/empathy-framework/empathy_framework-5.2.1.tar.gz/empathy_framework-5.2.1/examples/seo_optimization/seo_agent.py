"""SEO Optimization Agent System

A multi-agent system that audits, suggests, and implements SEO improvements for MkDocs sites.

This is a reference example showing how to use the Empathy Framework to build
a production-ready agent team with interactive approval workflows.

Usage:
    python seo_agent.py --mode audit     # Audit only
    python seo_agent.py --mode suggest   # Audit + suggestions
    python seo_agent.py --mode fix       # Audit + suggest + implement fixes
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from empathy_os.orchestration import MetaOrchestrator
from empathy_os.orchestration.composition_patterns import CompositionPattern

from utils import (
    SEOAuditor,
    ContentOptimizer,
    TechnicalSEOSpecialist,
    LinkAnalyzer,
    SEOReporter,
    SEOFixer,
)


@dataclass
class SEOAgentConfig:
    """Configuration for SEO optimization agent."""

    docs_path: Path
    site_url: str
    target_keywords: list[str]
    min_meta_description_length: int = 120
    max_meta_description_length: int = 160
    min_title_length: int = 30
    max_title_length: int = 60
    enable_auto_fix: bool = True


class SEOOptimizationTeam:
    """Multi-agent system for SEO optimization.

    This team coordinates four specialized agents:
    1. SEO Auditor - Scans for SEO issues
    2. Content Optimizer - Suggests content improvements
    3. Technical SEO Specialist - Handles technical SEO elements
    4. Link Analyzer - Analyzes internal/external linking
    """

    def __init__(self, config: SEOAgentConfig):
        """Initialize SEO optimization team.

        Args:
            config: Configuration for SEO optimization
        """
        self.config = config
        self.orchestrator = MetaOrchestrator()

        # Initialize specialized agents
        self.auditor = SEOAuditor(config)
        self.content_optimizer = ContentOptimizer(config)
        self.technical_specialist = TechnicalSEOSpecialist(config)
        self.link_analyzer = LinkAnalyzer(config)
        self.reporter = SEOReporter()
        self.fixer = SEOFixer(config)

    def audit(self) -> dict[str, Any]:
        """Run complete SEO audit.

        Returns:
            Comprehensive audit report with all findings
        """
        print("\n🔍 Starting SEO Audit...")
        print(f"📁 Scanning: {self.config.docs_path}")
        print(f"🌐 Site URL: {self.config.site_url}")

        # Gather findings from all agents
        audit_results = {
            "meta_tags": self.auditor.check_meta_tags(),
            "content_quality": self.content_optimizer.analyze_content(),
            "technical_seo": self.technical_specialist.check_technical_elements(),
            "links": self.link_analyzer.analyze_links(),
        }

        # Generate summary report
        report = self.reporter.generate_report(audit_results)

        print(f"\n✅ Audit complete: {report['total_issues']} issues found")
        print(f"   🔴 Critical: {report['critical_count']}")
        print(f"   🟡 Warning: {report['warning_count']}")
        print(f"   🔵 Info: {report['info_count']}")

        return report

    def suggest_fixes(self, audit_report: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate fix suggestions based on audit.

        Args:
            audit_report: Output from audit()

        Returns:
            List of suggested fixes with implementation details
        """
        print("\n💡 Generating fix suggestions...")

        suggestions = []

        # Meta tag improvements
        for issue in audit_report.get("issues", []):
            if issue["category"] == "meta_tags":
                suggestion = self._create_meta_tag_fix(issue)
                suggestions.append(suggestion)
            elif issue["category"] == "content":
                suggestion = self._create_content_fix(issue)
                suggestions.append(suggestion)
            elif issue["category"] == "technical":
                suggestion = self._create_technical_fix(issue)
                suggestions.append(suggestion)
            elif issue["category"] == "links":
                suggestion = self._create_link_fix(issue)
                suggestions.append(suggestion)

        print(f"✅ Generated {len(suggestions)} fix suggestions")
        return suggestions

    def implement_fixes(
        self, suggestions: list[dict[str, Any]], interactive: bool = True
    ) -> dict[str, Any]:
        """Implement suggested fixes with optional interactive approval.

        Args:
            suggestions: List of fix suggestions from suggest_fixes()
            interactive: If True, ask for approval before each fix

        Returns:
            Implementation report with success/failure details
        """
        print(f"\n🔧 Implementing fixes (interactive={interactive})...")

        if interactive:
            return self._implement_with_approval(suggestions)
        else:
            return self._implement_all(suggestions)

    def _implement_with_approval(
        self, suggestions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Implement fixes with user approval for each one.

        Uses MetaOrchestrator's interactive mode for approval workflow.
        """
        print("\n📋 Review and approve fixes:\n")

        approved_fixes = []
        rejected_fixes = []

        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n[{i}/{len(suggestions)}] {suggestion['title']}")
            print(f"   File: {suggestion['file']}")
            print(f"   Type: {suggestion['severity']}")
            print(f"   Change: {suggestion['description']}")

            # Show preview if available
            if "preview" in suggestion:
                print("\n   Preview:")
                print(f"   - Before: {suggestion['preview']['before'][:80]}...")
                print(f"   - After:  {suggestion['preview']['after'][:80]}...")

            # Use interactive prompt (in real implementation, this would use Claude Code IPC)
            response = input("\n   Apply this fix? [y/n/q]: ").lower().strip()

            if response == "q":
                print("\n❌ Fix process cancelled by user")
                break
            elif response == "y":
                # Apply the fix
                success = self.fixer.apply_fix(suggestion)
                if success:
                    approved_fixes.append(suggestion)
                    print("   ✅ Applied")
                else:
                    rejected_fixes.append(
                        {**suggestion, "reason": "Implementation failed"}
                    )
                    print("   ❌ Failed to apply")
            else:
                rejected_fixes.append({**suggestion, "reason": "User rejected"})
                print("   ⏭️  Skipped")

        return {
            "total": len(suggestions),
            "applied": len(approved_fixes),
            "rejected": len(rejected_fixes),
            "approved_fixes": approved_fixes,
            "rejected_fixes": rejected_fixes,
        }

    def _implement_all(self, suggestions: list[dict[str, Any]]) -> dict[str, Any]:
        """Implement all fixes without approval."""
        results = {"applied": [], "failed": []}

        for suggestion in suggestions:
            success = self.fixer.apply_fix(suggestion)
            if success:
                results["applied"].append(suggestion)
            else:
                results["failed"].append(suggestion)

        return {
            "total": len(suggestions),
            "applied": len(results["applied"]),
            "failed": len(results["failed"]),
            "details": results,
        }

    def _create_meta_tag_fix(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Create fix suggestion for meta tag issue."""
        return {
            "title": f"Fix missing/invalid meta tag: {issue['element']}",
            "file": issue["file"],
            "severity": issue["severity"],
            "category": "meta_tags",
            "description": issue["message"],
            "fix_type": "add_meta_tag",
            "data": {"tag": issue["element"], "suggested_value": issue.get("suggestion")},
        }

    def _create_content_fix(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Create fix suggestion for content issue."""
        return {
            "title": f"Improve content: {issue['element']}",
            "file": issue["file"],
            "severity": issue["severity"],
            "category": "content",
            "description": issue["message"],
            "fix_type": "update_content",
            "data": {"element": issue["element"], "suggestion": issue.get("suggestion")},
        }

    def _create_technical_fix(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Create fix suggestion for technical SEO issue."""
        return {
            "title": f"Technical SEO: {issue['element']}",
            "file": issue["file"],
            "severity": issue["severity"],
            "category": "technical",
            "description": issue["message"],
            "fix_type": "technical_update",
            "data": issue.get("fix_data", {}),
        }

    def _create_link_fix(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Create fix suggestion for link issue."""
        return {
            "title": f"Fix link: {issue['element']}",
            "file": issue["file"],
            "severity": issue["severity"],
            "category": "links",
            "description": issue["message"],
            "fix_type": "update_link",
            "data": {"link": issue["element"], "suggestion": issue.get("suggestion")},
        }


def main():
    """Main entry point for SEO optimization agent."""
    parser = argparse.ArgumentParser(
        description="SEO Optimization Agent - Multi-agent system for MkDocs sites"
    )
    parser.add_argument(
        "--mode",
        choices=["audit", "suggest", "fix"],
        default="audit",
        help="Operation mode: audit, suggest fixes, or implement fixes",
    )
    parser.add_argument(
        "--docs-path",
        type=Path,
        default=Path("docs"),
        help="Path to documentation directory",
    )
    parser.add_argument(
        "--site-url",
        default="https://smartaimemory.com",
        help="Base URL of the site",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file (optional, overrides CLI args)",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip interactive approval (auto-apply all fixes)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for results (JSON format)",
    )

    args = parser.parse_args()

    # Load configuration
    if args.config and args.config.exists():
        import yaml

        with open(args.config) as f:
            config_data = yaml.safe_load(f)
        config = SEOAgentConfig(
            docs_path=Path(config_data["docs_path"]),
            site_url=config_data["site_url"],
            target_keywords=config_data.get("target_keywords", []),
        )
    else:
        config = SEOAgentConfig(
            docs_path=args.docs_path,
            site_url=args.site_url,
            target_keywords=[
                "AI framework",
                "anticipatory AI",
                "multi-agent systems",
            ],
        )

    # Initialize agent team
    team = SEOOptimizationTeam(config)

    # Execute requested mode
    if args.mode == "audit":
        results = team.audit()
    elif args.mode == "suggest":
        audit_results = team.audit()
        results = team.suggest_fixes(audit_results)
    else:  # fix
        audit_results = team.audit()
        suggestions = team.suggest_fixes(audit_results)
        results = team.implement_fixes(
            suggestions, interactive=not args.no_interactive
        )

    # Save results if output file specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")

    print("\n✨ SEO optimization complete!")


if __name__ == "__main__":
    main()
