"""Document Generation Report Formatter.

Format documentation generation output as human-readable reports.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""


def format_doc_gen_report(result: dict, input_data: dict) -> str:
    """Format document generation output as a human-readable report.

    Args:
        result: The polish stage result
        input_data: Input data from previous stages

    Returns:
        Formatted report string

    """
    lines = []

    # Header
    doc_type = result.get("doc_type", "general").replace("_", " ").title()
    audience = result.get("audience", "developers").replace("_", " ").title()

    lines.append("=" * 60)
    lines.append("DOCUMENTATION GENERATION REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Document Type: {doc_type}")
    lines.append(f"Target Audience: {audience}")
    lines.append("")

    # Outline summary
    outline = input_data.get("outline", "")
    if outline:
        lines.append("-" * 60)
        lines.append("DOCUMENT OUTLINE")
        lines.append("-" * 60)
        # Show just a preview of the outline
        outline_lines = outline.split("\n")[:10]
        lines.extend(outline_lines)
        if len(outline.split("\n")) > 10:
            lines.append("...")
        lines.append("")

    # Generated document
    document = result.get("document", "")
    if document:
        lines.append("-" * 60)
        lines.append("GENERATED DOCUMENTATION")
        lines.append("-" * 60)
        lines.append("")
        lines.append(document)
        lines.append("")

    # Statistics
    word_count = len(document.split()) if document else 0
    section_count = document.count("##") if document else 0  # Count markdown headers
    was_chunked = input_data.get("chunked", False)
    chunk_count = input_data.get("chunk_count", 0)
    chunks_completed = input_data.get("chunks_completed", chunk_count)
    stopped_early = input_data.get("stopped_early", False)
    accumulated_cost = result.get("accumulated_cost", 0)
    polish_chunked = result.get("polish_chunked", False)

    lines.append("-" * 60)
    lines.append("STATISTICS")
    lines.append("-" * 60)
    lines.append(f"Word Count: {word_count}")
    lines.append(f"Section Count: ~{section_count}")
    if was_chunked:
        if stopped_early:
            lines.append(
                f"Generation Mode: Chunked ({chunks_completed}/{chunk_count} chunks completed)",
            )
        else:
            lines.append(f"Generation Mode: Chunked ({chunk_count} chunks)")
    if polish_chunked:
        polish_chunks = result.get("polish_chunks", 0)
        lines.append(f"Polish Mode: Chunked ({polish_chunks} sections)")
    if accumulated_cost > 0:
        lines.append(f"Estimated Cost: ${accumulated_cost:.2f}")
    lines.append("")

    # Export info
    export_path = result.get("export_path")
    if export_path:
        lines.append("-" * 60)
        lines.append("FILE EXPORT")
        lines.append("-" * 60)
        lines.append(f"Documentation saved to: {export_path}")
        report_path = result.get("report_path")
        if report_path:
            lines.append(f"Report saved to: {report_path}")
        lines.append("")
        lines.append("Full documentation is available in the exported file.")
        lines.append("")

    # Warning notice (cost limit, errors, etc.)
    warning = input_data.get("warning") or result.get("warning")
    if warning or stopped_early:
        lines.append("-" * 60)
        lines.append("⚠️  WARNING")
        lines.append("-" * 60)
        if warning:
            lines.append(warning)
        if stopped_early and not warning:
            lines.append("Generation stopped early due to cost or error limits.")
        lines.append("")

    # Truncation detection and scope notice
    truncation_indicators = []
    if document:  # Handle None or empty document
        truncation_indicators = [
            document.rstrip().endswith("..."),
            document.rstrip().endswith("-"),
            "```" in document and document.count("```") % 2 != 0,  # Unclosed code block
            any(
                phrase in document.lower()
                for phrase in ["continued in", "see next section", "to be continued"]
            ),
        ]

    # Count planned sections from outline (top-level only)
    import re

    planned_sections = 0
    top_level_pattern = re.compile(r"^(\d+)\.\s+([A-Za-z].*)")
    if outline:
        for line in outline.split("\n"):
            stripped = line.strip()
            if top_level_pattern.match(stripped):
                planned_sections += 1

    is_truncated = any(truncation_indicators) or (
        planned_sections > 0 and section_count < planned_sections - 1
    )

    if is_truncated or planned_sections > section_count + 1:
        lines.append("-" * 60)
        lines.append("SCOPE NOTICE")
        lines.append("-" * 60)
        lines.append("⚠️  DOCUMENTATION MAY BE INCOMPLETE")
        if planned_sections > 0:
            lines.append(f"   Planned sections: {planned_sections}")
            lines.append(f"   Generated sections: {section_count}")
        lines.append("")
        lines.append("To generate missing sections, re-run with section_focus:")
        lines.append("   workflow = DocumentGenerationWorkflow(")
        lines.append('       section_focus=["Testing Guide", "API Reference"]')
        lines.append("   )")
        lines.append("")

    # Footer
    lines.append("=" * 60)
    model_tier = result.get("model_tier_used", "unknown")
    lines.append(f"Generated using {model_tier} tier model")
    lines.append("=" * 60)

    return "\n".join(lines)
