# Proxmox MCP Server
![CI](https://git.airstrikeivanov.com/airstrikeivanov/proxmoxer-mcp-server/badges/workflows/ci.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/proxmoxer-mcp-server)
![Python](https://img.shields.io/pypi/pyversions/proxmoxer-mcp-server)

I tried a few other MCP servers for my homelab Proxmox setup, and couldn't get one that did exactly what I was after.

It defaults to stdio output. It uses [FastMCP](https://github.com/jlowin/fastmcp), so you can switch to http or sse as needed.
Uses [proxmoxer](https://github.com/proxmoxer/proxmoxer) to connect to Proxmox and handle commands.

**AI DISCLAIMER** - I used OpenCode to assist with this. This means AI-generated code is present. Audit the source and verify for yourself before you use in production.

## Requirements
- Python 3.10+
- Proxmox VE
- a Proxmox API token with the following permissions (you can omit things you want to deny): `VM.Console, VM.Config.Memory, Datastore.Audit, VM.Audit, VM.Snapshot.Rollback, Datastore.AllocateSpace, Sys.Audit, SDN.Audit, VM.Config.Disk, VM.Config.Network, VM.Config.CPU, Sys.Console, VM.Config.Cloudinit, Datastore.Allocate, Pool.Audit, VM.Config.CDROM, VM.PowerMgmt, Pool.Allocate, SDN.Use, VM.Clone, VM.Snapshot, VM.Config.Options, VM.Allocate`

## Install

### Option 1: Install from PyPI (Recommended)
```bash
pip install proxmoxer-mcp-server
proxmoxer-mcp-server  # Runs with environment variables
```

### Option 2: Install from Source
```bash
git clone https://git.airstrikeivanov.com/airstrikeivanov/proxmoxer-mcp-server.git && cd proxmoxer-mcp-server
python -m venv venv && source venv/bin/activate  # Virtualenv strongly recommended
pip install -e .  # Editable install
```

### Option 3: Development Install
```bash
git clone https://git.airstrikeivanov.com/airstrikeivanov/proxmoxer-mcp-server.git && cd proxmoxer-mcp-server
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"  # Includes dev dependencies
```

### Configuration
Copy `.env.example` to `.env` and edit, or set environment variables elsewhere.

### Running
```bash
# After PyPI install
proxmoxer-mcp-server

# After source install
python -m proxmoxer_mcp_server
# or
proxmoxer-mcp-server
```

## Configuration
The MCP server requires a handful of variables to start up. I don't provide defaults yet.

### Required Environment Variables
| Variable | Description |
|----------|-------------|
| `PROXMOX_HOST` | Proxmox server URL (without protocol prefix) |
| `PROXMOX_TOKEN_ID` | API token identifier in format: user@realm!tokenid |
| `PROXMOX_TOKEN_SECRET` | API token secret |
| `PROXMOX_NODE` | Default Proxmox node name |

### Optional Environment Variables
| Variable | Description |
|----------|-------------|
| `PROXMOX_SKIP_TLS_VERIFY` | Skip TLS verification (true for development, false for production) |
| `PROXMOX_ALLOW_DESTRUCTIVE` | Enable/disable destructive operations (default: false) |
| `PROXMOX_CONFIRMATION_MODE` | Confirmation strictness: strict or relaxed (default: strict) |
| `PROXMOX_AUDIT_LEVEL` | Audit detail: minimal, standard, or full (default: standard) |
| `LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) |

### FastMCP Transport Operations
| Variable | Description |
|----------|-------------|
| `MCP_HOST` | Host address to bind to (default: 127.0.0.1) - must be set to enable remote connections |
| `MCP_PORT` | Port to listen on (default: 8080) |
| `MCP_TRANSPORT` | Transport type to use (default: "stdio") - options: "stdio", "http", "sse" |

### Destructive Operations (Two-Step Process)
```bash
# Step 1: Request operation (requires confirmation)
delete_vm(node="pve", vmid="100", confirmed=False)
# Returns: "CONFIRMATION REQUIRED"

# Step 2: Execute with confirmation
delete_vm(node="pve", vmid="100", confirmed=True)
# Executes the deletion
```
