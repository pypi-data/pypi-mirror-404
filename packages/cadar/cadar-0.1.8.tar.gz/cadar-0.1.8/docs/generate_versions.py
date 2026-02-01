#!/usr/bin/env python3
"""
Generate versions index page for documentation
"""

import os
import json
from pathlib import Path


def generate_versions_index():
    """Generate an index of all documentation versions"""

    versions_dir = Path(__file__).parent / 'site' / 'versions'
    versions_dir.mkdir(parents=True, exist_ok=True)

    # Find all version directories
    versions = []
    if versions_dir.exists():
        for item in sorted(versions_dir.iterdir(), reverse=True):
            if item.is_dir() and not item.name.startswith('.'):
                versions.append(item.name)

    # Add 'latest' link to the most recent version
    if versions:
        latest = versions[0]
    else:
        latest = "dev"

    # Generate HTML index
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaDaR Documentation - Versions</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #5e35b1;
            padding-bottom: 10px;
        }}
        .version-list {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .version-item {{
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #5e35b1;
            background: #f9f9f9;
            border-radius: 4px;
            transition: all 0.3s;
        }}
        .version-item:hover {{
            background: #f0f0f0;
            transform: translateX(5px);
        }}
        .version-item a {{
            color: #5e35b1;
            text-decoration: none;
            font-size: 18px;
            font-weight: 500;
        }}
        .version-item a:hover {{
            text-decoration: underline;
        }}
        .latest-badge {{
            background: #4caf50;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }}
        .dev-badge {{
            background: #ff9800;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }}
        .description {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #999;
        }}
    </style>
</head>
<body>
    <h1>📚 CaDaR Documentation</h1>

    <div class="version-list">
        <h2>Available Versions</h2>

        <div class="version-item">
            <a href="../">Latest (v{latest})</a>
            <span class="latest-badge">RECOMMENDED</span>
            <div class="description">Always points to the most recent stable release</div>
        </div>

"""

    # Add each version
    for version in versions:
        html += f"""        <div class="version-item">
            <a href="versions/{version}/">v{version}</a>
            <div class="description">Documentation for version {version}</div>
        </div>

"""

    # Add development version
    html += """        <div class="version-item">
            <a href="../">Development</a>
            <span class="dev-badge">DEV</span>
            <div class="description">Latest development version from main branch</div>
        </div>
    </div>

    <div class="footer">
        <p>CaDaR - Canonicalization and Darija Representation</p>
        <p><a href="https://github.com/Oit-Technologies/CaDaR" style="color: #5e35b1;">GitHub Repository</a></p>
    </div>
</body>
</html>
"""

    # Write index file
    index_path = versions_dir.parent / 'versions.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated versions index: {index_path}")

    # Also generate versions.json for programmatic access
    versions_json = {
        "latest": latest,
        "versions": versions,
        "dev": True
    }

    json_path = versions_dir.parent / 'versions.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(versions_json, f, indent=2)

    print(f"✓ Generated versions.json: {json_path}")


if __name__ == '__main__':
    generate_versions_index()
