import base64
import email.utils
import quopri
from email.message import Message
from email.utils import parseaddr
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

def decode_base64_url(data: str) -> bytes:
    """
    Decode a Base64-url-encoded string (Gmail API uses URL-safe Base64).
    """
    data = data.replace('-', '+').replace('_', '/')
    # Fix padding
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.b64decode(data)


def _get_charset(headers_list: List[Dict[str, str]], mime_type: str) -> Optional[str]:
    content_type = find_header(headers_list, "Content-Type") or mime_type or ""
    if not content_type:
        return None
    msg = Message()
    msg["Content-Type"] = content_type
    return msg.get_content_charset()


def _decode_transfer_encoding(payload: bytes, transfer_encoding: str) -> bytes:
    encoding = (transfer_encoding or "").lower()
    if "quoted-printable" in encoding:
        return quopri.decodestring(payload)
    if "base64" in encoding:
        try:
            return base64.b64decode(payload, validate=False)
        except Exception:
            return payload
    return payload


_MOJIBAKE_MARKERS = (
    "\u00e2\u0080\u0099",
    "\u00e2\u0080\u0093",
    "\u00e2\u0080\u0094",
    "\u00e2\u0080\u009c",
    "\u00e2\u0080\u009d",
    "\u00e2\u0080\u00a6",
    "\u00c3\u00a9",
    "\u00c3\u00a0",
    "\u00c3\u00b6",
)


def _repair_mojibake(text: str) -> str:
    if not text or not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text
    if any(marker in repaired for marker in _MOJIBAKE_MARKERS):
        return text
    return repaired


def _decode_part_text(
    data: str, headers_list: List[Dict[str, str]], mime_type: str
) -> str:
    raw_bytes = decode_base64_url(data)
    transfer_encoding = find_header(headers_list, "Content-Transfer-Encoding") or ""
    decoded_bytes = _decode_transfer_encoding(raw_bytes, transfer_encoding)

    charset = _get_charset(headers_list, mime_type)
    tried = [charset, "utf-8", "windows-1252", "latin-1"]
    for enc in [e for e in tried if e]:
        try:
            text = decoded_bytes.decode(enc)
            return _repair_mojibake(text)
        except (LookupError, UnicodeDecodeError):
            continue
    return _repair_mojibake(decoded_bytes.decode("utf-8", errors="replace"))


def parse_plain_text_from_parts(parts: List[Dict[str, Any]]) -> str:
    """
    Recursively parse payload parts to extract all text (plain or HTML).
    HTML is converted to plain text.
    """
    text_chunks: List[str] = []
    for part in parts:
        if 'parts' in part:
            # Recursively parse nested parts
            text_chunks.append(parse_plain_text_from_parts(part['parts']))
        else:
            mime_type = part.get('mimeType', '')
            data = part.get('body', {}).get('data', '')
            if data:
                decoded_data = _decode_part_text(
                    data, part.get("headers", []), mime_type
                )
                if 'text/plain' in mime_type:
                    text_chunks.append(decoded_data)
                elif 'text/html' in mime_type:
                    soup = BeautifulSoup(decoded_data, 'html.parser')
                    text_chunks.append(soup.get_text())
    return "\n".join(chunk for chunk in text_chunks if chunk)


def extract_email_body_in_plain_text(message_data: Dict[str, Any]) -> str:
    """
    Extract the email body from the Gmail message_data in plain text.
    Converts any HTML to plain text. 
    Combines multiple parts if necessary.
    """
    payload = message_data.get('payload', {})
    # If top-level body has data (i.e. single-part message)
    if payload.get('body', {}).get('data'):
        raw_data = payload['body']['data']
        decoded_data = _decode_part_text(
            raw_data, payload.get("headers", []), payload.get("mimeType", "")
        )
        # Check if it might be HTML
        mime_type = payload.get('mimeType', '')
        if 'text/html' in mime_type:
            soup = BeautifulSoup(decoded_data, 'html.parser')
            return soup.get_text()
        return decoded_data

    # If multiple parts exist
    if 'parts' in payload:
        return parse_plain_text_from_parts(payload['parts'])

    return ""


def convert_date_to_iso(date_str: str) -> str:
    """
    Convert a date string (RFC 2822/5322) to an ISO 8601 formatted string.
    Example: "Wed, 07 Apr 2021 16:30:00 -0700" -> "2021-04-07T16:30:00-07:00"
    """
    dt = email.utils.parsedate_to_datetime(date_str)
    if not dt:
        return ""
    return dt.isoformat()


def find_header(headers_list: List[Dict[str, str]], header_name: str) -> Optional[str]:
    """
    Return the first matching header value for header_name, or None if not found.
    """
    for h in headers_list:
        if h['name'].lower() == header_name.lower():
            return h['value']
    return None


def parse_single_address(display_str: str) -> Tuple[str, str]:
    """
    Parses a single display string like "Alice <alice@example.com>" 
    returning (name, email).
    """
    name, email = parseaddr(display_str)
    # If no name is given, might be email only
    return (name.strip() or "", email.strip() or "")


def parse_address_list(display_str: str) -> List[Tuple[str, str]]:
    """
    Split a header string with possibly multiple addresses into a list
    of (name, email) tuples.
    
    Example input:
      "John Doe <john@example.com>, Jane Roe <jane@example.com>"
    returns:
      [("John Doe","john@example.com"), ("Jane Roe","jane@example.com")]
    """
    # The standard library doesn't have a direct "splitall addresses" 
    # but we can rely on email.utils.getaddresses
    # We'll break them into a list of (name, email).
    addresses = email.utils.getaddresses([display_str])
    return addresses


def find_all_recipients_in_headers(headers_list: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Collect 'To', 'Cc', 'Bcc' headers, parse each address, and return:
      (comma-separated receiver names, comma-separated receiver emails)
    """
    full_str = []
    for h in headers_list:
        if h['name'].lower() in ['to', 'cc', 'bcc']:
            full_str.append(h['value'])
    if not full_str:
        return ("", "")  # No recipients found

    combined_str = ", ".join(full_str)
    addresses = parse_address_list(combined_str)
    names = [addr[0] for addr in addresses if addr[0] or addr[1]]
    emails = [addr[1] for addr in addresses if addr[0] or addr[1]]

    return (", ".join(names), ", ".join(emails))
