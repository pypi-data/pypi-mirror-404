# K3s Cluster CLI

Minimal CLI for managing your K3s cluster.

## Installation

### From PyPI (Recommended)

**On Raspberry Pi / Debian-based systems:**
```bash
pip install --break-system-packages k3-cluster-cli
```

**On other systems:**
```bash
pip install k3-cluster-cli
```

**Alternative: Using pipx (recommended for CLI tools):**
```bash
pipx install k3-cluster-cli
```

### From Source

```bash
git clone https://gitlab.com/aleksey-lichtman/k3-cluster-cli.git
cd k3-cluster-cli
pip install -e .
```

## Commands

```bash
cluster reboot   # Check cluster health and reboot
cluster health   # Watch live cluster info
cluster version  # Check for updates
cluster upgrade  # Upgrade to latest version
```

## Requirements

- Python 3.8+
- kubectl (configured for your cluster)
- Access to a K3s cluster

## Development

Build the package:

```bash
python -m build
```

## License

MIT License - see [LICENSE](LICENSE) for details.
