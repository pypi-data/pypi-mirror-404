"""Backup device configurations using Netmiko."""

import os
from datetime import datetime

from netmiko import ConnectHandler

DEVICES = [
    {"name": "spine1", "host": "172.29.163.101", "device_type": "arista_eos"},
    {"name": "spine2", "host": "172.29.163.102", "device_type": "arista_eos"},
    {"name": "leaf1", "host": "172.29.163.103", "device_type": "arista_eos"},
    {"name": "leaf2", "host": "172.29.163.104", "device_type": "arista_eos"},
]

USERNAME = "admin"
PASSWORD = "Pack3tC0ders"
BACKUP_DIR = "backups"


def backup_device(device: dict) -> bool:
    """
    Connect to a device and backup its running configuration.

    Args:
        device: Dictionary with name, host, and device_type.

    Returns:
        True if backup succeeded, False otherwise.
    """
    name = device["name"]
    host = device["host"]

    print(f"\n{'='*60}")
    print(f"Backing up {name} ({host})")
    print(f"{'='*60}")

    try:
        connection = ConnectHandler(
            device_type=device["device_type"],
            host=host,
            username=USERNAME,
            password=PASSWORD,
            timeout=30,
            auth_timeout=30,
            banner_timeout=30,
        )

        print(f"✓ Connected to {name}")

        output = connection.send_command("show running-config")

        connection.disconnect()
        print(f"✓ Retrieved configuration ({len(output)} bytes)")

        os.makedirs(BACKUP_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{BACKUP_DIR}/{name}_{timestamp}.txt"

        with open(filename, "w") as f:
            f.write(output)

        print(f"✓ Saved to {filename}")
        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def main() -> None:
    """Backup all devices."""
    print("\nDevice Configuration Backup")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {"success": [], "failed": []}

    for device in DEVICES:
        if backup_device(device):
            results["success"].append(device["name"])
        else:
            results["failed"].append(device["name"])

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Successful: {len(results['success'])} - {', '.join(results['success']) or 'None'}")
    print(f"Failed: {len(results['failed'])} - {', '.join(results['failed']) or 'None'}")


if __name__ == "__main__":
    main()
