## embed4d
<!-- [![codecov](https://codecov.io/gh/myolab/embed4d/branch/main/graph/badge.svg)](https://codecov.io/gh/myolab/embed4d) -->
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](
https://colab.research.google.com/drive/1gXGBUu-QONjA4K3tgm7IwD2DBD2zPBVe?usp=sharing)
![PyPI - License](https://img.shields.io/pypi/l/myosuite)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/myohub/myosuite/blob/main/docs/CONTRIBUTING.md)
[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/caggianov/embed4d)


**Embed 4D (3D + time)** — lightweight GLB/GLTF/FBX animation viewer with:

- **Python package**: `embed4d` (import as `embed4d`)
- **Jupyter notebook integration** for inline 3D model viewing
- **Embeddable HTML viewer** for Gradio or any web UI
- **FastAPI server** for serving models over HTTP
- **Static HTML app** for drag‑and‑drop viewing of models


### 1. Python Installation

#### From PyPI

```bash
pip install embed4d
```

#### From source (this repo)

Inside the repo root:

```bash
# Using pip
pip install -e .

# Or using uv (faster, recommended for dev)
uv pip install -e .
```


#### 1. Python API

The core helpers live in `embed4d.viewer` and are re‑exported at the package root.

```python
from embed4d import open_viewer_webview

open_viewer_webview("motion.glb")
```

---

#### 2. 🤗 [Gradio](https://www.gradio.app/) integration [![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/caggianov/embed4d)

The file `examples/demo_gradio.py` contains a small demo that compares:

- A **custom HTML viewer** using `gr.HTML`
- Gradio’s built‑in **`gr.Model3D`** component

You typically want to use `iframe_srcdoc_html` or `model3d_viewer` from your own Gradio app:

```python
import gradio as gr
from embed4d import model3d_viewer

with gr.Blocks() as demo:
    file_input = gr.File(file_types=[".glb"], label="Select GLB File")
    viewer_output = gr.HTML()

    file_input.change(
        lambda file: model3d_viewer(file.name if file else None),
        inputs=file_input,
        outputs=viewer_output,
    )

demo.launch()
```


---

### 3. FastAPI Server

The package includes a FastAPI server for serving the 3D viewer via HTTP. This is useful for:
- Serving models over a network
- Embedding the viewer in web applications
- Sharing models with others via a URL

#### Python API

```python
from embed4d.viewer_server import launch

# Launch server with automatic port selection
url = launch()
print(f"Viewer available at: {url}")

# Launch server on a specific port
url = launch(port=8080)

# Launch server with a model file
url = launch(port=8080, model_file="motion.glb")
```

#### Command Line Interface

You can also run the server directly from the command line:

```bash
# Start server with automatic port selection
python -m embed4d.viewer_server

# Start server on a specific port
python -m embed4d.viewer_server --port 8080

# Start server with a model file
python -m embed4d.viewer_server --port 8080 --model motion.glb
```

The server provides two endpoints:
- `GET /` - Returns the HTML viewer (with embedded model if provided)
- `GET /model` - Returns the GLB model file (if provided)

The server runs in a background thread and returns the URL where the viewer is accessible.


---

### 4. Inside Jupyter Notebook or Colab [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1gXGBUu-QONjA4K3tgm7IwD2DBD2zPBVe?usp=sharing)

Display 3D GLB/GLTF models directly in Jupyter notebook cells using `notebook_viewer`. This function embeds the viewer as an iframe, making it easy to visualize models alongside your code.

#### Basic Usage

```python
from embed4d import notebook_viewer

# Display a model from a file path
notebook_viewer("path/to/model.glb")

# Display with custom height
notebook_viewer("model.glb", height=800)

# Display empty viewer (for drag-and-drop)
notebook_viewer()
```

#### Requirements

- **IPython** must be installed: `pip install ipython`
- Works in Jupyter Notebook, JupyterLab, and other IPython-compatible environments
- Requires a modern browser with WebGL support

#### Features

- **Inline rendering**: Viewer displays directly in notebook cells
- **File embedding**: GLB files are base64-encoded and embedded in the HTML
- **Interactive controls**: Full keyboard shortcuts and mouse controls
- **Animation playback**: Supports animated GLB files with timeline controls

---
### 5. Static HTML viewer

The package ships a pre‑built Three.js viewer template at:

- `embed4d/templates/index.html`

This is the same HTML that’s used for:

- `get_viewer_html` and `iframe_srcdoc_html`
- Any exported HTML file produced by the CLI

#### Running tests

```bash
pytest
# or, with uv:
uv run pytest
```

#### Linting / formatting

This project uses `ruff` via config in `pyproject.toml`. If you have `ruff` installed:

```bash
ruff check .
```

(CI will run linting for you; see `.github/workflows/`.)

---

### 6. Working on the HTML/Three.js viewer

The main viewer template is:

- `embed4d/templates/index.html`

It is self‑contained:

- Uses CDN Three.js + GLTFLoader
- Supports drag & drop `.glb`/`.gltf`
- Provides keyboard shortcuts, skeleton toggle, ground plane, etc.

Workflow:

1. Edit the HTML/JS in `embed4d/templates/index.html`.
2. Run the Python tests to ensure the template still contains the `{{GLB_BASE64}}` placeholder and that the iframe generation works.
3. Rebuild / re‑publish the package as needed.
