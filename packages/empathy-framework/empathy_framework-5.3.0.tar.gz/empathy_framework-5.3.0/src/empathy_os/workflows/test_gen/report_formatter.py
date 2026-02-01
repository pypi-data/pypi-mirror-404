"""Test Generation Report Formatter.

Format test generation output as human-readable reports.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import re


def format_test_gen_report(result: dict, input_data: dict) -> str:
    """Format test generation output as a human-readable report.

    Args:
        result: The review stage result
        input_data: Input data from previous stages

    Returns:
        Formatted report string

    """
    lines = []

    # Header
    total_tests = result.get("total_tests", 0)
    files_covered = result.get("files_covered", 0)

    lines.append("=" * 60)
    lines.append("TEST GAP ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Summary stats
    total_candidates = input_data.get("total_candidates", 0)
    hotspot_count = input_data.get("hotspot_count", 0)
    untested_count = input_data.get("untested_count", 0)

    lines.append("-" * 60)
    lines.append("SUMMARY")
    lines.append("-" * 60)
    lines.append(f"Tests Generated:     {total_tests}")
    lines.append(f"Files Covered:       {files_covered}")
    lines.append(f"Total Candidates:    {total_candidates}")
    lines.append(f"Bug Hotspots Found:  {hotspot_count}")
    lines.append(f"Untested Files:      {untested_count}")
    lines.append("")

    # Status indicator
    if total_tests == 0:
        lines.append("⚠️  No tests were generated")
    elif total_tests < 5:
        lines.append(f"🟡 Generated {total_tests} test(s) - consider adding more coverage")
    elif total_tests < 20:
        lines.append(f"🟢 Generated {total_tests} tests - good coverage")
    else:
        lines.append(f"✅ Generated {total_tests} tests - excellent coverage")
    lines.append("")

    # Scope notice for enterprise clarity
    total_source = input_data.get("total_source_files", 0)
    existing_tests = input_data.get("existing_test_files", 0)
    coverage_pct = input_data.get("analysis_coverage_percent", 100)
    large_project = input_data.get("large_project_warning", False)

    if total_source > 0 or existing_tests > 0:
        lines.append("-" * 60)
        lines.append("SCOPE NOTICE")
        lines.append("-" * 60)

        if large_project:
            lines.append("⚠️  LARGE PROJECT: Only high-priority files analyzed")
            lines.append(f"   Coverage: {coverage_pct:.0f}% of candidate files")
            lines.append("")

        lines.append(f"Source Files Found:   {total_source}")
        lines.append(f"Existing Test Files:  {existing_tests}")
        lines.append(f"Files Analyzed:       {files_covered}")

        if existing_tests > 0:
            lines.append("")
            lines.append("Note: This report identifies gaps in untested files.")
            lines.append("Run 'pytest --co -q' for full test suite statistics.")
        lines.append("")

    # Parse XML review feedback if present
    review = result.get("review_feedback", "")
    xml_summary = ""
    xml_findings = []
    xml_tests = []
    coverage_improvement = ""

    if review and "<response>" in review:
        # Extract summary
        summary_match = re.search(r"<summary>(.*?)</summary>", review, re.DOTALL)
        if summary_match:
            xml_summary = summary_match.group(1).strip()

        # Extract coverage improvement
        coverage_match = re.search(
            r"<coverage-improvement>(.*?)</coverage-improvement>",
            review,
            re.DOTALL,
        )
        if coverage_match:
            coverage_improvement = coverage_match.group(1).strip()

        # Extract findings
        for finding_match in re.finditer(
            r'<finding severity="(\w+)">(.*?)</finding>',
            review,
            re.DOTALL,
        ):
            severity = finding_match.group(1)
            finding_content = finding_match.group(2)

            title_match = re.search(r"<title>(.*?)</title>", finding_content, re.DOTALL)
            location_match = re.search(r"<location>(.*?)</location>", finding_content, re.DOTALL)
            fix_match = re.search(r"<fix>(.*?)</fix>", finding_content, re.DOTALL)

            xml_findings.append(
                {
                    "severity": severity,
                    "title": title_match.group(1).strip() if title_match else "Unknown",
                    "location": location_match.group(1).strip() if location_match else "",
                    "fix": fix_match.group(1).strip() if fix_match else "",
                },
            )

        # Extract suggested tests
        for test_match in re.finditer(r'<test target="([^"]+)">(.*?)</test>', review, re.DOTALL):
            target = test_match.group(1)
            test_content = test_match.group(2)

            type_match = re.search(r"<type>(.*?)</type>", test_content, re.DOTALL)
            desc_match = re.search(r"<description>(.*?)</description>", test_content, re.DOTALL)

            xml_tests.append(
                {
                    "target": target,
                    "type": type_match.group(1).strip() if type_match else "unit",
                    "description": desc_match.group(1).strip() if desc_match else "",
                },
            )

    # Show parsed summary
    if xml_summary:
        lines.append("-" * 60)
        lines.append("QUALITY ASSESSMENT")
        lines.append("-" * 60)
        # Word wrap the summary
        words = xml_summary.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 58:
                current_line += (" " if current_line else "") + word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        lines.append("")

        if coverage_improvement:
            lines.append(f"📈 {coverage_improvement}")
            lines.append("")

    # Show findings by severity
    if xml_findings:
        lines.append("-" * 60)
        lines.append("QUALITY FINDINGS")
        lines.append("-" * 60)

        severity_emoji = {"high": "🔴", "medium": "🟠", "low": "🟡", "info": "🔵"}
        severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}

        sorted_findings = sorted(xml_findings, key=lambda f: severity_order.get(f["severity"], 4))

        for finding in sorted_findings:
            emoji = severity_emoji.get(finding["severity"], "⚪")
            lines.append(f"{emoji} [{finding['severity'].upper()}] {finding['title']}")
            if finding["location"]:
                lines.append(f"   Location: {finding['location']}")
            if finding["fix"]:
                # Truncate long fix recommendations
                fix_text = finding["fix"]
                if len(fix_text) > 70:
                    fix_text = fix_text[:67] + "..."
                lines.append(f"   Fix: {fix_text}")
            lines.append("")

    # Show suggested tests
    if xml_tests:
        lines.append("-" * 60)
        lines.append("SUGGESTED TESTS TO ADD")
        lines.append("-" * 60)

        for i, test in enumerate(xml_tests[:5], 1):  # Limit to 5
            lines.append(f"{i}. {test['target']} ({test['type']})")
            if test["description"]:
                desc = test["description"]
                if len(desc) > 55:
                    desc = desc[:52] + "..."
                lines.append(f"   {desc}")
            lines.append("")

        if len(xml_tests) > 5:
            lines.append(f"   ... and {len(xml_tests) - 5} more suggested tests")
            lines.append("")

    # Generated tests breakdown (if no XML data)
    generated_tests = input_data.get("generated_tests", [])
    if generated_tests and not xml_findings:
        lines.append("-" * 60)
        lines.append("GENERATED TESTS BY FILE")
        lines.append("-" * 60)
        for test_file in generated_tests[:10]:  # Limit display
            source = test_file.get("source_file", "unknown")
            test_count = test_file.get("test_count", 0)
            # Shorten path for display
            if len(source) > 50:
                source = "..." + source[-47:]
            lines.append(f"  📁 {source}")
            lines.append(
                f"     └─ {test_count} test(s) → {test_file.get('test_file', 'test_*.py')}",
            )
        if len(generated_tests) > 10:
            lines.append(f"  ... and {len(generated_tests) - 10} more files")
        lines.append("")

    # Written files section
    written_files = input_data.get("written_files", [])
    if written_files:
        lines.append("-" * 60)
        lines.append("TESTS WRITTEN TO DISK")
        lines.append("-" * 60)
        for file_path in written_files[:10]:
            # Shorten path for display
            if len(file_path) > 55:
                file_path = "..." + file_path[-52:]
            lines.append(f"  ✅ {file_path}")
        if len(written_files) > 10:
            lines.append(f"  ... and {len(written_files) - 10} more files")
        lines.append("")
        lines.append("  Run: pytest <file> to execute these tests")
        lines.append("")
    elif input_data.get("tests_written") is False and total_tests > 0:
        lines.append("-" * 60)
        lines.append("GENERATED TESTS (NOT WRITTEN)")
        lines.append("-" * 60)
        lines.append("  ⚠️  Tests were generated but not written to disk.")
        lines.append("  To write tests, run with: write_tests=True")
        lines.append("")

    # Recommendations
    lines.append("-" * 60)
    lines.append("NEXT STEPS")
    lines.append("-" * 60)

    high_findings = sum(1 for f in xml_findings if f["severity"] == "high")
    medium_findings = sum(1 for f in xml_findings if f["severity"] == "medium")

    if high_findings > 0:
        lines.append(f"  🔴 Address {high_findings} high-priority finding(s) first")

    if medium_findings > 0:
        lines.append(f"  🟠 Review {medium_findings} medium-priority finding(s)")

    if xml_tests:
        lines.append(f"  📝 Consider adding {len(xml_tests)} suggested test(s)")

    if hotspot_count > 0:
        lines.append(f"  🔥 {hotspot_count} bug hotspot file(s) need priority testing")

    if untested_count > 0:
        lines.append(f"  📁 {untested_count} file(s) have no existing tests")

    if not any([high_findings, medium_findings, xml_tests, hotspot_count, untested_count]):
        lines.append("  ✅ Test suite is in good shape!")

    lines.append("")

    # Footer
    lines.append("=" * 60)
    model_tier = result.get("model_tier_used", "unknown")
    lines.append(f"Review completed using {model_tier} tier model")
    lines.append("=" * 60)

    return "\n".join(lines)
