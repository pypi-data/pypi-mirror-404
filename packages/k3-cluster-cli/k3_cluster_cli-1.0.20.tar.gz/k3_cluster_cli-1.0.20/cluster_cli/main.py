#!/usr/bin/env python3
import subprocess
import sys
import typer
import requests
from cluster_cli.__version__ import __version__

app = typer.Typer(
    add_completion=True,
    no_args_is_help=True,
    invoke_without_command=False,
    pretty_exceptions_enable=False,
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 100,
        "ignore_unknown_options": False
    }
)

# Package info
PYPI_PACKAGE_NAME = "k3-cluster-cli"


def get_latest_version_from_pypi():
    """Fetch the latest version from PyPI."""
    try:
        response = requests.get(
            f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except Exception as e:
        print(f"Warning: Could not check PyPI for updates: {e}", file=sys.stderr)
        return None


@app.command()
def version():
    """Show the current version and check for updates."""
    print(f"cluster CLI version {__version__}")

    latest = get_latest_version_from_pypi()

    if latest:
        if latest == __version__:
            print("✓ You are running the latest version")
        else:
            print(f"→ New version available: {latest}")
            print(f"  Run 'cluster upgrade'")


@app.command()
def upgrade():
    """Upgrade the cluster CLI to the latest version from PyPI."""
    print("=== Checking for latest version ===")
    latest = get_latest_version_from_pypi()

    if not latest:
        print("Error: Could not fetch latest version from PyPI")
        sys.exit(1)

    if latest == __version__:
        print("✓ Already running the latest version")
        return

    print(f"Upgrading from {__version__} to {latest}...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--break-system-packages", PYPI_PACKAGE_NAME],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error upgrading: {result.stderr}")
            sys.exit(1)

        print(f"\n✓ Successfully upgraded to version {latest}")
        print("  Restart your shell")

    except Exception as e:
        print(f"Error during upgrade: {e}")
        sys.exit(1)


@app.command()
def reboot(
    user: str = typer.Option(None, "--user", "-u", help="SSH user for remote nodes (defaults to current user)"),
):
    """Check cluster health and reboot all nodes in the cluster."""
    print("=== Checking cluster health ===")
    subprocess.run(["kubectl", "get", "nodes", "-o", "wide"])
    subprocess.run("kubectl get pods -A | grep -v 'Running\\|Completed'", shell=True)

    # Get all node IPs from kubectl
    result = subprocess.run(
        ["kubectl", "get", "nodes", "-o", "jsonpath={.items[*].status.addresses[?(@.type=='InternalIP')].address}"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error getting node IPs: {result.stderr}")
        sys.exit(1)

    node_ips = result.stdout.strip().split()
    if not node_ips:
        print("No nodes found in cluster")
        sys.exit(1)

    # Get current hostname to identify the main node
    hostname_result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
    local_ips = hostname_result.stdout.strip().split()

    # Separate local node from remote nodes
    remote_ips = [ip for ip in node_ips if ip not in local_ips]
    local_ip = next((ip for ip in node_ips if ip in local_ips), None)

    print(f"\n=== Nodes to reboot ===")
    for ip in remote_ips:
        print(f"  Remote: {ip}")
    if local_ip:
        print(f"  Local:  {local_ip} (this node, rebooted last)")

    print()
    response = typer.confirm(f"Proceed with rebooting {len(node_ips)} node(s)?")

    if response:
        # Reboot remote nodes first
        for ip in remote_ips:
            print(f"=== Rebooting {ip} ===")
            ssh_target = f"{user}@{ip}" if user else ip
            try:
                # Background the reboot so SSH can disconnect cleanly
                subprocess.run(
                    ["ssh", "-o", "ConnectTimeout=5", ssh_target, "nohup sudo reboot &"],
                    timeout=15
                )
            except subprocess.TimeoutExpired:
                print(f"  Connection to {ip} closed (node is rebooting)")

        # Reboot local node last
        if local_ip:
            print("=== Rebooting local node in 5 seconds ===")
            subprocess.run(["sleep", "5"])
            subprocess.run(["sudo", "reboot"])


@app.command()
def health():
    """Watch cluster info with live updates."""
    # ANSI escape codes for colors
    red = r'\x1b[31m'
    reset = r'\x1b[0m'

    # sed command to colorize <unknown> and NotReady in red
    colorize = f"sed -e 's/<unknown>/{red}<unknown>{reset}/g' -e 's/NotReady/{red}NotReady{reset}/g'"

    watch_cmd = f"""
    echo "=== NODES ==="
    kubectl top nodes 2>/dev/null | {colorize}
    echo ""
    echo "=== NODE STATUS ==="
    kubectl get nodes | {colorize}
    echo ""
    echo "=== PODS (all namespaces) ==="
    nodes=$(kubectl get pods -A -o jsonpath='{{range .items[*]}}{{.metadata.namespace}}/{{.metadata.name}}={{.spec.nodeName}}{{\"\\n\"}}{{end}}' 2>/dev/null)
    kubectl top pods -A --sort-by=memory 2>/dev/null | head -15 | while IFS= read -r line; do
      case "$line" in
        NAMESPACE*)
          printf "%-27s %-55s %-12s %-15s %s\\n" "NAMESPACE" "NAME" "CPU(cores)" "MEMORY(bytes)" "NODE"
          ;;
        *)
          ns=$(echo "$line" | awk '{{print $1}}')
          pod=$(echo "$line" | awk '{{print $2}}')
          cpu=$(echo "$line" | awk '{{print $3}}')
          mem=$(echo "$line" | awk '{{print $4}}')
          node=$(echo "$nodes" | grep "^${{ns}}/${{pod}}=" | cut -d= -f2 | head -1)
          printf "%-27s %-55s %-12s %-15s %s\\n" "$ns" "$pod" "$cpu" "$mem" "${{node:-unknown}}"
          ;;
      esac
    done
    echo ""
    echo "=== PROBLEM PODS ==="
    kubectl get pods -A | grep -v Running | grep -v Completed | head -10
    """
    subprocess.run(["watch", "-n", "5", "--color", watch_cmd])


if __name__ == "__main__":
    app()
