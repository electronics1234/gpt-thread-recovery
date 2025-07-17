import os
from datetime import datetime
import pdfkit
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile

load_dotenv()

# Only return data in-memory without writing to disk
def export_to_markdown(messages):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_lines = [
        f"# GPT Conversation Export\n",
        f"**Exported:** {timestamp}\n",
        "---\n"
    ]

    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        md_lines.append(f"### {role}\n")
        md_lines.append(f"{content}\n")
        md_lines.append("---\n")

    return "\n".join(md_lines)

def export_to_pdf(messages):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_lines = [
        f"<h1>GPT Conversation Export</h1>",
        f"<p><b>Exported:</b> {timestamp}</p><hr>"
    ]

    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"].replace("\n", "<br>")
        html_lines.append(f"<h3>{role}</h3><p>{content}</p><hr>")

    html_content = "\n".join(html_lines)
    wkhtmltopdf_path = os.getenv("WKHTMLTOPDF_PATH")
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path) if wkhtmltopdf_path else None

    with NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as html_file:
        html_file.write(html_content)
        html_file_path = html_file.name

    with NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
        pdfkit.from_file(html_file_path, pdf_file.name, configuration=config)
        return pdf_file.name
