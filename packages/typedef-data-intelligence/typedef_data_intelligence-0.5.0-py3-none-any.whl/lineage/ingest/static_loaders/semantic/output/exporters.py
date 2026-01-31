"""Export utilities for SQL analysis results."""

import json
from pathlib import Path
from typing import Optional
import fenic as fc


class ResultExporter:
    """Export analysis results to various formats."""

    @staticmethod
    def to_json(df: fc.DataFrame, output_path: str, pretty: bool = True):
        """
        Export results to JSON file.

        Args:
            df: DataFrame with analysis results
            output_path: Path to output JSON file
            pretty: Whether to format JSON with indentation
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        results = df.to_pydict()

        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(results, f, indent=2, ensure_ascii=False)
            else:
                json.dump(results, f, ensure_ascii=False)

        print(f"Results exported to {output_path}")

    @staticmethod
    def to_parquet(df: fc.DataFrame, output_path: str):
        """
        Export results to Parquet file.

        Args:
            df: DataFrame with analysis results
            output_path: Path to output Parquet file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to Parquet using Fenic
        df.write.parquet(str(output_path))

        print(f"Results exported to {output_path}")

    @staticmethod
    def to_csv(df: fc.DataFrame, output_path: str):
        """
        Export summary results to CSV file.

        Args:
            df: DataFrame with analysis results
            output_path: Path to output CSV file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Select summary columns for CSV
        summary_df = df.select(
            "filename",
            fc.col("business_semantics.grain_human").alias("grain"),
            fc.col("business_semantics.intent").alias("intent"),
            fc.col("audit_analysis.approved").alias("audit_passed"),
        )

        # Write to CSV using Fenic
        summary_df.write.csv(str(output_path))

        print(f"Summary exported to {output_path}")

    @staticmethod
    def export_by_pass(df: fc.DataFrame, output_dir: str):
        """
        Export each pass result to a separate JSON file.

        Args:
            df: DataFrame with analysis results
            output_dir: Directory to save individual pass results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # List of passes to export
        passes = [
            "relation_analysis",
            "column_analysis",
            "join_analysis",
            "filter_analysis",
            "grouping_by_scope",
            "time_by_scope",
            "window_by_scope",
            "output_by_scope",
            "audit_analysis",
            "business_semantics",
            "grain_humanization",
        ]

        for pass_name in passes:
            if pass_name in df.columns:
                pass_df = df.select("filename", pass_name)
                pass_results = pass_df.to_pydict()

                output_path = output_dir / f"{pass_name}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(pass_results, f, indent=2, ensure_ascii=False)

                print(f"  Exported {pass_name} to {output_path}")

        print(f"All pass results exported to {output_dir}")

    @staticmethod
    def export_audit_report(df: fc.DataFrame, output_path: str):
        """
        Export detailed audit report.

        Args:
            df: DataFrame with analysis results
            output_path: Path to output audit report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        results = df.select("filename", "audit_analysis").to_pydict()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("SQL ANALYSIS AUDIT REPORT\n")
            f.write("=" * 60 + "\n\n")

            for i in range(len(results["filename"])):
                f.write(f"File: {results['filename'][i]}\n")
                f.write("-" * 40 + "\n")

                audit = results["audit_analysis"][i]
                if audit:
                    status = "PASSED ✅" if audit["approved"] else "FAILED ❌"
                    f.write(f"Status: {status}\n\n")

                    if audit["findings"]:
                        f.write(f"Findings ({len(audit['findings'])}):\n")

                        # Group by severity
                        errors = [
                            f for f in audit["findings"] if f["severity"] == "error"
                        ]
                        warnings = [
                            f for f in audit["findings"] if f["severity"] == "warning"
                        ]
                        infos = [
                            f for f in audit["findings"] if f["severity"] == "info"
                        ]

                        if errors:
                            f.write("\n  ERRORS:\n")
                            for finding in errors:
                                f.write(
                                    f"    • {finding['code']}: {finding['message']}\n"
                                )

                        if warnings:
                            f.write("\n  WARNINGS:\n")
                            for finding in warnings:
                                f.write(
                                    f"    • {finding['code']}: {finding['message']}\n"
                                )

                        if infos:
                            f.write("\n  INFO:\n")
                            for finding in infos:
                                f.write(
                                    f"    • {finding['code']}: {finding['message']}\n"
                                )

                    if audit["suggested_patches"]:
                        f.write(
                            f"\nSuggested Patches ({len(audit['suggested_patches'])}):\n"
                        )
                        for patch in audit["suggested_patches"]:
                            f.write(
                                f"  • {patch['op']} {patch['path']}: {patch['rationale']}\n"
                            )

                    f.write("\n")
                else:
                    f.write("No audit results available\n\n")

        print(f"Audit report exported to {output_path}")
