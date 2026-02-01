import markdown
from weasyprint import HTML, CSS

# Read the markdown file
with open('/app/admin_manual.md', 'r') as f:
    md_content = f.read()

# Convert markdown to HTML
md = markdown.Markdown(extensions=['tables', 'toc', 'fenced_code'])
html_content = md.convert(md_content)

# Create styled HTML document
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BOH Hub - Administrator Manual</title>
</head>
<body>
{html_content}
</body>
</html>
"""

# CSS styling for PDF
css = CSS(string="""
@page {
    size: letter;
    margin: 1in;
    @top-center {
        content: "BOH Hub Administrator Manual";
        font-size: 10pt;
        color: #666;
    }
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    color: #1a365d;
    font-size: 24pt;
    border-bottom: 3px solid #3182ce;
    padding-bottom: 10px;
    margin-top: 40px;
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: avoid;
    text-align: center;
    font-size: 32pt;
    margin-top: 0;
}

h2 {
    color: #2c5282;
    font-size: 16pt;
    margin-top: 30px;
    border-bottom: 1px solid #bee3f8;
    padding-bottom: 5px;
}

h3 {
    color: #2b6cb0;
    font-size: 13pt;
    margin-top: 20px;
}

h4 {
    color: #3182ce;
    font-size: 11pt;
    margin-top: 15px;
}

p {
    margin: 10px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 10pt;
}

th, td {
    border: 1px solid #cbd5e0;
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #edf2f7;
    font-weight: bold;
    color: #2d3748;
}

tr:nth-child(even) {
    background-color: #f7fafc;
}

code {
    background-color: #edf2f7;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "Courier New", monospace;
    font-size: 10pt;
}

pre {
    background-color: #2d3748;
    color: #e2e8f0;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    font-size: 9pt;
}

ul, ol {
    margin: 10px 0;
    padding-left: 25px;
}

li {
    margin: 5px 0;
}

strong {
    color: #2d3748;
}

hr {
    border: none;
    border-top: 2px solid #e2e8f0;
    margin: 30px 0;
}

blockquote {
    border-left: 4px solid #3182ce;
    margin: 15px 0;
    padding: 10px 20px;
    background-color: #ebf8ff;
    color: #2c5282;
}

/* Cover page styling */
body > h1:first-of-type {
    margin-top: 200px;
    text-align: center;
}

body > h2:first-of-type {
    text-align: center;
    border: none;
    color: #4a5568;
}

/* Table of contents */
#table-of-contents + ol,
#table-of-contents + ul {
    columns: 2;
    column-gap: 40px;
}

/* Avoid page breaks inside these elements */
table, pre, blockquote {
    page-break-inside: avoid;
}

h2, h3 {
    page-break-after: avoid;
}
""")

# Generate PDF
HTML(string=full_html).write_pdf('/app/frontend/public/BOH_Hub_Admin_Manual.pdf', stylesheets=[css])

print("PDF generated successfully: /app/frontend/public/BOH_Hub_Admin_Manual.pdf")
