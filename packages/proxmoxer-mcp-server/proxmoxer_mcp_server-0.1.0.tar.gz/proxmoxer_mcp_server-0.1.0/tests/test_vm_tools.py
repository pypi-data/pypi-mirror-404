"""
Test VM management tools for Proxmoxer MCP Server
"""

from unittest.mock import patch

import pytest

import proxmoxer_mcp_server
from tests.conftest import get_original_func


class TestVMManagementTools:
    """Test VM management functionality"""

    def test_list_vms_success(self, mock_environment, mock_proxmox_api, sample_vm_data):
        """Test successful VM listing"""
        mock_proxmox_api.nodes.return_value.qemu.get.return_value = sample_vm_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = get_original_func(proxmoxer_mcp_server.list_vms)()

            assert result == sample_vm_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.qemu.get.assert_called_once()
            mock_audit.assert_called_once_with("list_vms", {"node": "test-node"})

    def test_list_vms_with_specific_node(self, mock_environment, mock_proxmox_api, sample_vm_data):
        """Test VM listing with specific node"""
        mock_proxmox_api.nodes.return_value.qemu.get.return_value = sample_vm_data

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.list_vms(node="specific-node")

            assert result == sample_vm_data
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_audit.assert_called_once_with("list_vms", {"node": "specific-node"})

    def test_list_vms_api_error(self, mock_environment, mock_proxmox_api):
        """Test VM listing with API error"""
        mock_proxmox_api.nodes.return_value.qemu.get.side_effect = Exception("API Error")

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="API Error"):
                proxmoxer_mcp_server.list_vms()

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with("list_vms", {"node": "test-node"}, error="API Error")

    def test_get_vm_status_success(self, mock_environment, mock_proxmox_api):
        """Test successful VM status retrieval"""
        status_data = {"status": "running", "cpu": 0.5, "memory": 1073741824}
        mock_proxmox_api.nodes.return_value.qemu.return_value.status.current.get.return_value = (
            status_data
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.get_vm_status("100")

            assert result == status_data
            mock_proxmox_api.nodes.assert_called_once_with("test-node")
            mock_proxmox_api.nodes.return_value.qemu.assert_called_once_with("100")
            mock_proxmox_api.nodes.return_value.qemu.return_value.status.current.get.assert_called_once()
            mock_audit.assert_called_once_with(
                "get_vm_status", {"node": "test-node", "vmid": "100"}
            )

    def test_get_vm_status_with_specific_node(self, mock_environment, mock_proxmox_api):
        """Test VM status retrieval with specific node"""
        status_data = {"status": "stopped"}
        mock_proxmox_api.nodes.return_value.qemu.return_value.status.current.get.return_value = (
            status_data
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.get_vm_status("101", node="specific-node")

            assert result == status_data
            mock_proxmox_api.nodes.assert_called_once_with("specific-node")
            mock_proxmox_api.nodes.return_value.qemu.assert_called_once_with("101")
            mock_audit.assert_called_once_with(
                "get_vm_status", {"node": "specific-node", "vmid": "101"}
            )

    def test_start_vm_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM start"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.status.start.post.return_value = {
            "task": "12345"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.start_vm("100", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 started"
            assert "result" in result
            mock_proxmox_api.nodes.return_value.qemu.return_value.status.start.post.assert_called_once()
            mock_audit.assert_called_once_with("start_vm", {"node": "test-node", "vmid": "100"})

    def test_start_vm_without_confirmation(self, mock_environment_destructive):
        """Test VM start fails without confirmation in strict mode"""
        with pytest.raises(PermissionError, match="CONFIRMATION REQUIRED"):
            proxmoxer_mcp_server.start_vm("100", confirmed=False)

    def test_start_vm_destructive_disabled(self, mock_environment):
        """Test VM start fails when destructive operations are disabled"""
        with pytest.raises(PermissionError, match="Destructive operation 'start_vm' is disabled"):
            proxmoxer_mcp_server.start_vm("100", confirmed=True)

    def test_stop_vm_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM stop"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.status.stop.post.return_value = {
            "task": "12346"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.stop_vm("100", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 stopped"
            mock_proxmox_api.nodes.return_value.qemu.return_value.status.stop.post.assert_called_once()
            mock_audit.assert_called_once_with("stop_vm", {"node": "test-node", "vmid": "100"})

    def test_restart_vm_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM restart"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.status.reboot.post.return_value = {
            "task": "12347"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.restart_vm("100", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 restarted"
            mock_proxmox_api.nodes.return_value.qemu.return_value.status.reboot.post.assert_called_once()
            mock_audit.assert_called_once_with("restart_vm", {"node": "test-node", "vmid": "100"})

    def test_delete_vm_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM deletion"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.delete.return_value = {
            "task": "12348"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.delete_vm("100", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 deleted"
            mock_proxmox_api.nodes.return_value.qemu.return_value.delete.assert_called_once()
            mock_audit.assert_called_once_with("delete_vm", {"node": "test-node", "vmid": "100"})

    def test_delete_vm_requires_confirmation(self, mock_environment_destructive):
        """Test VM deletion requires confirmation"""
        with pytest.raises(PermissionError, match="CONFIRMATION REQUIRED"):
            proxmoxer_mcp_server.delete_vm("100", confirmed=False)

    def test_clone_vm_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM clone"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.clone.post.return_value = {
            "task": "12349",
            "vmid": "101",
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.clone_vm("100", "101", "test-clone", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 cloned to 101"
            mock_proxmox_api.nodes.return_value.qemu.return_value.clone.post.assert_called_once_with(
                newid="101", name="test-clone"
            )
            mock_audit.assert_called_once_with(
                "clone_vm",
                {"node": "test-node", "vmid": "100", "newid": "101", "name": "test-clone"},
            )

    def test_clone_vm_minimal_params(self, mock_environment_destructive, mock_proxmox_api):
        """Test VM clone with minimal parameters"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.clone.post.return_value = {
            "task": "12350"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.clone_vm("100", "102", confirmed=True)

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.qemu.return_value.clone.post.assert_called_once_with(
                newid="102"
            )
            mock_audit.assert_called_once_with(
                "clone_vm", {"node": "test-node", "vmid": "100", "newid": "102", "name": None}
            )

    def test_create_snapshot_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful snapshot creation"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.snapshot.post.return_value = {
            "task": "12351"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.create_snapshot(
                "100", "test-snap", "Test snapshot", confirmed=True
            )

            assert result["status"] == "success"
            assert result["message"] == "Snapshot test-snap created for VM 100"
            mock_proxmox_api.nodes.return_value.qemu.return_value.snapshot.post.assert_called_once_with(
                snapname="test-snap", description="Test snapshot"
            )
            mock_audit.assert_called_once_with(
                "create_snapshot", {"node": "test-node", "vmid": "100", "snapname": "test-snap"}
            )

    def test_create_snapshot_minimal_params(self, mock_environment_destructive, mock_proxmox_api):
        """Test snapshot creation with minimal parameters"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.snapshot.post.return_value = {
            "task": "12352"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.create_snapshot("100", "minimal-snap", confirmed=True)

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.qemu.return_value.snapshot.post.assert_called_once_with(
                snapname="minimal-snap"
            )
            mock_audit.assert_called_once_with(
                "create_snapshot", {"node": "test-node", "vmid": "100", "snapname": "minimal-snap"}
            )


class TestVMResourceManagement:
    """Test VM resource management functionality"""

    def test_modify_vm_resources_memory(self, mock_environment_destructive, mock_proxmox_api):
        """Test VM memory modification"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.config.put.return_value = {
            "task": "12353"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.modify_vm_resources("100", memory=4096, confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 resources modified"
            mock_proxmox_api.nodes.return_value.qemu.return_value.config.put.assert_called_once_with(
                memory=4096
            )
            mock_audit.assert_called_once_with(
                "modify_vm_resources", {"node": "test-node", "vmid": "100", "memory": 4096}
            )

    def test_modify_vm_resources_multiple_params(
        self, mock_environment_destructive, mock_proxmox_api
    ):
        """Test VM resource modification with multiple parameters"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.config.put.return_value = {
            "task": "12354"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.modify_vm_resources(
                "100", memory=2048, cores=4, sockets=2, confirmed=True
            )

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.qemu.return_value.config.put.assert_called_once_with(
                memory=2048, cores=4, sockets=2
            )
            mock_audit.assert_called_once_with(
                "modify_vm_resources",
                {"node": "test-node", "vmid": "100", "memory": 2048, "cores": 4, "sockets": 2},
            )

    def test_modify_vm_resources_no_params_raises_error(self, mock_environment_destructive):
        """Test VM resource modification fails with no parameters"""
        with pytest.raises(ValueError, match="At least one resource parameter"):
            proxmoxer_mcp_server.modify_vm_resources("100", confirmed=True)

    def test_resize_vm_disk_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM disk resize"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.resize.put.return_value = {
            "task": "12355"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.resize_vm_disk("100", "scsi0", "+10G", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 disk scsi0 resized by +10G"
            mock_proxmox_api.nodes.return_value.qemu.return_value.resize.put.assert_called_once_with(
                disk="scsi0", size="+10G"
            )
            mock_audit.assert_called_once_with(
                "resize_vm_disk",
                {"node": "test-node", "vmid": "100", "disk": "scsi0", "size": "+10G"},
            )

    def test_create_vm_template_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM template creation"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.template.post.return_value = {
            "task": "12356"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.create_vm_template("100", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 converted to template"
            mock_proxmox_api.nodes.return_value.qemu.return_value.template.post.assert_called_once()
            mock_audit.assert_called_once_with(
                "create_vm_template", {"node": "test-node", "vmid": "100"}
            )


class TestVMAdvancedOperations:
    """Test advanced VM operations"""

    def test_migrate_vm_success(self, mock_environment_destructive, mock_proxmox_api):
        """Test successful VM migration"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.migrate.post.return_value = {
            "task": "12357"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.migrate_vm(
                "100", "target-node", online=False, confirmed=True
            )

            assert result["status"] == "success"
            assert result["message"] == "VM 100 migration to target-node initiated"
            mock_proxmox_api.nodes.return_value.qemu.return_value.migrate.post.assert_called_once_with(
                target="target-node", online=0
            )
            mock_audit.assert_called_once_with(
                "migrate_vm",
                {"node": "test-node", "vmid": "100", "target_node": "target-node", "online": False},
            )

    def test_migrate_vm_online_migration(self, mock_environment_destructive, mock_proxmox_api):
        """Test online VM migration"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.migrate.post.return_value = {
            "task": "12358"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.migrate_vm(
                "100", "target-node", online=True, confirmed=True
            )

            assert result["status"] == "success"
            mock_proxmox_api.nodes.return_value.qemu.return_value.migrate.post.assert_called_once_with(
                target="target-node", online=1
            )
            mock_audit.assert_called_once_with(
                "migrate_vm",
                {"node": "test-node", "vmid": "100", "target_node": "target-node", "online": True},
            )

    def test_create_template_alias(self, mock_environment_destructive, mock_proxmox_api):
        """Test create_template alias function"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.template.post.return_value = {
            "task": "12359"
        }

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            result = proxmoxer_mcp_server.create_template("100", confirmed=True)

            assert result["status"] == "success"
            assert result["message"] == "VM 100 converted to template"
            mock_proxmox_api.nodes.return_value.qemu.return_value.template.post.assert_called_once()
            mock_audit.assert_called_once_with(
                "create_template", {"node": "test-node", "vmid": "100"}
            )


class TestVMErrorHandling:
    """Test VM operation error handling"""

    def test_vm_operation_api_error(self, mock_environment_destructive, mock_proxmox_api):
        """Test VM operation handles API errors"""
        mock_proxmox_api.nodes.return_value.qemu.return_value.status.start.post.side_effect = (
            Exception("VM start failed")
        )

        with (
            patch("proxmoxer_mcp_server.get_proxmox", return_value=mock_proxmox_api),
            patch("proxmoxer_mcp_server.get_default_node", return_value="test-node"),
            patch("proxmoxer_mcp_server.logger") as mock_logger,
            patch("proxmoxer_mcp_server.audit_log") as mock_audit,
        ):

            with pytest.raises(Exception, match="VM start failed"):
                proxmoxer_mcp_server.start_vm("100", confirmed=True)

            mock_logger.error.assert_called_once()
            mock_audit.assert_called_once_with(
                "start_vm", {"node": "test-node", "vmid": "100"}, error="VM start failed"
            )
