"""
Test core infrastructure functions for Proxmoxer MCP Server
"""

# Import after mocking to avoid initialization issues
import importlib
import os
from unittest.mock import MagicMock, patch

import pytest

import proxmoxer_mcp_server


class TestProxmoxConnection:
    """Test ProxmoxAPI connection functionality"""

    def test_get_proxmox_success(self, mock_environment, mock_proxmox_api):
        """Test successful ProxmoxAPI connection"""
        # Reset module state
        importlib.reload(proxmoxer_mcp_server)

        with patch("proxmoxer_mcp_server.ProxmoxAPI", return_value=mock_proxmox_api) as mock_api:
            result = proxmoxer_mcp_server.get_proxmox()

            assert result is mock_proxmox_api
            mock_api.assert_called_once_with(
                "test-proxmox:8006",
                user="root@pam",
                token_name="test-token",
                token_value="test-secret-value",
                verify_ssl=True,
            )

    def test_get_proxmox_missing_host(self, mock_proxmox_api):
        """Test get_proxmox fails when PROXMOX_HOST is missing"""
        env_vars = {
            "PROXMOX_TOKEN_ID": "root@pam!test-token",
            "PROXMOX_TOKEN_SECRET": "test-secret",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # Reset module state
            importlib.reload(proxmoxer_mcp_server)

            with pytest.raises(ValueError, match="Missing required environment variables"):
                proxmoxer_mcp_server.get_proxmox()

    def test_get_proxmox_missing_token_id(self, mock_proxmox_api):
        """Test get_proxmox fails when PROXMOX_TOKEN_ID is missing"""
        env_vars = {"PROXMOX_HOST": "test-proxmox:8006", "PROXMOX_TOKEN_SECRET": "test-secret"}
        with patch.dict(os.environ, env_vars, clear=True):
            # Reset module state
            importlib.reload(proxmoxer_mcp_server)

            with pytest.raises(ValueError, match="Missing required environment variables"):
                proxmoxer_mcp_server.get_proxmox()

    def test_get_proxmox_missing_token_secret(self, mock_proxmox_api):
        """Test get_proxmox fails when PROXMOX_TOKEN_SECRET is missing"""
        env_vars = {"PROXMOX_HOST": "test-proxmox:8006", "PROXMOX_TOKEN_ID": "root@pam!test-token"}
        with patch.dict(os.environ, env_vars, clear=True):
            # Reset module state
            importlib.reload(proxmoxer_mcp_server)

            with pytest.raises(ValueError, match="Missing required environment variables"):
                proxmoxer_mcp_server.get_proxmox()

    def test_get_proxmox_connection_singleton(self, mock_environment, mock_proxmox_api):
        """Test that get_proxmox returns same instance (singleton pattern)"""
        # Reset module state
        importlib.reload(proxmoxer_mcp_server)

        with patch("proxmoxer_mcp_server.ProxmoxAPI", return_value=mock_proxmox_api) as mock_api:
            result1 = proxmoxer_mcp_server.get_proxmox()
            result2 = proxmoxer_mcp_server.get_proxmox()

            assert result1 is result2
            mock_api.assert_called_once()  # Only called once due to singleton

    def test_get_proxmox_tls_skip_true(self, mock_proxmox_api):
        """Test get_proxmox with TLS verification disabled"""
        env_vars = {
            "PROXMOX_HOST": "test-proxmox:8006",
            "PROXMOX_TOKEN_ID": "root@pam!test-token",
            "PROXMOX_TOKEN_SECRET": "test-secret-value",
            "PROXMOX_SKIP_TLS_VERIFY": "true",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # Reset module state
            importlib.reload(proxmoxer_mcp_server)

            with patch(
                "proxmoxer_mcp_server.ProxmoxAPI", return_value=mock_proxmox_api
            ) as mock_api:
                proxmoxer_mcp_server.get_proxmox()

                mock_api.assert_called_once_with(
                    "test-proxmox:8006",
                    user="root@pam",
                    token_name="test-token",
                    token_value="test-secret-value",
                    verify_ssl=False,
                )

    def test_get_proxmox_host_protocol_stripping(self, mock_proxmox_api):
        """Test that protocol prefixes are stripped from host"""
        test_cases = [
            ("https://test-proxmox:8006", "test-proxmox:8006"),
            ("http://test-proxmox:8006", "test-proxmox:8006"),
            ("test-proxmox:8006", "test-proxmox:8006"),
        ]

        for input_host, expected_host in test_cases:
            env_vars = {
                "PROXMOX_HOST": input_host,
                "PROXMOX_TOKEN_ID": "root@pam!test-token",
                "PROXMOX_TOKEN_SECRET": "test-secret-value",
            }
            with patch.dict(os.environ, env_vars, clear=True):
                # Reset module state
                importlib.reload(proxmoxer_mcp_server)

                with patch(
                    "proxmoxer_mcp_server.ProxmoxAPI", return_value=mock_proxmox_api
                ) as mock_api:
                    # Reset connection global for each test
                    proxmoxer_mcp_server._proxmox_connection = None

                    proxmoxer_mcp_server.get_proxmox()

                    mock_api.assert_called_once()
                    args, kwargs = mock_api.call_args
                    assert args[0] == expected_host
                    assert kwargs["token_value"] == "test-secret-value"
                    mock_api.reset_mock()


class TestDefaultNode:
    """Test default node functionality"""

    def test_get_default_node_success(self, mock_environment):
        """Test successful default node retrieval"""
        result = proxmoxer_mcp_server.get_default_node()
        assert result == "test-node"

    def test_get_default_node_missing_env_var(self):
        """Test get_default_node fails when PROXMOX_NODE is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="PROXMOX_NODE environment variable not set"):
                proxmoxer_mcp_server.get_default_node()


class TestAppInitialization:
    """Test FastMCP application initialization"""

    def test_initialize_app_stdio(self):
        """Test app initialization with stdio transport"""
        env_vars = {"MCP_TRANSPORT": "stdio"}
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("proxmoxer_mcp_server.FastMCP") as mock_fastmcp:
                mock_instance = MagicMock()
                mock_fastmcp.return_value = mock_instance

                result = proxmoxer_mcp_server.initialize_app()

                assert result is mock_instance
                mock_fastmcp.assert_called_once_with("proxmoxer-mcp-server", version="0.1.0")

    def test_initialize_app_http(self):
        """Test app initialization with HTTP transport"""
        env_vars = {"MCP_TRANSPORT": "http", "MCP_HOST": "0.0.0.0", "MCP_PORT": "8080"}
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("proxmoxer_mcp_server.FastMCP") as mock_fastmcp:
                mock_instance = MagicMock()
                mock_fastmcp.return_value = mock_instance

                result = proxmoxer_mcp_server.initialize_app()

                assert result is mock_instance
                mock_fastmcp.assert_called_once_with("proxmoxer-mcp-server", version="0.1.0")

    def test_initialize_app_sse(self):
        """Test app initialization with SSE transport"""
        env_vars = {"MCP_TRANSPORT": "sse", "MCP_HOST": "0.0.0.0", "MCP_PORT": "8080"}
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("proxmoxer_mcp_server.FastMCP") as mock_fastmcp:
                mock_instance = MagicMock()
                mock_fastmcp.return_value = mock_instance

                result = proxmoxer_mcp_server.initialize_app()

                assert result is mock_instance
                mock_fastmcp.assert_called_once_with("proxmoxer-mcp-server", version="0.1.0")

    def test_initialize_app_default_transport(self):
        """Test app initialization defaults to stdio when no transport specified"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("proxmoxer_mcp_server.FastMCP") as mock_fastmcp:
                mock_instance = MagicMock()
                mock_fastmcp.return_value = mock_instance

                result = proxmoxer_mcp_server.initialize_app()

                assert result is mock_instance
                mock_fastmcp.assert_called_once_with("proxmoxer-mcp-server", version="0.1.0")


class TestGlobalAppState:
    """Test global application state and initialization"""

    def test_app_is_global_variable(self):
        """Test that app is initialized as a global variable"""
        # This test verifies the app is properly initialized at module level
        assert hasattr(proxmoxer_mcp_server, "app")
        assert proxmoxer_mcp_server.app is not None

    def test_proxmox_connection_global_initialization(self):
        """Test that proxmox connection global is initialized to None"""
        # Reset module to initial state
        importlib.reload(proxmoxer_mcp_server)
        assert hasattr(proxmoxer_mcp_server, "_proxmox_connection")
        assert proxmoxer_mcp_server._proxmox_connection is None
