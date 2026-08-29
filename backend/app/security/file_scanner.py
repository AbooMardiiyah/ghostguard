"""Upload quarantine + suspicious pattern detection."""

SUSPICIOUS_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".ps1",
    ".sh",
    ".vbs",
    ".js",
    ".scr",
    ".pif",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def scan_upload(filename: str, content: bytes) -> dict:
    """Scan an uploaded file for suspicious patterns. Fail-secure."""
    result = {"filename": filename, "safe": True, "threats": [], "size": len(content)}

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        result["safe"] = False
        result["threats"].append(
            f"File exceeds maximum size ({MAX_FILE_SIZE // 1024 // 1024}MB)"
        )
        return result

    # Check extension
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext in SUSPICIOUS_EXTENSIONS:
        result["safe"] = False
        result["threats"].append(f"Suspicious file extension: {ext}")

    # Check for embedded scripts in CSV/text files
    if ext in (".csv", ".txt", ".tsv"):
        text = content.decode("utf-8", errors="ignore")
        if "=CMD(" in text.upper() or "=SYSTEM(" in text.upper():
            result["safe"] = False
            result["threats"].append("CSV formula injection detected")

    return result
