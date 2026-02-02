import datetime
import html
from pathlib import Path
from typing import List

from .validator import ValidationError

class ValidationReporter:
    """
    Generates human-readable reports from validation errors.
    """

    @staticmethod
    def generate_report(errors: List[ValidationError], output_path: str):
        """
        Generates a validation report and saves it to the specified path.
        Detects format (HTML/Markdown) based on file extension.
        
        Args:
            errors: List of ValidationError objects.
            output_path: Path to save the report.
        """
        path = Path(output_path)
        ext = path.suffix.lower()
        
        if ext in ['.html', '.htm']:
            content = ValidationReporter._generate_html(errors)
        elif ext in ['.md', '.markdown']:
            content = ValidationReporter._generate_markdown(errors)
        else:
            # Default to text/markdown if unknown
            content = ValidationReporter._generate_markdown(errors)
            
        path.write_text(content, encoding='utf-8')

    @staticmethod
    def _generate_markdown(errors: List[ValidationError]) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "FAILED" if errors else "PASSED"
        
        md = [f"# OmicsGuard Validation Report"]
        md.append(f"**Date:** {timestamp}")
        md.append(f"**Status:** {status}")
        md.append("")
        
        if not errors:
            md.append("No validation errors found. The metadata is compliant.")
        else:
            md.append(f"Found {len(errors)} errors:")
            md.append("")
            md.append("| Field | Error Message |")
            md.append("| --- | --- |")
            for err in errors:
                safe_msg = err.message.replace("|", r"\|")
                md.append(f"| `{err.path}` | {safe_msg} |")
                
        return "\n".join(md)

    @staticmethod
    def _generate_html(errors: List[ValidationError]) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "FAILED" if errors else "PASSED"
        color = "#e74c3c" if errors else "#2ecc71" # Red or Green
        
        rows = ""
        for err in errors:
            rows += f"""
            <tr>
                <td><code>{html.escape(err.path)}</code></td>
                <td>{html.escape(err.message)}</td>
            </tr>
            """
            
        if not errors:
            content = "<p class='success'>No validation errors found. The metadata is compliant.</p>"
        else:
            content = f"""
            <p>Found <strong>{len(errors)}</strong> errors:</p>
            <table>
                <thead>
                    <tr>
                        <th>Field</th>
                        <th>Error Message</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            """

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OmicsGuard Validation Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 960px; margin: 0 auto; padding: 20px; }}
        h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .meta {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .status {{ font-weight: bold; color: {color}; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #f5f5f5; }}
        code {{ background-color: #eee; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
        .success {{ color: #2ecc71; font-weight: bold; font-size: 1.2em; }}
    </style>
</head>
<body>
    <h1>OmicsGuard Validation Report</h1>
    <div class="meta">
        <p><strong>Date:</strong> {timestamp}</p>
        <p><strong>Status:</strong> <span class="status">{status}</span></p>
    </div>
    {content}
</body>
</html>
"""
        return html_template
