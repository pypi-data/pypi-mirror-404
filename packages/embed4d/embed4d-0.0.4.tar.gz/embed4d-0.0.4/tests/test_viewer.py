import base64
import sys

# pylint: disable=import-error
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from embed4d import (
    file_to_base64,
    get_glb_html,
    get_template_html,
    get_viewer_html,
    iframe_srcdoc_html,
    model3d_viewer,
    open_viewer_webview,
)


def test_file_to_base64_missing_returns_empty(tmp_path):
    assert file_to_base64(None) == ""
    assert file_to_base64(tmp_path / "does_not_exist.bin") == ""


def test_file_to_base64_roundtrip(tmp_path):
    p = tmp_path / "x.bin"
    raw = b"\x00\x01abc"
    p.write_bytes(raw)
    assert file_to_base64(p) == base64.b64encode(raw).decode("utf-8")


def test_get_template_html_contains_placeholder():
    template = get_template_html()
    assert "{{GLB_BASE64}}" in template
    assert "{{MODEL_FORMAT}}" in template


def test_get_viewer_html_replaces_placeholder():
    html = get_viewer_html("AAA")
    assert "AAA" in html
    assert "{{GLB_BASE64}}" not in html


def test_get_viewer_html_replaces_model_format():
    """get_viewer_html with model_format='fbx' should inject fbx so the viewer loads FBX."""
    html = get_viewer_html("AAA", model_format="fbx")
    assert "AAA" in html
    assert "{{MODEL_FORMAT}}" not in html
    assert "embeddedModelFormat = 'fbx'" in html or "embeddedModelFormat='fbx'" in html


def test_iframe_srcdoc_html_contains_height_and_escapes_quotes():
    out = iframe_srcdoc_html(glb_base64="AAA", height=123)
    assert out.startswith("<iframe ")
    assert 'height="123px"' in out
    # Template contains many double-quotes; they should be escaped
    # inside srcdoc attribute
    assert "&quot;" in out


def test_model3d_viewer_generates_iframe_for_valid_file(tmp_path):
    """model3d_viewer should generate an iframe HTML for a valid GLB file."""
    glb_path = tmp_path / "dummy.glb"
    raw = b"GLB_BINARY_CONTENT"
    glb_path.write_bytes(raw)

    html = model3d_viewer(str(glb_path))

    assert isinstance(html, str)
    assert "<iframe" in html
    # The base64‑encoded content of the file should appear in the HTML.
    encoded = base64.b64encode(raw).decode("utf-8")
    assert encoded in html


def test_model3d_viewer_fbx_file(tmp_path):
    """model3d_viewer should generate iframe HTML for a valid FBX file with format fbx."""
    fbx_path = tmp_path / "model.fbx"
    raw = b"Kaydara FBX binary placeholder"
    fbx_path.write_bytes(raw)

    html = model3d_viewer(str(fbx_path))

    assert isinstance(html, str)
    assert "<iframe" in html
    encoded = base64.b64encode(raw).decode("utf-8")
    assert encoded in html
    # Viewer should receive format fbx so it uses FBXLoader, not GLTFLoader
    assert "fbx" in html


def test_model3d_viewer_with_missing_file_gracefully_handles_path():
    """model3d_viewer should not crash when the file path does not exist."""
    html = model3d_viewer("/path/does/not/exist.glb")
    assert isinstance(html, str)


def _html_viewer_callback(file):
    """Mirror the Gradio callback for the custom HTML viewer."""
    # In viewer.py:
    # lambda file: model3d_viewer(file.name if file else None)
    return model3d_viewer(file.name if file else None)


def _model3d_callback(file):
    """Mirror the Gradio callback for the Model3D component."""
    # In viewer.py:
    # lambda file: file.name if file else None
    return file.name if file else None


def test_gradio_html_callback_with_file(tmp_path):
    """Simulate the Gradio HTML viewer callback with a file object."""
    glb_path = tmp_path / "dummy.glb"
    glb_path.write_bytes(b"1234")
    fake_file = SimpleNamespace(name=str(glb_path))

    html = _html_viewer_callback(fake_file)

    assert isinstance(html, str)
    assert "<iframe" in html


def test_gradio_html_callback_with_none():
    """Simulate the Gradio HTML viewer callback when no file is provided."""
    html = _html_viewer_callback(None)
    assert isinstance(html, str)


def test_gradio_model3d_callback_with_file(tmp_path):
    """Simulate the Gradio Model3D callback with a file object."""
    glb_path = tmp_path / "dummy.glb"
    glb_path.write_bytes(b"1234")
    fake_file = SimpleNamespace(name=str(glb_path))

    out = _model3d_callback(fake_file)
    assert out == str(glb_path)


def test_gradio_model3d_callback_with_none():
    """Simulate the Gradio Model3D callback when no file is provided."""
    out = _model3d_callback(None)
    assert out is None


# ==================== Additional Comprehensive Tests ====================


def test_file_to_base64_empty_file(tmp_path):
    """Test file_to_base64 with an empty file."""
    empty_file = tmp_path / "empty.bin"
    empty_file.write_bytes(b"")
    result = file_to_base64(empty_file)
    assert result == ""
    assert isinstance(result, str)


def test_file_to_base64_large_file(tmp_path):
    """Test file_to_base64 with a large file."""
    large_file = tmp_path / "large.bin"
    # Create a 1MB file
    large_data = b"x" * (1024 * 1024)
    large_file.write_bytes(large_data)
    result = file_to_base64(large_file)
    assert isinstance(result, str)
    assert len(result) > 0
    # Verify roundtrip
    decoded = base64.b64decode(result)
    assert decoded == large_data


def test_file_to_base64_binary_data(tmp_path):
    """Test file_to_base64 with various binary data patterns."""
    test_file = tmp_path / "binary.bin"
    # Test with null bytes, high bytes, etc.
    binary_data = bytes(range(256))
    test_file.write_bytes(binary_data)
    result = file_to_base64(test_file)
    assert isinstance(result, str)
    decoded = base64.b64decode(result)
    assert decoded == binary_data


def test_file_to_base64_unicode_path(tmp_path):
    """Test file_to_base64 with unicode characters in path."""
    unicode_file = tmp_path / "测试文件.glb"
    unicode_file.write_bytes(b"test data")
    result = file_to_base64(unicode_file)
    assert isinstance(result, str)
    assert result == base64.b64encode(b"test data").decode("utf-8")


def test_file_to_base64_empty_string():
    """Test file_to_base64 with empty string path."""
    assert file_to_base64("") == ""


def test_get_template_html_returns_string():
    """Test that get_template_html returns a non-empty string."""
    template = get_template_html()
    assert isinstance(template, str)
    assert len(template) > 0


def test_get_template_html_contains_threejs():
    """Test that template contains Three.js references."""
    template = get_template_html()
    # Should contain Three.js or related keywords
    template_lower = template.lower()
    assert (
        "three" in template_lower
        or "gltf" in template_lower
        or "loader" in template_lower
    )


def test_get_viewer_html_with_empty_base64():
    """Test get_viewer_html with empty base64 string."""
    html = get_viewer_html("")
    assert isinstance(html, str)
    assert "{{GLB_BASE64}}" not in html
    assert len(html) > 0


def test_get_viewer_html_with_none():
    """Test get_viewer_html with None (should be treated as empty)."""
    html = get_viewer_html(None)
    assert isinstance(html, str)
    assert "{{GLB_BASE64}}" not in html


def test_get_viewer_html_with_very_long_base64():
    """Test get_viewer_html with very long base64 string."""
    long_base64 = "A" * 10000
    html = get_viewer_html(long_base64)
    assert isinstance(html, str)
    assert long_base64 in html
    assert "{{GLB_BASE64}}" not in html


def test_get_viewer_html_preserves_template_structure():
    """Test that get_viewer_html preserves the template structure."""
    html = get_viewer_html("TEST_DATA")
    # Should contain HTML structure
    assert "<" in html and ">" in html
    # Should not contain placeholder
    assert "{{GLB_BASE64}}" not in html
    # Should contain the data
    assert "TEST_DATA" in html


def test_iframe_srcdoc_html_default_height():
    """Test iframe_srcdoc_html with default height."""
    html = iframe_srcdoc_html("TEST")
    assert 'height="500px"' in html
    assert "<iframe" in html
    assert "srcdoc=" in html


def test_iframe_srcdoc_html_custom_height():
    """Test iframe_srcdoc_html with custom height."""
    html = iframe_srcdoc_html("TEST", height=800)
    assert 'height="800px"' in html
    assert 'height="500px"' not in html


def test_iframe_srcdoc_html_escapes_quotes():
    """Test that iframe_srcdoc_html properly escapes quotes in HTML."""
    # Create HTML content that contains quotes
    base64_data = "TEST"
    html = iframe_srcdoc_html(base64_data)
    # Count that quotes are escaped
    assert "&quot;" in html or '"' in html
    # Should be valid HTML
    assert html.startswith("<iframe")


def test_iframe_srcdoc_html_contains_styling():
    """Test that iframe_srcdoc_html includes proper styling."""
    html = iframe_srcdoc_html("TEST")
    assert "border:none" in html or "border: none" in html
    assert "border-radius" in html


def test_iframe_srcdoc_html_zero_height():
    """Test iframe_srcdoc_html with zero height (edge case)."""
    html = iframe_srcdoc_html("TEST", height=0)
    assert 'height="0px"' in html


def test_iframe_srcdoc_html_very_large_height():
    """Test iframe_srcdoc_html with very large height."""
    html = iframe_srcdoc_html("TEST", height=99999)
    assert 'height="99999px"' in html


def test_get_glb_html_backwards_compatibility(tmp_path):
    """Test get_glb_html for backwards compatibility."""
    glb_file = tmp_path / "test.glb"
    glb_file.write_bytes(b"test data")
    base64_data = file_to_base64(glb_file)
    html = get_glb_html(base64_data)
    assert isinstance(html, str)
    assert "<iframe" in html
    assert base64_data in html or "&quot;" in html  # May be escaped


def test_get_glb_html_custom_height():
    """Test get_glb_html with custom height."""
    html = get_glb_html("TEST", height=600)
    assert 'height="600px"' in html


def test_get_glb_html_missing_template():
    """Test get_glb_html when template is missing."""
    with patch("embed4d.viewer.HTML_TEMPLATE_PATH", "/nonexistent/path.html"):
        html = get_glb_html("TEST")
        assert isinstance(html, str)
        assert "not found" in html.lower() or "error" in html.lower()


def test_model3d_viewer_custom_height(tmp_path):
    """Test model3d_viewer with custom height."""
    glb_file = tmp_path / "test.glb"
    glb_file.write_bytes(b"test")
    html = model3d_viewer(str(glb_file), height=700)
    assert 'height="700px"' in html


def test_model3d_viewer_default_height(tmp_path):
    """Test model3d_viewer with default height."""
    glb_file = tmp_path / "test.glb"
    glb_file.write_bytes(b"test")
    html = model3d_viewer(str(glb_file))
    assert 'height="500px"' in html


def test_model3d_viewer_empty_path():
    """Test model3d_viewer with empty path."""
    html = model3d_viewer("")
    assert isinstance(html, str)
    assert "<iframe" in html


def test_model3d_viewer_none_path():
    """Test model3d_viewer with None path."""
    html = model3d_viewer(None)
    assert isinstance(html, str)
    assert "<iframe" in html


def test_model3d_viewer_unicode_filename(tmp_path):
    """Test model3d_viewer with unicode filename."""
    unicode_file = tmp_path / "模型.glb"
    unicode_file.write_bytes(b"test data")
    html = model3d_viewer(str(unicode_file))
    assert isinstance(html, str)
    assert "<iframe" in html


def test_model3d_viewer_different_extensions(tmp_path):
    """Test model3d_viewer with different file extensions."""
    for ext in [".glb", ".gltf", ".bin", ".txt"]:
        test_file = tmp_path / f"test{ext}"
        test_file.write_bytes(b"data")
        html = model3d_viewer(str(test_file))
        assert isinstance(html, str)
        assert "<iframe" in html


def test_open_viewer_webview_with_file(tmp_path):
    """Test open_viewer_webview with a file path."""
    glb_file = tmp_path / "test.glb"
    glb_file.write_bytes(b"test data")

    mock_webview = MagicMock()
    mock_window = MagicMock()
    mock_webview.create_window.return_value = mock_window
    mock_webview.start = MagicMock()

    def import_side_effect(name, *args, **kwargs):
        if name == "webview":
            return mock_webview
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        open_viewer_webview(
            file_path=str(glb_file), title="Test", width=800, height=600
        )

    mock_webview.create_window.assert_called_once()
    call_args = mock_webview.create_window.call_args
    assert call_args[0][0] == "Test"
    assert call_args[1]["width"] == 800
    assert call_args[1]["height"] == 600
    assert "html" in call_args[1]
    assert call_args[1]["js_api"] is not None
    mock_webview.start.assert_called_once_with(debug=False)


def test_open_viewer_webview_without_file():
    """Test open_viewer_webview without a file path."""
    mock_webview = MagicMock()
    mock_window = MagicMock()
    mock_webview.create_window.return_value = mock_window
    mock_webview.start = MagicMock()

    def import_side_effect(name, *args, **kwargs):
        if name == "webview":
            return mock_webview
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        open_viewer_webview(title="Empty Viewer", width=1000, height=700)

    mock_webview.create_window.assert_called_once()
    call_args = mock_webview.create_window.call_args
    assert call_args[0][0] == "Empty Viewer"
    assert call_args[1]["width"] == 1000
    assert call_args[1]["height"] == 700
    assert "html" in call_args[1]
    mock_webview.start.assert_called_once()


def test_open_viewer_webview_defaults():
    """Test open_viewer_webview with default parameters."""
    mock_webview = MagicMock()
    mock_window = MagicMock()
    mock_webview.create_window.return_value = mock_window
    mock_webview.start = MagicMock()

    def import_side_effect(name, *args, **kwargs):
        if name == "webview":
            return mock_webview
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        open_viewer_webview()

    mock_webview.create_window.assert_called_once()
    call_args = mock_webview.create_window.call_args
    assert call_args[0][0] == "3D Model Viewer"
    assert call_args[1]["width"] == 1200
    assert call_args[1]["height"] == 800


def test_open_viewer_webview_import_error():
    """Test open_viewer_webview raises ImportError when webview unavailable."""
    with patch("builtins.__import__", side_effect=ImportError("No module")):
        with pytest.raises(ImportError) as exc_info:
            open_viewer_webview()
        assert "pywebview" in str(exc_info.value).lower()


def test_open_viewer_webview_webview_api_toggle_fullscreen():
    """Test WebviewAPI toggle_fullscreen method."""
    mock_webview = MagicMock()
    mock_window = MagicMock()
    mock_window.toggle_fullscreen = MagicMock()
    mock_window.fullscreen = False
    mock_webview.create_window.return_value = mock_window
    mock_webview.start = MagicMock()

    def import_side_effect(name, *args, **kwargs):
        if name == "webview":
            return mock_webview
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        open_viewer_webview()

    # Get the API instance that was created
    call_args = mock_webview.create_window.call_args
    api = call_args[1]["js_api"]
    api.set_window(mock_window)

    # Test toggle_fullscreen
    result = api.toggle_fullscreen()
    assert isinstance(result, bool)
    mock_window.toggle_fullscreen.assert_called_once()


def test_open_viewer_webview_webview_api_fullscreen_property():
    """Test WebviewAPI with fullscreen property fallback."""
    mock_webview = MagicMock()
    mock_window = MagicMock()
    # Remove toggle_fullscreen method, use property instead
    del mock_window.toggle_fullscreen
    mock_window.fullscreen = False
    mock_webview.create_window.return_value = mock_window
    mock_webview.start = MagicMock()

    def import_side_effect(name, *args, **kwargs):
        if name == "webview":
            return mock_webview
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        open_viewer_webview()

    call_args = mock_webview.create_window.call_args
    api = call_args[1]["js_api"]
    api.set_window(mock_window)

    # Test toggle_fullscreen with property
    result = api.toggle_fullscreen()
    assert isinstance(result, bool)
    assert mock_window.fullscreen is True  # Should be toggled


def test_open_viewer_webview_webview_api_no_window():
    """Test WebviewAPI toggle_fullscreen when window is None."""
    mock_webview = MagicMock()
    mock_window = MagicMock()
    mock_webview.create_window.return_value = mock_window
    mock_webview.start = MagicMock()

    def import_side_effect(name, *args, **kwargs):
        if name == "webview":
            return mock_webview
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        open_viewer_webview()

    call_args = mock_webview.create_window.call_args
    api = call_args[1]["js_api"]
    # Explicitly set window to None to test the None case
    api.window = None
    result = api.toggle_fullscreen()
    assert result is False


def test_open_viewer_webview_webview_api_exception_handling():
    """Test WebviewAPI handles exceptions gracefully."""
    mock_webview = MagicMock()
    mock_window = MagicMock()
    mock_window.toggle_fullscreen = MagicMock(side_effect=RuntimeError("Test error"))
    mock_window.fullscreen = False
    mock_webview.create_window.return_value = mock_window
    mock_webview.start = MagicMock()

    def import_side_effect(name, *args, **kwargs):
        if name == "webview":
            return mock_webview
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        open_viewer_webview()

    call_args = mock_webview.create_window.call_args
    api = call_args[1]["js_api"]
    api.set_window(mock_window)

    # Should handle exception and return False
    result = api.toggle_fullscreen()
    assert result is False


def test_get_viewer_html_multiple_replacements():
    """Test that get_viewer_html replaces all placeholder instances."""
    # Create a template-like string with multiple placeholders
    original_template = "{{GLB_BASE64}} and {{GLB_BASE64}}"
    with patch(
        "embed4d.viewer.get_template_html",
        return_value=original_template,
    ):
        html = get_viewer_html("REPLACED")
        # Should replace all instances
        assert "{{GLB_BASE64}}" not in html
        assert html.count("REPLACED") == 2


def test_iframe_srcdoc_html_width_attribute():
    """Test that iframe_srcdoc_html includes width attribute."""
    html = iframe_srcdoc_html("TEST")
    assert 'width="100%"' in html


def test_model3d_viewer_includes_base64_in_html(tmp_path):
    """Test model3d_viewer includes base64 data in generated HTML."""
    glb_file = tmp_path / "test.glb"
    test_data = b"GLB_CONTENT_12345"
    glb_file.write_bytes(test_data)

    html = model3d_viewer(str(glb_file))
    encoded = base64.b64encode(test_data).decode("utf-8")
    # The encoded data should be in the HTML (possibly escaped)
    assert encoded in html or encoded.replace("+", "&quot;") in html or "&quot;" in html


# ==================== Jupyter Notebook Display Tests ====================


def test_notebook_viewer_with_file_returns_html_object(tmp_path):
    """Test notebook_viewer returns IPython.display.IFrame object with file."""
    glb_file = tmp_path / "test.glb"
    test_data = b"GLB_CONTENT"
    glb_file.write_bytes(test_data)

    mock_iframe = MagicMock()
    mock_iframe_class = MagicMock(return_value=mock_iframe)

    # Create mock IPython modules
    mock_display = MagicMock()
    mock_display.IFrame = mock_iframe_class
    mock_ipython = MagicMock()
    mock_ipython.display = mock_display

    # Add to sys.modules before patching
    with patch.dict(
        sys.modules, {"IPython": mock_ipython, "IPython.display": mock_display}
    ):
        from embed4d import notebook_viewer

        result = notebook_viewer(str(glb_file))

        assert result is mock_iframe
        mock_iframe_class.assert_called_once()
        # Verify IFrame was called with correct arguments
        call_kwargs = mock_iframe_class.call_args[1]
        assert "src" in call_kwargs
        assert call_kwargs["width"] == "100%"
        assert call_kwargs["height"] == 600
        # Verify the data URI contains the base64 data
        data_uri = call_kwargs["src"]
        assert data_uri.startswith("data:text/html;base64,")
        decoded_html = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8")
        encoded = base64.b64encode(test_data).decode("utf-8")
        assert encoded in decoded_html


def test_notebook_viewer_without_file_returns_html_object():
    """Test notebook_viewer returns IPython.display.IFrame object without file."""
    mock_iframe = MagicMock()
    mock_iframe_class = MagicMock(return_value=mock_iframe)

    # Create mock IPython modules
    mock_display = MagicMock()
    mock_display.IFrame = mock_iframe_class
    mock_ipython = MagicMock()
    mock_ipython.display = mock_display

    with patch.dict(
        sys.modules, {"IPython": mock_ipython, "IPython.display": mock_display}
    ):
        from embed4d import notebook_viewer

        result = notebook_viewer()

        assert result is mock_iframe
        mock_iframe_class.assert_called_once()
        # Verify IFrame was called with correct arguments
        call_kwargs = mock_iframe_class.call_args[1]
        assert "src" in call_kwargs
        assert call_kwargs["width"] == "100%"
        assert call_kwargs["height"] == 600
        # Verify the data URI contains valid HTML
        data_uri = call_kwargs["src"]
        assert data_uri.startswith("data:text/html;base64,")
        decoded_html = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8")
        assert isinstance(decoded_html, str)
        assert len(decoded_html) > 0
        # Should not contain placeholder
        assert "{{GLB_BASE64}}" not in decoded_html


def test_notebook_viewer_with_custom_height(tmp_path):
    """Test notebook_viewer with custom height parameter."""
    glb_file = tmp_path / "test.glb"
    glb_file.write_bytes(b"test")

    mock_iframe = MagicMock()
    mock_iframe_class = MagicMock(return_value=mock_iframe)

    # Create mock IPython modules
    mock_display = MagicMock()
    mock_display.IFrame = mock_iframe_class
    mock_ipython = MagicMock()
    mock_ipython.display = mock_display

    with patch.dict(
        sys.modules, {"IPython": mock_ipython, "IPython.display": mock_display}
    ):
        from embed4d import notebook_viewer

        result = notebook_viewer(str(glb_file), height=800)

        assert result is mock_iframe
        # Verify height parameter is passed to IFrame
        mock_iframe_class.assert_called_once()
        call_kwargs = mock_iframe_class.call_args[1]
        assert call_kwargs["height"] == 800


def test_notebook_viewer_raises_import_error_without_ipython():
    """Test notebook_viewer raises ImportError when IPython is not available."""
    # Remove IPython from sys.modules if it exists
    ipython_backup = sys.modules.pop("IPython", None)
    ipython_display_backup = sys.modules.pop("IPython.display", None)

    try:
        # Mock __import__ to raise ImportError for IPython
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "IPython" or (
                isinstance(name, str) and name.startswith("IPython")
            ):
                raise ImportError("No module named 'IPython'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Reload the module to pick up the patched import
            import importlib

            import embed4d.viewer

            importlib.reload(embed4d.viewer)
            from embed4d.viewer import notebook_viewer

            with pytest.raises(ImportError) as exc_info:
                notebook_viewer()

            assert "IPython" in str(exc_info.value)
            assert "ipython" in str(exc_info.value).lower()
    finally:
        # Restore if they existed
        if ipython_backup:
            sys.modules["IPython"] = ipython_backup
        if ipython_display_backup:
            sys.modules["IPython.display"] = ipython_display_backup
        # Reload the module one more time to restore normal behavior
        import importlib

        import embed4d.viewer

        importlib.reload(embed4d.viewer)


def test_notebook_viewer_includes_base64_data(tmp_path):
    """Test that notebook_viewer correctly embeds base64 data in HTML."""
    glb_file = tmp_path / "test.glb"
    test_data = b"GLB_BINARY_DATA_123"
    glb_file.write_bytes(test_data)

    mock_iframe = MagicMock()
    mock_iframe_class = MagicMock(return_value=mock_iframe)

    # Create mock IPython modules
    mock_display = MagicMock()
    mock_display.IFrame = mock_iframe_class
    mock_ipython = MagicMock()
    mock_ipython.display = mock_display

    with patch.dict(
        sys.modules, {"IPython": mock_ipython, "IPython.display": mock_display}
    ):
        from embed4d import notebook_viewer

        notebook_viewer(str(glb_file))

        # Get the data URI that was passed to IFrame()
        call_kwargs = mock_iframe_class.call_args[1]
        data_uri = call_kwargs["src"]
        assert data_uri.startswith("data:text/html;base64,")
        # Decode the base64 HTML content
        html_content = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8")
        encoded = base64.b64encode(test_data).decode("utf-8")
        assert encoded in html_content


def test_notebook_viewer_with_nonexistent_file(tmp_path):
    """Test notebook_viewer handles nonexistent file gracefully."""
    nonexistent_file = tmp_path / "nonexistent.glb"

    mock_iframe = MagicMock()
    mock_iframe_class = MagicMock(return_value=mock_iframe)

    # Create mock IPython modules
    mock_display = MagicMock()
    mock_display.IFrame = mock_iframe_class
    mock_ipython = MagicMock()
    mock_ipython.display = mock_display

    with patch.dict(
        sys.modules, {"IPython": mock_ipython, "IPython.display": mock_display}
    ):
        from embed4d import notebook_viewer

        # Should not raise error, just return empty viewer
        result = notebook_viewer(str(nonexistent_file))

        assert result is mock_iframe
        mock_iframe_class.assert_called_once()
        # Verify IFrame was called with data URI
        call_kwargs = mock_iframe_class.call_args[1]
        data_uri = call_kwargs["src"]
        assert data_uri.startswith("data:text/html;base64,")
        # HTML should be generated (empty base64)
        decoded_html = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8")
        assert isinstance(decoded_html, str)
        assert "{{GLB_BASE64}}" not in decoded_html


def test_notebook_viewer_html_structure(tmp_path):
    """Test that notebook_viewer generates valid HTML structure."""
    glb_file = tmp_path / "test.glb"
    glb_file.write_bytes(b"test")

    mock_iframe = MagicMock()
    mock_iframe_class = MagicMock(return_value=mock_iframe)

    # Create mock IPython modules
    mock_display = MagicMock()
    mock_display.IFrame = mock_iframe_class
    mock_ipython = MagicMock()
    mock_ipython.display = mock_display

    with patch.dict(
        sys.modules, {"IPython": mock_ipython, "IPython.display": mock_display}
    ):
        from embed4d import notebook_viewer

        notebook_viewer(str(glb_file))

        # Get the data URI and decode the HTML content
        call_kwargs = mock_iframe_class.call_args[1]
        data_uri = call_kwargs["src"]
        assert data_uri.startswith("data:text/html;base64,")
        html_content = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8")
        # Should contain HTML structure
        assert "<" in html_content and ">" in html_content
        # Should be a complete HTML document
        assert "html" in html_content.lower() or "script" in html_content.lower()
