import base64
import os


def file_to_base64(file_path: str):
    """Convert a file to base64 string."""
    if not file_path or not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
