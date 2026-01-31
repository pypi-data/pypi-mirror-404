"""
Test safety controls and audit logging for Proxmoxer MCP Server
"""

import importlib
import os
from unittest.mock import patch

import pytest

import proxmoxer_mcp_server


class TestDestructiveOperationControls:
    """Test destructive operation safety controls"""

    def test_destructive_ops_disabled_by_default(self, mock_environment):
        """Test that destructive operations are disabled by default"""
        with pytest.raises(PermissionError, match="Destructive operation 'start_vm' is disabled"):
            proxmoxer_mcp_server.check_destructive_allowed("start_vm")

    def test_destructive_ops_enabled_with_env_var(self, mock_environment_destructive):
        """Test that destructive operations are enabled when env var is set"""
        # Reset module state with destructive enabled environment
        importlib.reload(proxmoxer_mcp_server)
        # Should not raise an exception
        proxmoxer_mcp_server.check_destructive_allowed("start_vm")

    def test_strict_confirmation_mode_requires_flag(self, mock_environment_destructive):
        """Test that strict mode requires confirmed=True"""
        # Reset module state with destructive enabled environment
        importlib.reload(proxmoxer_mcp_server)
        with pytest.raises(PermissionError, match="CONFIRMATION REQUIRED"):
            proxmoxer_mcp_server.check_destructive_allowed("start_vm", confirmed=False)

    def test_relaxed_confirmation_mode_bypasses_safe_ops(self):
        """Test that relaxed mode bypasses confirmation for safe operations"""
        env_vars = {
            "PROXMOX_ALLOW_DESTRUCTIVE": "true",
            "PROXMOX_CONFIRMATION_MODE": "relaxed",
            "PROXMOX_AUDIT_LEVEL": "standard",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # Reset module-level variables by re-importing module
            importlib.reload(proxmoxer_mcp_server)

            # Should not raise an exception even without confirmation
            proxmoxer_mcp_server.check_destructive_allowed("start_vm", confirmed=False)

    def test_non_destructive_operation_always_allowed(self, mock_environment):
        """Test that non-destructive operations are always allowed"""
        # Should not raise an exception even with destructive ops disabled
        proxmoxer_mcp_server.check_destructive_allowed("list_vms")
        proxmoxer_mcp_server.check_destructive_allowed("get_vm_status")

    def test_all_destructive_operations_identified(self, mock_environment_destructive):
        """Test that all known destructive operations are properly identified"""
        destructive_ops = [
            "delete_vm",
            "delete_lxc",
            "resize_vm_disk",
            "create_template",
            "create_vm_template",
            "start_vm",
            "stop_vm",
            "restart_vm",
            "create_lxc",
            "clone_lxc",
            "clone_vm",
            "lxc_config",
            "modify_vm_resources",
            "migrate_vm",
            "lxc_backup",
            "lxc_restore",
            "download_template",
            "create_snapshot",
        ]

        for operation in destructive_ops:
            # Should not raise exception with destructive ops enabled
            importlib.reload(proxmoxer_mcp_server)
            proxmoxer_mcp_server.check_destructive_allowed(operation, confirmed=True)

    def test_destructive_ops_disabled_environment_override(self, mock_environment):
        """Test destructive operations can be disabled via environment"""
        # Reset module state with default environment
        importlib.reload(proxmoxer_mcp_server)
        with pytest.raises(PermissionError, match="Destructive operation 'delete_vm' is disabled"):
            proxmoxer_mcp_server.check_destructive_allowed("delete_vm", confirmed=True)

    def test_confirmed_parameter_required_for_destructive_ops(self, mock_environment_destructive):
        """Test that confirmed parameter is required for destructive operations in strict mode"""
        # Reset with strict mode
        env_vars = {
            "PROXMOX_ALLOW_DESTRUCTIVE": "true",
            "PROXMOX_CONFIRMATION_MODE": "strict",
            "PROXMOX_AUDIT_LEVEL": "standard",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            importlib.reload(proxmoxer_mcp_server)

            # These should fail without confirmation
            with pytest.raises(PermissionError, match="CONFIRMATION REQUIRED"):
                proxmoxer_mcp_server.check_destructive_allowed("delete_vm")

            with pytest.raises(PermissionError, match="CONFIRMATION REQUIRED"):
                proxmoxer_mcp_server.check_destructive_allowed("start_vm", confirmed=False)

            # This should succeed with confirmation
            proxmoxer_mcp_server.check_destructive_allowed("delete_vm", confirmed=True)
            proxmoxer_mcp_server.check_destructive_allowed("start_vm", confirmed=True)


class TestAuditLogging:
    """Test audit logging functionality"""

    def test_audit_log_minimal_level(self, mock_environment):
        """Test audit logging at minimal level"""
        env_vars = {**mock_environment, "PROXMOX_AUDIT_LEVEL": "minimal"}
        with patch.dict(os.environ, env_vars):
            importlib.reload(proxmoxer_mcp_server)

            with patch("proxmoxer_mcp_server.logger") as mock_logger:
                proxmoxer_mcp_server.audit_log("test_operation", {"param": "value"})
                mock_logger.info.assert_called_once_with("Operation: test_operation")

    def test_audit_log_standard_level(self, mock_environment):
        """Test audit logging at standard level"""
        env_vars = {**mock_environment, "PROXMOX_AUDIT_LEVEL": "standard"}
        with patch.dict(os.environ, env_vars):
            importlib.reload(proxmoxer_mcp_server)

            with patch("proxmoxer_mcp_server.logger") as mock_logger:
                params = {"param": "value", "node": "test"}
                proxmoxer_mcp_server.audit_log("test_operation", params)
                mock_logger.info.assert_called_once_with(
                    "Operation: test_operation, Params: {'param': 'value', 'node': 'test'}"
                )

    def test_audit_log_full_level(self, mock_environment):
        """Test audit logging at full level"""
        env_vars = {**mock_environment, "PROXMOX_AUDIT_LEVEL": "full"}
        with patch.dict(os.environ, env_vars):
            importlib.reload(proxmoxer_mcp_server)

            with patch("proxmoxer_mcp_server.logger") as mock_logger:
                params = {"param": "value"}
                result = {"status": "success"}
                error = None

                proxmoxer_mcp_server.audit_log("test_operation", params, result, error)
                mock_logger.info.assert_called_once_with(
                    "Operation: test_operation, Params: {'param': 'value'}, "
                    "Result: {'status': 'success'}, Error: None"
                )

    def test_audit_log_with_error(self, mock_environment):
        """Test audit logging with error"""
        with patch("proxmoxer_mcp_server.logger") as mock_logger:
            params = {"param": "value"}
            error = "Connection failed"

            proxmoxer_mcp_server.audit_log("test_operation", params, error=error)
            mock_logger.info.assert_called_once_with(
                "Operation: test_operation, Params: {'param': 'value'}, Result: None, Error: Connection failed"
            )

    def test_audit_log_full_level_with_result_and_error(self, mock_environment):
        """Test audit logging at full level with both result and error"""
        env_vars = {**mock_environment, "PROXMOX_AUDIT_LEVEL": "full"}
        with patch.dict(os.environ, env_vars):
            importlib.reload(proxmoxer_mcp_server)

            with patch("proxmoxer_mcp_server.logger") as mock_logger:
                params = {"vmid": "100"}
                result = None
                error = "VM not found"

                proxmoxer_mcp_server.audit_log("delete_vm", params, result, error)
                mock_logger.info.assert_called_once_with(
                    "Operation: delete_vm, Params: {'vmid': '100'}, "
                    "Result: None, Error: VM not found"
                )

    def test_audit_log_default_level(self, mock_environment):
        """Test audit logging defaults to standard level"""
        with patch("proxmoxer_mcp_server.logger") as mock_logger:
            params = {"test": "param"}

            proxmoxer_mcp_server.audit_log("test_operation", params)
            mock_logger.info.assert_called_once_with(
                "Operation: test_operation, Params: {'test': 'param'}, Result: None, Error: None"
            )


class TestSafetyIntegration:
    """Test integration between safety controls and operations"""

    def test_environment_variables_reload(self):
        """Test that changing environment variables affects safety controls"""
        # First test with destructive ops disabled
        env_vars_disabled = {
            "PROXMOX_ALLOW_DESTRUCTIVE": "false",
            "PROXMOX_CONFIRMATION_MODE": "strict",
            "PROXMOX_AUDIT_LEVEL": "standard",
        }

        with patch.dict(os.environ, env_vars_disabled, clear=True):
            importlib.reload(proxmoxer_mcp_server)

            with pytest.raises(PermissionError):
                proxmoxer_mcp_server.check_destructive_allowed("delete_vm", confirmed=True)

        # Then test with destructive ops enabled
        env_vars_enabled = {
            "PROXMOX_ALLOW_DESTRUCTIVE": "true",
            "PROXMOX_CONFIRMATION_MODE": "strict",
            "PROXMOX_AUDIT_LEVEL": "standard",
        }

        with patch.dict(os.environ, env_vars_enabled, clear=True):
            importlib.reload(proxmoxer_mcp_server)

            # Should not raise exception
            proxmoxer_mcp_server.check_destructive_allowed("delete_vm", confirmed=True)

    def test_global_constants_set_correctly(self):
        """Test that global safety constants are set correctly"""
        # Test default values
        assert hasattr(proxmoxer_mcp_server, "DESTRUCTIVE_OPERATIONS")
        assert "delete_vm" in proxmoxer_mcp_server.DESTRUCTIVE_OPERATIONS
        assert "list_vms" not in proxmoxer_mcp_server.DESTRUCTIVE_OPERATIONS

        assert hasattr(proxmoxer_mcp_server, "DESTRUCTIVE_OPS_ALLOWED")
        assert isinstance(proxmoxer_mcp_server.DESTRUCTIVE_OPS_ALLOWED, bool)

        assert hasattr(proxmoxer_mcp_server, "CONFIRMATION_MODE")
        assert proxmoxer_mcp_server.CONFIRMATION_MODE in ["strict", "relaxed"]

        assert hasattr(proxmoxer_mcp_server, "AUDIT_LEVEL")
        assert proxmoxer_mcp_server.AUDIT_LEVEL in ["minimal", "standard", "full"]
