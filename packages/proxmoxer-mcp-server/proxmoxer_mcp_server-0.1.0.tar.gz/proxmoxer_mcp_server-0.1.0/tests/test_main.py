# Test for the main entry point
import os
import sys
from unittest.mock import patch

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import proxmoxer_mcp_server


class TestMainEntry:
    """Test the main entry point functionality"""

    @patch("proxmoxer_mcp_server.get_proxmox")
    @patch("proxmoxer_mcp_server.get_default_node")
    @patch("proxmoxer_mcp_server.app")
    def test_main_stdio_transport(self, mock_app, mock_get_node, mock_get_proxmox):
        """Test main function with stdio transport"""
        # Set environment for stdio transport
        with patch.dict(os.environ, {"MCP_TRANSPORT": "stdio"}):
            proxmoxer_mcp_server.main()

            # Verify environment validation
            mock_get_proxmox.assert_called_once()
            mock_get_node.assert_called_once()

            # Verify stdio app.run was called
            mock_app.run.assert_called_once()

    @patch("proxmoxer_mcp_server.get_proxmox")
    @patch("proxmoxer_mcp_server.get_default_node")
    @patch("proxmoxer_mcp_server.app")
    def test_main_http_transport(self, mock_app, mock_get_node, mock_get_proxmox):
        """Test main function with HTTP transport"""
        with patch.dict(
            os.environ, {"MCP_TRANSPORT": "http", "MCP_HOST": "0.0.0.0", "MCP_PORT": "8080"}
        ):
            proxmoxer_mcp_server.main()

            # Verify HTTP app.run was called with correct parameters
            mock_app.run.assert_called_once_with(transport="sse", host="0.0.0.0", port=8080)

    @patch("sys.exit")
    @patch("proxmoxer_mcp_server.get_proxmox")
    def test_main_configuration_error(self, mock_get_proxmox, mock_exit):
        """Test main function handles configuration errors"""
        mock_get_proxmox.side_effect = ValueError("Missing required environment variable")

        with patch("proxmoxer_mcp_server.logger") as mock_logger:
            proxmoxer_mcp_server.main()

            # Verify error logging and exit
            mock_logger.error.assert_called()
            mock_exit.assert_called_once_with(1)
