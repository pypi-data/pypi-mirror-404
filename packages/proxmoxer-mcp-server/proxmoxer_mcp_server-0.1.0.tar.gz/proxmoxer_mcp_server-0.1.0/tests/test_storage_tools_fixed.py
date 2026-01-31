"""
Test storage and template management tools for Proxmoxer MCP Server
"""

from unittest.mock import patch

import pytest

import proxmoxer_mcp_server
from tests.conftest import get_original_func


class TestNodeManagement:
    """Test node management functionality"""

    def test_get_node_status_success(self, mock_environment, mock_proxmox_api):
        """Test successful node status retrieval"""
        status_data = {
            "node": "test-node",
            "status": "online",
            "cpu": 0.15,
            "mem": 2147483648,
            "maxmem": 8589934592,
            "disk": 107374182400,
            "maxdisk": 214748364800,
        }
        mock_proxmox_api.nodes.return_value.status.get.return_value = status_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.get_node_status)()

            assert result == status_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.status.get.assert_called_once()
            mock_audit.assert_called_once_with("get_node_status", {"node": "test-node"})

    def test_get_node_status_with_specific_node(self, mock_environment, mock_proxmox_api):
        """Test node status retrieval with specific node"""
        status_data = {"node": "specific-node", "status": "online"}
        mock_proxmox_api.nodes.return_value.status.get.return_value = status_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.get_node_status)(node="specific-node")

            assert result == status_data
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_audit.assert_called_once_with("get_node_status", {"node": "specific-node"})

    def test_list_nodes_success(self, mock_environment, mock_proxmox_api):
        """Test successful cluster nodes listing"""
        nodes_data = [
            {"node": "test-node-1", "status": "online", "cpu": 0.1, "mem": 1000000},
            {"node": "test-node-2", "status": "offline", "cpu": 0.0, "mem": 0},
        ]
        mock_proxmox_api.nodes.get.return_value = nodes_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_nodes)()

            assert result == nodes_data
            mock_proxmox_api.nodes.get.assert_called_once()
            mock_audit.assert_called_once_with("list_nodes", {})


class TestStorageManagement:
    """Test storage management functionality"""

    def test_list_storage_success(self, mock_environment, mock_proxmox_api, sample_storage_data):
        """Test successful storage listing"""
        mock_proxmox_api.nodes.return_value.storage.get.return_value = sample_storage_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_storage)()

            assert result == sample_storage_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.storage.get.assert_called_once()
            mock_audit.assert_called_once_with("list_storage", {"node": "test-node"})

    def test_list_storage_with_specific_node(
        self, mock_environment, mock_proxmox_api, sample_storage_data
    ):
        """Test storage listing with specific node"""
        mock_proxmox_api.nodes.return_value.storage.get.return_value = sample_storage_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_storage)(node="specific-node")

            assert result == sample_storage_data
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_audit.assert_called_once_with("list_storage", {"node": "specific-node"})


class TestTemplateManagement:
    """Test template management functionality"""

    def test_list_templates_success(self, mock_environment, mock_proxmox_api, sample_template_data):
        """Test successful template listing"""
        mock_proxmox_api.nodes.return_value.storage.return_value.content.get.return_value = (
            sample_template_data
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_templates)()

            assert result == sample_template_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.storage.assert_called_once_with("local")
            mock_proxmox_api.nodes.return_value.storage.return_value.content.get.assert_called_once_with(
                content="vztmpl"
            )
            mock_audit.assert_called_once_with(
                "list_templates", {"node": "test-node", "storage": "local"}
            )

    def test_list_templates_with_specific_storage(
        self, mock_environment, mock_proxmox_api, sample_template_data
    ):
        """Test template listing with specific storage"""
        mock_proxmox_api.nodes.return_value.storage.return_value.content.get.return_value = (
            sample_template_data
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_templates)(
                storage="local-lvm", node="specific-node"
            )

            assert result == sample_template_data
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_proxmox_api.nodes.return_value.storage.assert_called_once_with("local-lvm")
            mock_audit.assert_called_once_with(
                "list_templates", {"node": "specific-node", "storage": "local-lvm"}
            )

    def test_list_iso_images_success(self, mock_environment, mock_proxmox_api, sample_iso_data):
        """Test successful ISO image listing"""
        mock_proxmox_api.nodes.return_value.storage.return_value.content.get.return_value = (
            sample_iso_data
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_iso_images)()

            assert result == sample_iso_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.storage.assert_called_once_with("local")
            mock_proxmox_api.nodes.return_value.storage.return_value.content.get.assert_called_once_with(
                content="iso"
            )
            mock_audit.assert_called_once_with(
                "list_iso_images", {"node": "test-node", "storage": "local"}
            )

    def test_list_iso_images_with_specific_storage(
        self, mock_environment, mock_proxmox_api, sample_iso_data
    ):
        """Test ISO image listing with specific storage"""
        mock_proxmox_api.nodes.return_value.storage.return_value.content.get.return_value = (
            sample_iso_data
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_iso_images)(
                storage="iso-storage", node="specific-node"
            )

            assert result == sample_iso_data
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_proxmox_api.nodes.return_value.storage.assert_called_once_with("iso-storage")
            mock_audit.assert_called_once_with(
                "list_iso_images", {"node": "specific-node", "storage": "iso-storage"}
            )

    def test_list_os_images_success(
        self, mock_environment, mock_proxmox_api, sample_iso_data, sample_template_data
    ):
        """Test successful OS images listing (both ISOs and templates)"""
        # Mock both calls in sequence
        mock_proxmox_api.nodes.return_value.storage.return_value.content.get.side_effect = [
            sample_iso_data,
            sample_template_data,
        ]

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_os_images)()

            assert result["isos"] == sample_iso_data
            assert result["templates"] == sample_template_data
            assert (
                mock_proxmox_api.nodes.return_value.storage.return_value.content.get.call_count == 2
            )
            mock_audit.assert_called_once_with(
                "list_os_images", {"node": "test-node", "storage": "local"}
            )

    def test_download_template_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful template download"""
        mock_proxmox_api.nodes.return_value.aplinfo.post.return_value = {
            "task": "65432",
            "status": "downloading",
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.download_template)(
                storage="local",
                template="ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                confirmed=True,
            )

            assert result["status"] == "success"
            assert (
                result["message"]
                == "Template ubuntu-22.04-standard_22.04-1_amd64.tar.zst download initiated"
            )
            mock_proxmox_api.nodes.return_value.aplinfo.post.assert_called_once_with(
                storage="local", template="ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
            )
            mock_audit.assert_called_once_with(
                "download_template",
                {
                    "node": "test-node",
                    "storage": "local",
                    "template": "ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                },
            )

    def test_download_template_requires_confirmation(self, mock_environment_destructive):
        """Test template download requires confirmation"""
        with pytest.raises(PermissionError, match="CONFIRMATION REQUIRED"):
            get_original_func(proxmoxer_mcp_server.download_template)(
                storage="local",
                template="ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                confirmed=False,
            )

    def test_download_template_with_specific_node(
        self, mock_environment_destructive, mock_proxmox_api
    ):
        """Test template download with specific node"""
        mock_proxmox_api.nodes.return_value.aplinfo.post.return_value = {"task": "65433"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.download_template)(
                storage="backup-storage",
                template="debian-11-standard_11.3-1_amd64.tar.zst",
                node="specific-node",
                confirmed=True,
            )

            assert result["status"] == "success"
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_proxmox_api.nodes.return_value.aplinfo.post.assert_called_once_with(
                storage="backup-storage", template="debian-11-standard_11.3-1_amd64.tar.zst"
            )
            mock_audit.assert_called_once_with(
                "download_template",
                {
                    "node": "specific-node",
                    "storage": "backup-storage",
                    "template": "debian-11-standard_11.3-1_amd64.tar.zst",
                },
            )


class TestStorageErrorHandling:
    """Test storage operation error handling"""

    def test_list_storage_api_error(self, mock_environment, mock_proxmox_api):
        """Test storage listing handles API errors"""
        mock_proxmox_api.nodes.return_value.storage.get.side_effect = Exception(
            "Storage access failed"
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="Storage access failed"):
                get_original_func(proxmoxer_mcp_server.list_storage)()

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with(
                "list_storage", {"node": "test-node"}, error="Storage access failed"
            )

    def test_list_templates_api_error(self, mock_environment, mock_proxmox_api):
        """Test template listing handles API errors"""
        mock_proxmox_api.nodes.return_value.storage.return_value.content.get.side_effect = (
            Exception("Template access failed")
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="Template access failed"):
                get_original_func(proxmoxer_mcp_server.list_templates)()

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with(
                "list_templates",
                {"node": "test-node", "storage": "local"},
                error="Template access failed",
            )

    def test_download_template_api_error(self, mock_environment_destructive, mock_proxmox_api):
        """Test template download handles API errors"""
        mock_proxmox_api.nodes.return_value.aplinfo.post.side_effect = Exception("Download failed")

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="Download failed"):
                get_original_func(proxmoxer_mcp_server.download_template)(
                    storage="local",
                    template="ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                    confirmed=True,
                )

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with(
                "download_template",
                {
                    "node": "test-node",
                    "storage": "local",
                    "template": "ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                },
                error="Download failed",
            )

    def test_list_os_images_partial_failure(
        self, mock_environment, mock_proxmox_api, sample_iso_data
    ):
        """Test OS images listing handles partial failure"""
        # First call succeeds (ISOs), second call fails (templates)
        mock_proxmox_api.nodes.return_value.storage.return_value.content.get.side_effect = [
            sample_iso_data,
            Exception("Template access failed"),
        ]

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="Template access failed"):
                get_original_func(proxmoxer_mcp_server.list_os_images)()

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with(
                "list_os_images",
                {"node": "test-node", "storage": "local"},
                error="Template access failed",
            )


class TestNodeErrorHandling:
    """Test node operation error handling"""

    def test_get_node_status_api_error(self, mock_environment, mock_proxmox_api):
        """Test node status retrieval handles API errors"""
        mock_proxmox_api.nodes.return_value.status.get.side_effect = Exception("Node access failed")

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="Node access failed"):
                get_original_func(proxmoxer_mcp_server.get_node_status)()

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with(
                "get_node_status", {"node": "test-node"}, error="Node access failed"
            )

    def test_list_nodes_api_error(self, mock_environment, mock_proxmox_api):
        """Test cluster nodes listing handles API errors"""
        mock_proxmox_api.nodes.get.side_effect = Exception("Cluster access failed")

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="Cluster access failed"):
                get_original_func(proxmoxer_mcp_server.list_nodes)()

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with("list_nodes", {}, error="Cluster access failed")
