import os
from datetime import datetime
from io import BytesIO
from xhtml2pdf import pisa

def export_to_markdown(messages, filename="chat_export"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_lines = [f"# GPT Conversation Export\n", f"**File:** {filename}", f"**Exported:** {timestamp}\n", "---\n"]

    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        md_lines.append(f"### {role}\n")
        md_lines.append(f"{content}\n")
        md_lines.append("---\n")

    return "\n".join(md_lines)

def export_to_pdf(messages):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    html = f"""
    <html>
    <head>
    <style>
    body {{ font-family: Arial; padding: 20px; }}
    h1 {{ color: #2c3e50; }}
    .role {{ font-weight: bold; margin-top: 20px; }}
    .msg {{ margin-bottom: 10px; }}
    </style>
    </head>
    <body>
    <h1>GPT Conversation Export</h1>
    <p><b>Exported:</b> {timestamp}</p><hr>
    """

    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"].replace("\n", "<br>")
        html += f"<div class='role'>{role}</div><div class='msg'>{content}</div><hr>"

    html += "</body></html>"

    pdf_bytes = BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_bytes)
    if pisa_status.err:
        return None

    pdf_bytes.seek(0)
    return pdf_bytes
