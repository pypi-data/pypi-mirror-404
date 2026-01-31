"""Output reporters for SQL analysis results."""

import json
import fenic as fc


def print_analysis_summary(df: fc.DataFrame):
    """Print analysis results as JSON."""
    try:
        results = df.to_pydict()
        print(json.dumps(results, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")


def print_compact_summary(df: fc.DataFrame):
    """Print a compact summary of analysis results."""
    results = df.select(
        "filename", "business_semantics", "grain_humanization", "audit_analysis"
    ).to_pydict()

    for i in range(len(results["filename"])):
        print(f"\n{'=' * 60}")
        print(f"FILE: {results['filename'][i]}")
        print(f"{'=' * 60}")

        if "business_semantics" in results and results["business_semantics"][i]:
            business = results["business_semantics"][i]
            print(f"\n💼 BUSINESS SUMMARY:")
            print(f"  Grain: {business['grain_human']}")
            print(f"  Intent: {business['intent']}")
            print(f"  Measures: {', '.join([m['name'] for m in business['measures']])}")
            print(
                f"  Dimensions: {', '.join([d['name'] for d in business['dimensions']])}"
            )

        if "audit_analysis" in results and results["audit_analysis"][i]:
            audit = results["audit_analysis"][i]
            status = "✅ PASSED" if audit["approved"] else "❌ FAILED"
            print(f"\n{status} - {len(audit['findings'])} findings")
