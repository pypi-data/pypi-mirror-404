"""
Test LXC container management tools for Proxmoxer MCP Server
"""

from unittest.mock import patch

import pytest

import proxmoxer_mcp_server


class TestLXCManagementTools:
    """Test LXC container management functionality"""

    def test_list_lxc_success(self, mock_environment, mock_proxmox_api, sample_lxc_data):
        """Test successful LXC container listing"""
        mock_proxmox_api.nodes.return_value.lxc.get.return_value = sample_lxc_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.list_lxc()

            assert result == sample_lxc_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.lxc.get.assert_called_once()
            mock_audit.assert_called_once_with("list_lxc", {"node": "test-node"})

    def test_list_lxc_with_specific_node(self, mock_environment, mock_proxmox_api, sample_lxc_data):
        """Test LXC listing with specific node"""
        mock_proxmox_api.nodes.return_value.lxc.get.return_value = sample_lxc_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.list_lxc(node="specific-node")

            assert result == sample_lxc_data
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_audit.assert_called_once_with("list_lxc", {"node": "specific-node"})

    def test_get_lxc_status_success(self, mock_environment, mock_proxmox_api):
        """Test successful LXC status retrieval"""
        status_data = {"status": "running", "cpu": 0.3, "memory": 536870912}
        mock_proxmox_api.nodes.return_value.lxc.return_value.status.current.get.return_value = (
            status_data
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.get_lxc_status("200")

            assert result == status_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.lxc.assert_called_once_with("200")
            mock_proxmox_api.nodes.return_value.lxc.return_value.status.current.get.assert_called_once()
            mock_audit.assert_called_once_with(
                "get_lxc_status", {"node": "test-node", "vmid": "200"}
            )

    def test_create_lxc_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful LXC container creation"""
        mock_proxmox_api.nodes.return_value.lxc.post.return_value = {"task": "54321", "vmid": "200"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.create_lxc(
                vmid="200",
                hostname="test-lxc",
                ostemplate="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                storage="local-lvm",
                memory=1024,
                cores=2,
                rootfs_size=16,
                password="testpass",
                confirmed=True,
            )

            assert result["status"] == "success"
            assert result["message"] == "LXC container 200 created"
            mock_proxmox_api.nodes.return_value.lxc.post.assert_called_once_with(
                vmid="200",
                hostname="test-lxc",
                ostemplate="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                storage="local-lvm",
                memory=1024,
                cores=2,
                rootfs="local-lvm:16",
                password="testpass",
            )
            mock_audit.assert_called_once()

    def test_create_lxc_minimal_params(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC creation with minimal parameters"""
        mock_proxmox_api.nodes.return_value.lxc.post.return_value = {"task": "54322"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.create_lxc(
                vmid="201",
                hostname="minimal-lxc",
                ostemplate="local:vztmpl/debian-11-standard_11.3-1_amd64.tar.zst",
                confirmed=True,
            )

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.lxc.post.assert_called_once_with(
                vmid="201",
                hostname="minimal-lxc",
                ostemplate="local:vztmpl/debian-11-standard_11.3-1_amd64.tar.zst",
                storage="local-lvm",
                memory=512,
                cores=1,
                rootfs="local-lvm:8",
            )
            mock_audit.assert_called_once()

    def test_create_lxc_without_password(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC creation without password"""
        mock_proxmox_api.nodes.return_value.lxc.post.return_value = {"task": "54323"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as _mock_audit,
        ):

            result = proxmoxer_mcp_server.create_lxc(
                vmid="202",
                hostname="no-pass-lxc",
                ostemplate="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                confirmed=True,
            )

            assert result["status"] == "success"
            # Verify password is not in the call
            call_args = mock_proxmox_api.nodes.return_value.lxc.post.call_args[1]
            assert "password" not in call_args

    def test_delete_lxc_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful LXC container deletion"""
        mock_proxmox_api.nodes.return_value.lxc.return_value.delete.return_value = {"task": "54324"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.delete_lxc("200", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "LXC container 200 deleted"
            mock_proxmox_api.nodes.return_value.lxc.return_value.delete.assert_called_once()
            mock_audit.assert_called_once_with("delete_lxc", {"node": "test-node", "vmid": "200"})

    def test_delete_lxc_requires_confirmation(self, mock_environment_destructive):
        """Test LXC deletion requires confirmation"""
        with pytest.raises(PermissionError, match="CONFIRMATION REQUIRED"):
            proxmoxer_mcp_server.delete_lxc("200", confirmed=False)


class TestLXCAdvancedOperations:
    """Test advanced LXC operations"""

    def test_clone_lxc_full_clone(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC full clone"""
        mock_proxmox_api.nodes.return_value.lxc.return_value.clone.post.return_value = {
            "task": "54325",
            "vmid": "201",
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.clone_lxc(
                "200", "201", "cloned-lxc", full=True, confirmed=True
            )

            assert result["status"] == "success"
            assert result["message"] == "LXC 200 cloned to 201"
            mock_proxmox_api.nodes.return_value.lxc.return_value.clone.post.assert_called_once_with(
                newid="201", full=1, hostname="cloned-lxc"
            )
            mock_audit.assert_called_once_with(
                "clone_lxc",
                {"node": "test-node", "vmid": "200", "newid": "201", "hostname": "cloned-lxc"},
            )

    def test_clone_lxc_linked_clone(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC linked clone"""
        mock_proxmox_api.nodes.return_value.lxc.return_value.clone.post.return_value = {
            "task": "54326"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.clone_lxc("200", "202", full=False, confirmed=True)

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.lxc.return_value.clone.post.assert_called_once_with(
                newid="202", full=0
            )
            mock_audit.assert_called_once_with(
                "clone_lxc", {"node": "test-node", "vmid": "200", "newid": "202", "hostname": None}
            )

    def test_lxc_config_update(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC configuration update"""
        mock_proxmox_api.nodes.return_value.lxc.return_value.config.put.return_value = {
            "task": "54327"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            config_params = {"memory": 2048, "cores": 4, "net0": "bridge=vmbr0,firewall=1"}

            result = proxmoxer_mcp_server.lxc_config("200", config_params, confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "LXC 200 configuration updated"
            mock_proxmox_api.nodes.return_value.lxc.return_value.config.put.assert_called_once_with(
                **config_params
            )
            mock_audit.assert_called_once_with(
                "lxc_config", {"node": "test-node", "vmid": "200", "config_params": config_params}
            )

    def test_lxc_backup_snapshot_mode(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC backup with snapshot mode"""
        mock_proxmox_api.nodes.return_value.vzdump.post.return_value = {"task": "54328"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.lxc_backup(
                vmid="200", storage="local", mode="snapshot", compress="zstd", confirmed=True
            )

            assert result["status"] == "success"
            assert result["message"] == "LXC 200 backup initiated"
            mock_proxmox_api.nodes.return_value.vzdump.post.assert_called_once_with(
                vmid="200", storage="local", mode="snapshot", compress="zstd"
            )
            mock_audit.assert_called_once_with(
                "lxc_backup",
                {"node": "test-node", "vmid": "200", "storage": "local", "mode": "snapshot"},
            )

    def test_lxc_backup_suspend_mode(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC backup with suspend mode"""
        mock_proxmox_api.nodes.return_value.vzdump.post.return_value = {"task": "54329"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as _mock_audit,
        ):

            result = proxmoxer_mcp_server.lxc_backup(
                vmid="200",
                storage="backup-storage",
                mode="suspend",
                compress="gzip",
                confirmed=True,
            )

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.vzdump.post.assert_called_once_with(
                vmid="200", storage="backup-storage", mode="suspend", compress="gzip"
            )

    def test_lxc_restore_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC restore from backup"""
        mock_proxmox_api.nodes.return_value.lxc.post.return_value = {"task": "54330", "vmid": "203"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.lxc_restore(
                vmid="203",
                archive="local:backup/vzdump-lxc-200-2024_01_01-00_00_00.tar.zst",
                storage="local-lvm",
                force=True,
                confirmed=True,
            )

            assert result["status"] == "success"
            assert (
                result["message"]
                == "LXC 203 restore initiated from local:backup/vzdump-lxc-200-2024_01_01-00_00_00.tar.zst"
            )
            mock_proxmox_api.nodes.return_value.lxc.post.assert_called_once_with(
                vmid="203",
                archive="local:backup/vzdump-lxc-200-2024_01_01-00_00_00.tar.zst",
                restore=1,
                force=1,
                storage="local-lvm",
            )
            mock_audit.assert_called_once_with(
                "lxc_restore",
                {
                    "node": "test-node",
                    "vmid": "203",
                    "archive": "local:backup/vzdump-lxc-200-2024_01_01-00_00_00.tar.zst",
                },
            )

    def test_lxc_restore_minimal_params(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC restore with minimal parameters"""
        mock_proxmox_api.nodes.return_value.lxc.post.return_value = {"task": "54331"}

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as _mock_audit,
        ):

            result = proxmoxer_mcp_server.lxc_restore(
                vmid="204",
                archive="local:backup/vzdump-lxc-200-2024_01_01-00_00_00.tar.zst",
                confirmed=True,
            )

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.lxc.post.assert_called_once_with(
                vmid="204",
                archive="local:backup/vzdump-lxc-200-2024_01_01-00_00_00.tar.zst",
                restore=1,
                force=0,
            )

    def test_lxc_console_success(self, mock_environment, mock_proxmox_api):
        """Test LXC console information retrieval"""
        console_info = {"port": 5900, "ticket": "abc123"}
        mock_proxmox_api.nodes.return_value.lxc.return_value.vncproxy.post.return_value = (
            console_info
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.lxc_console("200")

            assert result["status"] == "success"
            assert result["message"] == "Console info for LXC 200"
            assert result["console"] == console_info
            mock_proxmox_api.nodes.return_value.lxc.return_value.vncproxy.post.assert_called_once()
            mock_audit.assert_called_once_with("lxc_console", {"node": "test-node", "vmid": "200"})


class TestLXCErrorHandling:
    """Test LXC operation error handling"""

    def test_lxc_operation_api_error(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC operation handles API errors"""
        mock_proxmox_api.nodes.return_value.lxc.post.side_effect = Exception("LXC creation failed")

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="LXC creation failed"):
                proxmoxer_mcp_server.create_lxc(
                    vmid="200",
                    hostname="test-lxc",
                    ostemplate="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
                    confirmed=True,
                )

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once()

    def test_lxc_list_error(self, mock_environment, mock_proxmox_api):
        """Test LXC listing handles API errors"""
        mock_proxmox_api.nodes.return_value.lxc.get.side_effect = Exception(
            "Failed to list containers"
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="Failed to list containers"):
                proxmoxer_mcp_server.list_lxc()

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with(
                "list_lxc", {"node": "test-node"}, error="Failed to list containers"
            )

    def test_lxc_config_validation(self, mock_environment_destructive, mock_proxmox_api):
        """Test LXC config with empty parameters"""
        mock_proxmox_api.nodes.return_value.lxc.return_value.config.put.return_value = {
            "task": "54332"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            # Empty config should still work (no validation for empty config in current implementation)
            result = proxmoxer_mcp_server.lxc_config("200", {}, confirmed=True)

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.lxc.return_value.config.put.assert_called_once_with()
            mock_audit.assert_called_once_with(
                "lxc_config", {"node": "test-node", "vmid": "200", "config_params": {}}
            )
