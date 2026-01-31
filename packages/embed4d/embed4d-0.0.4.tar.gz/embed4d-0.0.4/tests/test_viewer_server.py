import os
import socket
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from embed4d.viewer_server import app, find_free_port, launch


class TestFindFreePort:
    """Tests for find_free_port function."""

    def test_find_free_port_returns_valid_port(self):
        """Test that find_free_port returns a valid port number."""
        port = find_free_port()
        assert isinstance(port, int)
        assert 1024 <= port <= 65535  # Valid port range

    def test_find_free_port_returns_different_ports(self):
        """Test that find_free_port can return different ports."""
        port1 = find_free_port()
        port2 = find_free_port()
        # They might be the same or different, but both should be valid
        assert isinstance(port1, int)
        assert isinstance(port2, int)
        assert 1024 <= port1 <= 65535
        assert 1024 <= port2 <= 65535

    def test_find_free_port_port_is_available(self):
        """Test that the returned port is actually available."""
        port = find_free_port()
        # Try to bind to the port to verify it's free
        s = socket.socket()
        try:
            s.bind(("", port))
            s.listen(1)
            # If we get here, the port is available
            assert True
        except OSError:
            pytest.fail(f"Port {port} is not available")
        finally:
            s.close()


class TestFastAPIEndpoints:
    """Tests for FastAPI endpoints."""

    def test_root_endpoint_returns_html(self):
        """Test that the root endpoint returns HTML."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert isinstance(response.text, str)
        assert len(response.text) > 0

    def test_root_endpoint_contains_template_content(self):
        """Test that the root endpoint contains template HTML."""
        client = TestClient(app)
        response = client.get("/")
        html = response.text
        # Should contain HTML structure
        assert "<" in html and ">" in html
        # Should not contain the placeholder (it gets replaced with empty string if no model)
        assert "{{GLB_BASE64}}" not in html

    def test_model_endpoint_without_model_returns_error(self):
        """Test that /model endpoint returns error when no model is set."""
        # Reset MODEL_FILE to None
        from embed4d import viewer_server

        original_model = viewer_server.MODEL_FILE
        try:
            viewer_server.MODEL_FILE = None
            client = TestClient(app)
            response = client.get("/model")
            assert response.status_code == 200
            assert response.json() == {"error": "No model file provided"}
        finally:
            viewer_server.MODEL_FILE = original_model

    def test_model_endpoint_with_model_returns_file(self, tmp_path):
        """Test that /model endpoint returns file when model is set."""
        # Create a test GLB file
        test_file = tmp_path / "test.glb"
        test_content = b"fake glb content"
        test_file.write_bytes(test_content)

        from embed4d import viewer_server

        original_model = viewer_server.MODEL_FILE
        try:
            viewer_server.MODEL_FILE = str(test_file)
            client = TestClient(app)
            response = client.get("/model")
            assert response.status_code == 200
            assert response.headers["content-type"] == "model/gltf-binary"
            assert response.content == test_content
        finally:
            viewer_server.MODEL_FILE = original_model


class TestLaunch:
    """Tests for launch function."""

    def test_launch_without_port_uses_free_port(self):
        """Test that launch finds a free port when port is None."""
        with patch("embed4d.viewer_server.uvicorn.run"):
            with patch("embed4d.viewer_server.threading.Thread") as mock_thread:
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance

                url = launch(port=None, model_file=None)

                assert url.startswith("http://localhost:")
                port = int(url.split(":")[-1])
                assert 1024 <= port <= 65535
                mock_thread_instance.start.assert_called_once()

    def test_launch_with_port_uses_specified_port(self):
        """Test that launch uses the specified port."""
        test_port = 8888
        with patch("embed4d.viewer_server.uvicorn.run") as mock_uvicorn:
            with patch("embed4d.viewer_server.threading.Thread") as mock_thread:
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance

                url = launch(port=test_port, model_file=None)

                assert url == f"http://localhost:{test_port}"
                # Verify thread was created with a function that will call uvicorn.run
                mock_thread.assert_called_once()
                thread_call_args = mock_thread.call_args
                # The function is passed as keyword argument 'target'
                run_api_func = thread_call_args[1]["target"]
                # Call the function to verify it calls uvicorn.run with correct args
                run_api_func()
                mock_uvicorn.assert_called_once()
                call_args = mock_uvicorn.call_args
                assert call_args[1]["port"] == test_port
                assert call_args[1]["host"] == "0.0.0.0"

    def test_launch_with_model_file(self, tmp_path):
        """Test that launch sets MODEL_FILE when model_file is provided."""
        test_file = tmp_path / "test.glb"
        test_file.write_bytes(b"test content")

        from embed4d import viewer_server

        original_model = viewer_server.MODEL_FILE
        try:
            with patch("embed4d.viewer_server.uvicorn.run"):
                with patch("embed4d.viewer_server.threading.Thread") as mock_thread:
                    mock_thread_instance = Mock()
                    mock_thread.return_value = mock_thread_instance

                    launch(port=9999, model_file=str(test_file))

                    assert viewer_server.MODEL_FILE == str(test_file.resolve())
        finally:
            viewer_server.MODEL_FILE = original_model

    def test_launch_with_nonexistent_model_file_raises_error(self, tmp_path):
        """Test that launch raises FileNotFoundError for nonexistent model file."""
        nonexistent_file = tmp_path / "nonexistent.glb"

        with pytest.raises(FileNotFoundError) as exc_info:
            launch(port=9999, model_file=str(nonexistent_file))

        assert "Model file not found" in str(exc_info.value)
        assert str(nonexistent_file) in str(exc_info.value)

    def test_launch_starts_thread(self):
        """Test that launch starts a daemon thread."""
        with patch("embed4d.viewer_server.uvicorn.run"):
            with patch("embed4d.viewer_server.threading.Thread") as mock_thread:
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance

                launch(port=9999, model_file=None)

                mock_thread.assert_called_once()
                call_args = mock_thread.call_args
                assert call_args[1]["daemon"] is True
                mock_thread_instance.start.assert_called_once()

    def test_launch_waits_for_server_start(self):
        """Test that launch waits for server to start."""
        with patch("embed4d.viewer_server.uvicorn.run"):
            with patch("embed4d.viewer_server.threading.Thread"):
                with patch("embed4d.viewer_server.time.sleep") as mock_sleep:
                    launch(port=9999, model_file=None)
                    # Should sleep to give server time to start
                    mock_sleep.assert_called_once_with(1.5)

    def test_launch_returns_correct_url(self):
        """Test that launch returns the correct URL."""
        test_port = 7777
        with patch("embed4d.viewer_server.uvicorn.run"):
            with patch("embed4d.viewer_server.threading.Thread"):
                url = launch(port=test_port, model_file=None)
                assert url == f"http://localhost:{test_port}"

    def test_launch_with_relative_model_file_path(self, tmp_path):
        """Test that launch converts relative model file path to absolute."""
        test_file = tmp_path / "test.glb"
        test_file.write_bytes(b"test")

        from embed4d import viewer_server

        original_model = viewer_server.MODEL_FILE
        try:
            # Change to tmp_path directory to test relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                with patch("embed4d.viewer_server.uvicorn.run"):
                    with patch("embed4d.viewer_server.threading.Thread"):
                        launch(port=9999, model_file="test.glb")
                        # MODEL_FILE should be absolute path
                        assert os.path.isabs(viewer_server.MODEL_FILE)
                        assert Path(viewer_server.MODEL_FILE).name == "test.glb"
            finally:
                os.chdir(original_cwd)
        finally:
            viewer_server.MODEL_FILE = original_model

    def test_launch_prints_startup_messages(self, capsys):
        """Test that launch prints startup messages."""
        with patch("embed4d.viewer_server.uvicorn.run"):
            with patch("embed4d.viewer_server.threading.Thread"):
                launch(port=8888, model_file=None)
                captured = capsys.readouterr()
                assert "🚀 Starting FastAPI" in captured.out
                assert "http://localhost:8888" in captured.out
                assert "No model file provided" in captured.out

    def test_launch_prints_model_file_message(self, tmp_path, capsys):
        """Test that launch prints model file message when model is provided."""
        test_file = tmp_path / "test.glb"
        test_file.write_bytes(b"test")

        with patch("embed4d.viewer_server.uvicorn.run"):
            with patch("embed4d.viewer_server.threading.Thread"):
                launch(port=8888, model_file=str(test_file))
                captured = capsys.readouterr()
                assert "Serving model:" in captured.out
                assert "test.glb" in captured.out or str(test_file) in captured.out
