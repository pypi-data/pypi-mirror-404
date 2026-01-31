#!/usr/bin/env python3
"""
Proxmoxer MCP Server - Manages Proxmox VE infrastructure via MCP protocol
Enhanced with FastMCP and comprehensive safety mechanisms
"""

import asyncio
import logging
import os
from typing import Any, Optional

from fastmcp import FastMCP
from proxmoxer import ProxmoxAPI

# Configure logging from environment variable
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger("proxmoxer-mcp")

# Environment-based safety controls
DESTRUCTIVE_OPS_ALLOWED = os.getenv("PROXMOX_ALLOW_DESTRUCTIVE", "false").lower() == "true"
CONFIRMATION_MODE = os.getenv("PROXMOX_CONFIRMATION_MODE", "strict")  # strict, relaxed
AUDIT_LEVEL = os.getenv("PROXMOX_AUDIT_LEVEL", "standard")  # minimal, standard, full

# Operation safety classification
DESTRUCTIVE_OPERATIONS = {
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
}


# Transport and server configuration
TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = os.getenv("MCP_PORT", "8080")


# Initialize server with enhanced configuration
def initialize_app():
    """Initialize FastMCP app with environment-based configuration"""

    if TRANSPORT in ("http", "sse"):
        transport_type = "SSE" if TRANSPORT == "sse" else "HTTP"
        logger.info(f"Configured for {transport_type} transport on {HOST}:{PORT}")
        return FastMCP("proxmoxer-mcp-server", version="0.1.0")
    else:  # stdio (default)
        logger.info("Configured for stdio transport")
        return FastMCP("proxmoxer-mcp-server", version="0.1.0")


# Initialize app
app = initialize_app()

# Proxmox connection singleton
_proxmox_connection = None


def get_proxmox() -> ProxmoxAPI:
    """Get or create Proxmox API connection"""
    global _proxmox_connection

    if _proxmox_connection is None:
        host = os.getenv("PROXMOX_HOST")
        token_id = os.getenv("PROXMOX_TOKEN_ID")
        token_secret = os.getenv("PROXMOX_TOKEN_SECRET")
        skip_tls = os.getenv("PROXMOX_SKIP_TLS_VERIFY", "false").lower() == "true"

        if not all([host, token_id, token_secret]):
            raise ValueError(
                "Missing required environment variables: "
                "PROXMOX_HOST, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET"
            )

        # Remove protocol prefix if present
        host = host.replace("https://", "").replace("http://", "")

        logger.info(f"Connecting to Proxmox host: {host}")
        _proxmox_connection = ProxmoxAPI(
            host,
            user=token_id.split("!")[0],
            token_name=token_id.split("!")[1],
            token_value=token_secret,
            verify_ssl=not skip_tls,
        )
        logger.info("Successfully connected to Proxmox")

    return _proxmox_connection


def get_default_node() -> str:
    """Get default node from environment"""
    node = os.getenv("PROXMOX_NODE")
    if not node:
        raise ValueError("PROXMOX_NODE environment variable not set")
    return node


def check_destructive_allowed(operation: str, confirmed: bool = False) -> None:
    """Check if destructive operation is allowed"""
    if operation in DESTRUCTIVE_OPERATIONS:
        if not DESTRUCTIVE_OPS_ALLOWED:
            raise PermissionError(
                f"Destructive operation '{operation}' is disabled. "
                "Set PROXMOX_ALLOW_DESTRUCTIVE=true to enable."
            )

        if CONFIRMATION_MODE == "strict" and not confirmed:
            raise PermissionError(
                f"CONFIRMATION REQUIRED: Operation '{operation}' requires confirmation. "
                "Add confirmed=True parameter to execute."
            )


def audit_log(operation: str, params: dict[str, Any], result: Any = None, error: Any = None):
    """Log operation for audit trail"""
    if AUDIT_LEVEL == "minimal":
        logger.info(f"Operation: {operation}")
    elif AUDIT_LEVEL == "standard":
        logger.info(f"Operation: {operation}, Params: {params}")
    elif AUDIT_LEVEL == "full":
        logger.info(f"Operation: {operation}, Params: {params}, Result: {result}, Error: {error}")


# ============================================================================
# VM Management Tools
# ============================================================================


@app.tool()
def list_vms(node: str | None = None) -> list[dict[str, Any]]:
    """
    List all VMs on a Proxmox node

    Args:
        node: Proxmox node name (uses default if not specified)

    Returns:
        List of VM information dictionaries
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("list_vms", {"node": node})
        vms = proxmox.nodes(node).qemu.get()

        return vms
    except Exception as e:
        logger.error(f"Error listing VMs: {e}")
        audit_log("list_vms", {"node": node}, error=str(e))
        raise


@app.tool()
def get_vm_status(vmid: str, node: str | None = None) -> dict[str, Any]:
    """
    Get detailed status of a specific VM

    Args:
        vmid: VM ID
        node: Proxmox node name (uses default if not specified)

    Returns:
        VM status information
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("get_vm_status", {"node": node, "vmid": vmid})
        status = proxmox.nodes(node).qemu(vmid).status.current.get()

        return status
    except Exception as e:
        logger.error(f"Error getting VM status: {e}")
        audit_log("get_vm_status", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def start_vm(vmid: str, node: str | None = None, confirmed: bool = False) -> dict[str, Any]:
    """
    Start a VM

    Args:
        vmid: VM ID
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("start_vm", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("start_vm", {"node": node, "vmid": vmid})
        result = proxmox.nodes(node).qemu(vmid).status.start.post()

        return {"status": "success", "message": f"VM {vmid} started", "result": result}
    except Exception as e:
        logger.error(f"Error starting VM: {e}")
        audit_log("start_vm", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def stop_vm(vmid: str, node: str | None = None, confirmed: bool = False) -> dict[str, Any]:
    """
    Stop a VM

    Args:
        vmid: VM ID
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("stop_vm", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("stop_vm", {"node": node, "vmid": vmid})
        result = proxmox.nodes(node).qemu(vmid).status.stop.post()

        return {"status": "success", "message": f"VM {vmid} stopped", "result": result}
    except Exception as e:
        logger.error(f"Error stopping VM: {e}")
        audit_log("stop_vm", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def restart_vm(vmid: str, node: str | None = None, confirmed: bool = False) -> dict[str, Any]:
    """
    Restart a VM

    Args:
        vmid: VM ID
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("restart_vm", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("restart_vm", {"node": node, "vmid": vmid})
        result = proxmox.nodes(node).qemu(vmid).status.reboot.post()

        return {"status": "success", "message": f"VM {vmid} restarted", "result": result}
    except Exception as e:
        logger.error(f"Error restarting VM: {e}")
        audit_log("restart_vm", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def delete_vm(vmid: str, node: str | None = None, confirmed: bool = False) -> dict[str, Any]:
    """
    Delete a VM (DESTRUCTIVE - requires confirmation)

    Args:
        vmid: VM ID
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag (REQUIRED)

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("delete_vm", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("delete_vm", {"node": node, "vmid": vmid})
        result = proxmox.nodes(node).qemu(vmid).delete()

        return {"status": "success", "message": f"VM {vmid} deleted", "result": result}
    except Exception as e:
        logger.error(f"Error deleting VM: {e}")
        audit_log("delete_vm", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def clone_vm(
    vmid: str,
    newid: str,
    name: str | None = None,
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Clone a VM

    Args:
        vmid: Source VM ID
        newid: New VM ID
        name: Name for the new VM
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("clone_vm", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {"newid": newid}
        if name:
            params["name"] = name

        audit_log("clone_vm", {"node": node, "vmid": vmid, "newid": newid, "name": name})
        result = proxmox.nodes(node).qemu(vmid).clone.post(**params)

        return {"status": "success", "message": f"VM {vmid} cloned to {newid}", "result": result}
    except Exception as e:
        logger.error(f"Error cloning VM: {e}")
        audit_log("clone_vm", {"node": node, "vmid": vmid, "newid": newid}, error=str(e))
        raise


@app.tool()
def create_snapshot(
    vmid: str,
    snapname: str,
    description: str | None = None,
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Create a VM snapshot

    Args:
        vmid: VM ID
        snapname: Snapshot name
        description: Snapshot description
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("create_snapshot", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {"snapname": snapname}
        if description:
            params["description"] = description

        audit_log("create_snapshot", {"node": node, "vmid": vmid, "snapname": snapname})
        result = proxmox.nodes(node).qemu(vmid).snapshot.post(**params)

        return {
            "status": "success",
            "message": f"Snapshot {snapname} created for VM {vmid}",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        audit_log(
            "create_snapshot", {"node": node, "vmid": vmid, "snapname": snapname}, error=str(e)
        )
        raise


@app.tool()
def modify_vm_resources(
    vmid: str,
    memory: int | None = None,
    cores: int | None = None,
    sockets: int | None = None,
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Modify VM resources (memory, CPU)

    Args:
        vmid: VM ID
        memory: Memory in MB
        cores: Number of CPU cores
        sockets: Number of CPU sockets
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("modify_vm_resources", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {}
        if memory is not None:
            params["memory"] = memory
        if cores is not None:
            params["cores"] = cores
        if sockets is not None:
            params["sockets"] = sockets

        if not params:
            raise ValueError(
                "At least one resource parameter (memory, cores, sockets) must be specified"
            )

        audit_log("modify_vm_resources", {"node": node, "vmid": vmid, **params})
        result = proxmox.nodes(node).qemu(vmid).config.put(**params)

        return {"status": "success", "message": f"VM {vmid} resources modified", "result": result}
    except Exception as e:
        logger.error(f"Error modifying VM resources: {e}")
        audit_log("modify_vm_resources", {"node": node, "vmid": vmid}, error=str(e))
        raise


# ============================================================================
# LXC Container Management Tools
# ============================================================================


@app.tool()
def list_lxc(node: str | None = None) -> list[dict[str, Any]]:
    """
    List all LXC containers on a Proxmox node

    Args:
        node: Proxmox node name (uses default if not specified)

    Returns:
        List of LXC container information dictionaries
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("list_lxc", {"node": node})
        containers = proxmox.nodes(node).lxc.get()

        return containers
    except Exception as e:
        logger.error(f"Error listing LXC containers: {e}")
        audit_log("list_lxc", {"node": node}, error=str(e))
        raise


@app.tool()
def get_lxc_status(vmid: str, node: str | None = None) -> dict[str, Any]:
    """
    Get detailed status of a specific LXC container

    Args:
        vmid: Container ID
        node: Proxmox node name (uses default if not specified)

    Returns:
        Container status information
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("get_lxc_status", {"node": node, "vmid": vmid})
        status = proxmox.nodes(node).lxc(vmid).status.current.get()

        return status
    except Exception as e:
        logger.error(f"Error getting LXC status: {e}")
        audit_log("get_lxc_status", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def create_lxc(
    vmid: str,
    hostname: str,
    ostemplate: str,
    storage: str = "local-lvm",
    memory: int = 512,
    cores: int = 1,
    rootfs_size: int = 8,
    password: str | None = None,
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Create a new LXC container

    Args:
        vmid: Container ID
        hostname: Container hostname
        ostemplate: OS template (e.g., 'local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst')
        storage: Storage pool (default: local-lvm)
        memory: Memory in MB (default: 512)
        cores: Number of CPU cores (default: 1)
        rootfs_size: Root filesystem size in GB (default: 8)
        password: Root password
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("create_lxc", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {
            "vmid": vmid,
            "hostname": hostname,
            "ostemplate": ostemplate,
            "storage": storage,
            "memory": memory,
            "cores": cores,
            "rootfs": f"{storage}:{rootfs_size}",
        }

        if password:
            params["password"] = password

        audit_log("create_lxc", {"node": node, **params})
        result = proxmox.nodes(node).lxc.post(**params)

        return {"status": "success", "message": f"LXC container {vmid} created", "result": result}
    except Exception as e:
        logger.error(f"Error creating LXC container: {e}")
        audit_log("create_lxc", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def delete_lxc(vmid: str, node: str | None = None, confirmed: bool = False) -> dict[str, Any]:
    """
    Delete an LXC container (DESTRUCTIVE - requires confirmation)

    Args:
        vmid: Container ID
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag (REQUIRED)

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("delete_lxc", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("delete_lxc", {"node": node, "vmid": vmid})
        result = proxmox.nodes(node).lxc(vmid).delete()

        return {"status": "success", "message": f"LXC container {vmid} deleted", "result": result}
    except Exception as e:
        logger.error(f"Error deleting LXC container: {e}")
        audit_log("delete_lxc", {"node": node, "vmid": vmid}, error=str(e))
        raise


# ============================================================================
# Node Management Tools
# ============================================================================


@app.tool()
def get_node_status(node: str | None = None) -> dict[str, Any]:
    """
    Get status and resource usage of a Proxmox node

    Args:
        node: Proxmox node name (uses default if not specified)

    Returns:
        Node status information
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("get_node_status", {"node": node})
        status = proxmox.nodes(node).status.get()

        return status
    except Exception as e:
        logger.error(f"Error getting node status: {e}")
        audit_log("get_node_status", {"node": node}, error=str(e))
        raise


@app.tool()
def list_nodes() -> list[dict[str, Any]]:
    """
    List all nodes in the Proxmox cluster

    Returns:
        List of node information dictionaries
    """
    try:
        proxmox = get_proxmox()

        audit_log("list_nodes", {})
        nodes = proxmox.nodes.get()

        return nodes
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        audit_log("list_nodes", {}, error=str(e))
        raise


# ============================================================================
# Storage and Template Management Tools
# ============================================================================


@app.tool()
def list_storage(node: str | None = None) -> list[dict[str, Any]]:
    """
    List storage pools on a Proxmox node

    Args:
        node: Proxmox node name (uses default if not specified)

    Returns:
        List of storage pool information
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("list_storage", {"node": node})
        storage = proxmox.nodes(node).storage.get()

        return storage
    except Exception as e:
        logger.error(f"Error listing storage: {e}")
        audit_log("list_storage", {"node": node}, error=str(e))
        raise


@app.tool()
def list_templates(storage: str = "local", node: str | None = None) -> list[dict[str, Any]]:
    """
    List available templates in storage

    Args:
        storage: Storage name (default: local)
        node: Proxmox node name (uses default if not specified)

    Returns:
        List of available templates
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("list_templates", {"node": node, "storage": storage})
        templates = proxmox.nodes(node).storage(storage).content.get(content="vztmpl")

        return templates
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        audit_log("list_templates", {"node": node, "storage": storage}, error=str(e))
        raise


@app.tool()
def list_iso_images(storage: str = "local", node: str | None = None) -> list[dict[str, Any]]:
    """
    List available ISO images in storage

    Args:
        storage: Storage name (default: local)
        node: Proxmox node name (uses default if not specified)

    Returns:
        List of available ISO images
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("list_iso_images", {"node": node, "storage": storage})
        isos = proxmox.nodes(node).storage(storage).content.get(content="iso")

        return isos
    except Exception as e:
        logger.error(f"Error listing ISO images: {e}")
        audit_log("list_iso_images", {"node": node, "storage": storage}, error=str(e))
        raise


@app.tool()
def list_os_images(storage: str = "local", node: str | None = None) -> dict[str, Any]:
    """
    List available OS images (both ISOs and templates)

    Args:
        storage: Storage name (default: local)
        node: Proxmox node name (uses default if not specified)

    Returns:
        Dictionary with ISOs and templates
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("list_os_images", {"node": node, "storage": storage})

        isos = proxmox.nodes(node).storage(storage).content.get(content="iso")
        templates = proxmox.nodes(node).storage(storage).content.get(content="vztmpl")

        return {"isos": isos, "templates": templates}
    except Exception as e:
        logger.error(f"Error listing OS images: {e}")
        audit_log("list_os_images", {"node": node, "storage": storage}, error=str(e))
        raise


@app.tool()
def download_template(
    storage: str, template: str, node: str | None = None, confirmed: bool = False
) -> dict[str, Any]:
    """
    Download a template from the Proxmox template repository

    Args:
        storage: Storage name where template will be downloaded
        template: Template name (e.g., 'ubuntu-22.04-standard_22.04-1_amd64.tar.zst')
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("download_template", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("download_template", {"node": node, "storage": storage, "template": template})
        result = proxmox.nodes(node).aplinfo.post(storage=storage, template=template)

        return {
            "status": "success",
            "message": f"Template {template} download initiated",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error downloading template: {e}")
        audit_log(
            "download_template",
            {"node": node, "storage": storage, "template": template},
            error=str(e),
        )
        raise


# ============================================================================
# Advanced VM Operations
# ============================================================================


@app.tool()
def resize_vm_disk(
    vmid: str, disk: str, size: str, node: str | None = None, confirmed: bool = False
) -> dict[str, Any]:
    """
    Resize a VM disk (can only increase size)

    Args:
        vmid: VM ID
        disk: Disk identifier (e.g., 'scsi0', 'virtio0')
        size: Size increase (e.g., '+10G' to add 10GB)
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("resize_vm_disk", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("resize_vm_disk", {"node": node, "vmid": vmid, "disk": disk, "size": size})
        result = proxmox.nodes(node).qemu(vmid).resize.put(disk=disk, size=size)

        return {
            "status": "success",
            "message": f"VM {vmid} disk {disk} resized by {size}",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error resizing VM disk: {e}")
        audit_log(
            "resize_vm_disk", {"node": node, "vmid": vmid, "disk": disk, "size": size}, error=str(e)
        )
        raise


@app.tool()
def create_vm_template(
    vmid: str, node: str | None = None, confirmed: bool = False
) -> dict[str, Any]:
    """
    Convert a VM to a template

    Args:
        vmid: VM ID to convert to template
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("create_vm_template", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("create_vm_template", {"node": node, "vmid": vmid})
        result = proxmox.nodes(node).qemu(vmid).template.post()

        return {
            "status": "success",
            "message": f"VM {vmid} converted to template",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error creating VM template: {e}")
        audit_log("create_vm_template", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def migrate_vm(
    vmid: str,
    target_node: str,
    online: bool = False,
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Migrate a VM to another node

    Args:
        vmid: VM ID to migrate
        target_node: Target node name
        online: Perform online/live migration (default: False)
        node: Source node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("migrate_vm", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {"target": target_node, "online": 1 if online else 0}

        audit_log(
            "migrate_vm", {"node": node, "vmid": vmid, "target_node": target_node, "online": online}
        )
        result = proxmox.nodes(node).qemu(vmid).migrate.post(**params)

        return {
            "status": "success",
            "message": f"VM {vmid} migration to {target_node} initiated",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error migrating VM: {e}")
        audit_log(
            "migrate_vm", {"node": node, "vmid": vmid, "target_node": target_node}, error=str(e)
        )
        raise


# ============================================================================
# Advanced LXC Operations
# ============================================================================


@app.tool()
def clone_lxc(
    vmid: str,
    newid: str,
    hostname: str | None = None,
    full: bool = True,
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Clone an LXC container

    Args:
        vmid: Source container ID
        newid: New container ID
        hostname: Hostname for the new container
        full: Full clone (True) or linked clone (False)
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("clone_lxc", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {"newid": newid, "full": 1 if full else 0}
        if hostname:
            params["hostname"] = hostname

        audit_log("clone_lxc", {"node": node, "vmid": vmid, "newid": newid, "hostname": hostname})
        result = proxmox.nodes(node).lxc(vmid).clone.post(**params)

        return {"status": "success", "message": f"LXC {vmid} cloned to {newid}", "result": result}
    except Exception as e:
        logger.error(f"Error cloning LXC: {e}")
        audit_log("clone_lxc", {"node": node, "vmid": vmid, "newid": newid}, error=str(e))
        raise


@app.tool()
def lxc_config(
    vmid: str, config_params: dict[str, Any], node: str | None = None, confirmed: bool = False
) -> dict[str, Any]:
    """
    Modify LXC container configuration

    Args:
        vmid: Container ID
        config_params: Dictionary of configuration parameters to modify
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("lxc_config", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("lxc_config", {"node": node, "vmid": vmid, "config_params": config_params})
        result = proxmox.nodes(node).lxc(vmid).config.put(**config_params)

        return {
            "status": "success",
            "message": f"LXC {vmid} configuration updated",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error updating LXC config: {e}")
        audit_log("lxc_config", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def lxc_backup(
    vmid: str,
    storage: str = "local",
    mode: str = "snapshot",
    compress: str = "zstd",
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Create a backup of an LXC container

    Args:
        vmid: Container ID
        storage: Storage for backup (default: local)
        mode: Backup mode - 'snapshot', 'suspend', or 'stop' (default: snapshot)
        compress: Compression algorithm - 'zstd', 'gzip', or 'lzo' (default: zstd)
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("lxc_backup", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {"vmid": vmid, "storage": storage, "mode": mode, "compress": compress}

        audit_log("lxc_backup", {"node": node, "vmid": vmid, "storage": storage, "mode": mode})
        result = proxmox.nodes(node).vzdump.post(**params)

        return {"status": "success", "message": f"LXC {vmid} backup initiated", "result": result}
    except Exception as e:
        logger.error(f"Error backing up LXC: {e}")
        audit_log("lxc_backup", {"node": node, "vmid": vmid}, error=str(e))
        raise


@app.tool()
def lxc_restore(
    vmid: str,
    archive: str,
    storage: str | None = None,
    force: bool = False,
    node: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Restore an LXC container from backup

    Args:
        vmid: Container ID for the restored container
        archive: Backup archive path (e.g., 'local:backup/vzdump-lxc-100-2024_01_01-00_00_00.tar.zst')
        storage: Storage for restored container
        force: Allow to overwrite existing container
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("lxc_restore", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        params = {"vmid": vmid, "archive": archive, "restore": 1, "force": 1 if force else 0}
        if storage:
            params["storage"] = storage

        audit_log("lxc_restore", {"node": node, "vmid": vmid, "archive": archive})
        result = proxmox.nodes(node).lxc.post(**params)

        return {
            "status": "success",
            "message": f"LXC {vmid} restore initiated from {archive}",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error restoring LXC: {e}")
        audit_log("lxc_restore", {"node": node, "vmid": vmid, "archive": archive}, error=str(e))
        raise


@app.tool()
def lxc_console(vmid: str, node: str | None = None) -> dict[str, Any]:
    """
    Get LXC container console information

    Args:
        vmid: Container ID
        node: Proxmox node name (uses default if not specified)

    Returns:
        Console connection information
    """
    try:
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("lxc_console", {"node": node, "vmid": vmid})
        console_info = proxmox.nodes(node).lxc(vmid).vncproxy.post()

        return {
            "status": "success",
            "message": f"Console info for LXC {vmid}",
            "console": console_info,
        }
    except Exception as e:
        logger.error(f"Error getting LXC console: {e}")
        audit_log("lxc_console", {"node": node, "vmid": vmid}, error=str(e))
        raise


# ============================================================================
# Missing Tool Implementations
# ============================================================================


@app.tool()
def create_template(vmid: str, node: str | None = None, confirmed: bool = False) -> dict[str, Any]:
    """
    Create a template from a VM (alias for create_vm_template)

    Args:
        vmid: VM ID to convert to template
        node: Proxmox node name (uses default if not specified)
        confirmed: Confirmation flag for destructive operation

    Returns:
        Operation result
    """
    try:
        check_destructive_allowed("create_template", confirmed)
        node = node or get_default_node()
        proxmox = get_proxmox()

        audit_log("create_template", {"node": node, "vmid": vmid})
        result = proxmox.nodes(node).qemu(vmid).template.post()

        return {
            "status": "success",
            "message": f"VM {vmid} converted to template",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        audit_log("create_template", {"node": node, "vmid": vmid}, error=str(e))
        raise


def main():
    """Main entry point for the proxmoxer-mcp-server application"""
    # Verify required environment variables on startup
    try:
        get_proxmox()
        get_default_node()
        logger.info("Environment configuration validated successfully")
        logger.info(
            f"Destructive operations: {'ENABLED' if DESTRUCTIVE_OPS_ALLOWED else 'DISABLED'}"
        )
        logger.info(f"Confirmation mode: {CONFIRMATION_MODE}")
        logger.info(f"Audit level: {AUDIT_LEVEL}")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your environment variables")
        exit(1)

    # Run the server
    if TRANSPORT in ("http", "sse"):
        app.run(transport="sse", host=HOST, port=int(PORT))
    else:
        app.run()


if __name__ == "__main__":
    main()
