"""
Diff report generator for change visualization.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape


logger = logging.getLogger(__name__)


class DiffReporter:
    """Generate human-readable diff reports."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize reporter with template directory.
        
        Args:
            template_dir: Path to Jinja2 templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Register custom filters
        self.env.filters['format_date'] = self._format_date
        self.env.filters['format_number'] = self._format_number
        self.env.filters['highlight_diff'] = self._highlight_diff
    
    def generate_html_report(self, diff_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate HTML diff report.
        
        Args:
            diff_data: Diff results from DiffEngine
            output_path: Path to save HTML report
            
        Returns:
            Path to generated report
        """
        # Create simple HTML template if not exists
        template_content = self._get_default_html_template()
        
        # Process diff data for template
        context = self._prepare_context(diff_data)
        
        # Render HTML
        html_content = self._render_html_with_inline_template(template_content, context)
        
        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML diff report saved to {output_path}")
        return str(output_path)
    
    def generate_json_report(self, diff_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate JSON diff report.
        
        Args:
            diff_data: Diff results from DiffEngine
            output_path: Path to save JSON report
            
        Returns:
            Path to generated report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(diff_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"JSON diff report saved to {output_path}")
        return str(output_path)
    
    def generate_markdown_report(self, diff_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate Markdown diff report.
        
        Args:
            diff_data: Diff results from DiffEngine
            output_path: Path to save Markdown report
            
        Returns:
            Path to generated report
        """
        lines = []
        
        # Header
        lines.append("# RENEC Data Diff Report")
        lines.append(f"\nGenerated: {diff_data.get('generated_at', 'Unknown')}")
        lines.append(f"Period: {diff_data.get('timestamp1', 'Unknown')} to {diff_data.get('timestamp2', 'Unknown')}")
        
        # Summary
        summary = diff_data.get('summary', {})
        lines.append("\n## Summary")
        lines.append(f"- Total Changes: **{summary.get('total_changes', 0)}**")
        
        if 'by_operation' in summary:
            lines.append("\n### Changes by Operation")
            for op, count in summary['by_operation'].items():
                lines.append(f"- {op.capitalize()}: {count}")
        
        if 'by_entity' in summary:
            lines.append("\n### Changes by Entity")
            for entity, stats in summary['by_entity'].items():
                lines.append(f"\n#### {entity}")
                lines.append(f"- Added: {stats.get('added', 0)}")
                lines.append(f"- Removed: {stats.get('removed', 0)}")
                lines.append(f"- Modified: {stats.get('modified', 0)}")
        
        # Notable changes
        if summary.get('notable_changes'):
            lines.append("\n### Notable Changes")
            for change in summary['notable_changes']:
                lines.append(f"- {change['description']}")
        
        # Detailed changes by entity
        for entity_type, changes in diff_data.get('changes_by_type', {}).items():
            lines.append(f"\n## {entity_type} Changes")
            
            # Added items
            if changes.get('added'):
                lines.append(f"\n### Added ({len(changes['added'])} items)")
                for item in changes['added'][:5]:  # Show first 5
                    key = item.get('ec_clave') or item.get('cert_id', 'Unknown')
                    lines.append(f"- {key}: {item.get('data', {}).get('titulo') or item.get('data', {}).get('nombre_legal', 'Unknown')}")
                
                if len(changes['added']) > 5:
                    lines.append(f"- ... and {len(changes['added']) - 5} more")
            
            # Removed items
            if changes.get('removed'):
                lines.append(f"\n### Removed ({len(changes['removed'])} items)")
                for item in changes['removed'][:5]:
                    key = item.get('ec_clave') or item.get('cert_id', 'Unknown')
                    lines.append(f"- {key}: {item.get('data', {}).get('titulo') or item.get('data', {}).get('nombre_legal', 'Unknown')}")
                
                if len(changes['removed']) > 5:
                    lines.append(f"- ... and {len(changes['removed']) - 5} more")
            
            # Modified items
            if changes.get('modified'):
                lines.append(f"\n### Modified ({len(changes['modified'])} items)")
                for item in changes['modified'][:5]:
                    key = item.get('ec_clave') or item.get('cert_id', 'Unknown')
                    lines.append(f"\n#### {key}")
                    
                    for field, change in item.get('changes', {}).items():
                        if field == 'estandares_acreditados':
                            # Special handling for list changes
                            if 'added' in change:
                                lines.append(f"- Standards Added: {', '.join(change['added'])}")
                            if 'removed' in change:
                                lines.append(f"- Standards Removed: {', '.join(change['removed'])}")
                        else:
                            lines.append(f"- {field}: `{change['before']}` → `{change['after']}`")
                
                if len(changes['modified']) > 5:
                    lines.append(f"\n... and {len(changes['modified']) - 5} more modified items")
        
        # Statistics
        lines.append("\n## Statistics")
        for entity_type, changes in diff_data.get('changes_by_type', {}).items():
            if 'stats' in changes and changes['stats']:
                lines.append(f"\n### {entity_type}")
                for stat, value in changes['stats'].items():
                    if not stat.startswith('field_'):
                        lines.append(f"- {stat}: {value}")
        
        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Markdown diff report saved to {output_path}")
        return str(output_path)
    
    def _prepare_context(self, diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for template rendering."""
        context = diff_data.copy()
        
        # Add formatting helpers
        context['format_timestamp'] = lambda ts: datetime.fromisoformat(ts).strftime('%Y-%m-%d %H:%M:%S')
        context['format_duration'] = lambda s: f"{int(s/3600)}h {int(s%3600/60)}m" if s > 3600 else f"{int(s/60)}m"
        
        return context
    
    def _render_html_with_inline_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render HTML using inline template."""
        from jinja2 import Template
        
        tmpl = Template(template)
        return tmpl.render(**context)
    
    def _get_default_html_template(self) -> str:
        """Get default HTML template."""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RENEC Diff Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 {
            color: #2c3e50;
            margin: 0 0 10px 0;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        .stat-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .changes-section {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .added {
            color: #27ae60;
            background-color: #d5f4e6;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .removed {
            color: #e74c3c;
            background-color: #fadbd8;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .modified {
            color: #f39c12;
            background-color: #fdebd0;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .change-item {
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #3498db;
            background-color: #f8f9fa;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        .diff-before {
            background-color: #fadbd8;
            text-decoration: line-through;
        }
        .diff-after {
            background-color: #d5f4e6;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>RENEC Data Diff Report</h1>
        <p>Period: {{ timestamp1 }} to {{ timestamp2 }}</p>
        <p>Generated: {{ generated_at }}</p>
    </div>
    
    <div class="summary">
        <div class="stat-card">
            <div class="stat-value">{{ summary.total_changes }}</div>
            <div class="stat-label">Total Changes</div>
        </div>
        {% for op, count in summary.by_operation.items() %}
        <div class="stat-card">
            <div class="stat-value">{{ count }}</div>
            <div class="stat-label">{{ op|capitalize }}</div>
        </div>
        {% endfor %}
    </div>
    
    {% for entity_type, changes in changes_by_type.items() %}
    <div class="changes-section">
        <h2>{{ entity_type|replace('_', ' ')|title }}</h2>
        
        {% if changes.added %}
        <h3><span class="added">Added ({{ changes.added|length }})</span></h3>
        <ul>
            {% for item in changes.added[:10] %}
            <li>{{ item.ec_clave or item.cert_id }}: {{ item.data.titulo or item.data.nombre_legal }}</li>
            {% endfor %}
            {% if changes.added|length > 10 %}
            <li>... and {{ changes.added|length - 10 }} more</li>
            {% endif %}
        </ul>
        {% endif %}
        
        {% if changes.removed %}
        <h3><span class="removed">Removed ({{ changes.removed|length }})</span></h3>
        <ul>
            {% for item in changes.removed[:10] %}
            <li>{{ item.ec_clave or item.cert_id }}: {{ item.data.titulo or item.data.nombre_legal }}</li>
            {% endfor %}
            {% if changes.removed|length > 10 %}
            <li>... and {{ changes.removed|length - 10 }} more</li>
            {% endif %}
        </ul>
        {% endif %}
        
        {% if changes.modified %}
        <h3><span class="modified">Modified ({{ changes.modified|length }})</span></h3>
        {% for item in changes.modified[:5] %}
        <div class="change-item">
            <h4>{{ item.ec_clave or item.cert_id }}</h4>
            <table>
                <tr>
                    <th>Field</th>
                    <th>Before</th>
                    <th>After</th>
                </tr>
                {% for field, change in item.changes.items() %}
                <tr>
                    <td>{{ field }}</td>
                    <td class="diff-before">{{ change.before }}</td>
                    <td class="diff-after">{{ change.after }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endfor %}
        {% if changes.modified|length > 5 %}
        <p>... and {{ changes.modified|length - 5 }} more modified items</p>
        {% endif %}
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>'''
    
    def _format_date(self, date_str: str) -> str:
        """Format date string."""
        try:
            date = datetime.fromisoformat(date_str)
            return date.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str
    
    def _format_number(self, num: int) -> str:
        """Format number with thousands separator."""
        return f"{num:,}"
    
    def _highlight_diff(self, text: str, is_before: bool = True) -> str:
        """Highlight diff text."""
        if is_before:
            return f'<span class="diff-before">{text}</span>'
        else:
            return f'<span class="diff-after">{text}</span>'