from bs4 import BeautifulSoup
import email
from email import policy

def parse_mhtml(uploaded_file):
    raw_bytes = uploaded_file.read()

    # Parse multipart .mhtml structure
    msg = email.message_from_bytes(raw_bytes, policy=policy.default)
    html_content = None

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html_payload = part.get_payload(decode=True)
            charset = part.get_content_charset() or "utf-8"
            html_content = html_payload.decode(charset, errors="replace")
            break

    if not html_content:
        raise ValueError("No HTML content found in .mhtml file.")

    soup = BeautifulSoup(html_content, "lxml")
    messages = []
    index = 0

    # Extract all divs in document order and tag role dynamically
    all_divs = soup.find_all("div")
    for div in all_divs:
        class_list = div.get("class") or []
        content = div.get_text(separator="\n", strip=True)
        if not content:
            continue

        cleaned = content.replace('\uFFFD', '').strip()
        if not cleaned:
            continue

        if "prose" in class_list and "markdown" in class_list:
            role = "assistant"
        elif "whitespace-pre-wrap" in class_list:
            role = "user"
        else:
            continue  # Skip unknown roles

        messages.append({
            "index": index,
            "role": role,
            "content": cleaned
        })
        index += 1

    if not messages:
        raise ValueError("No messages found. File may be unsupported or empty.")

    return messages
