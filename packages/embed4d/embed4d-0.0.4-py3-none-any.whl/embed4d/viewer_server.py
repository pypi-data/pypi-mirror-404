import argparse
import os
import socket
import threading
import time

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from embed4d.utilities import file_to_base64

# ------------------ Paths ------------------
BASE_DIR = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "index.html")
MODEL_FILE = None  # optional GLB file from CLI


# ------------------ FastAPI app ------------------

app = FastAPI()


@app.get("/")
def viewer():
    """Serve the HTML viewer with base64 GLB embedded if provided."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_template = f.read()

    glb_base64 = file_to_base64(MODEL_FILE) if MODEL_FILE else ""
    html = html_template.replace("{{GLB_BASE64}}", glb_base64)

    return HTMLResponse(html)


@app.get("/model")
def get_model():
    """Serve the GLB model if provided"""
    if not MODEL_FILE:
        return {"error": "No model file provided"}
    return FileResponse(MODEL_FILE, media_type="model/gltf-binary")


# ------------------ Utilities ------------------


def find_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ------------------ Main launcher ------------------


def launch(port=None, model_file=None):
    global MODEL_FILE

    if model_file:
        if not os.path.isfile(model_file):
            raise FileNotFoundError(f"Model file not found: {model_file}")
        MODEL_FILE = os.path.abspath(model_file)

    if port is None:
        port = find_free_port()

    print(f"🚀 Starting FastAPI on http://localhost:{port}")
    if MODEL_FILE:
        print(f"🗂 Serving model: {MODEL_FILE}")
    else:
        print("🗂 No model file provided. Viewer will start empty.")

    def run_api():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

    t = threading.Thread(target=run_api, daemon=True)
    t.start()

    time.sleep(1.5)  # give server a moment to start
    return f"http://localhost:{port}"


# ------------------ CLI ------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the 3D GLB viewer server.")
    parser.add_argument(
        "--port", "-p", type=int, default=None, help="Port to run the server on"
    )
    parser.add_argument(
        "--model", "-m", type=str, default=None, help="Path to the .glb model file"
    )

    args = parser.parse_args()

    url = launch(port=args.port, model_file=args.model)

    print("\nViewer ready:")
    print(url)
    print("\nPress Ctrl+C to stop")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nShutting down...")
