"""Optional Windows tray shell; exiting it never stops the service."""

import os
import webbrowser

import httpx


class TrayController:
    def __init__(self, base_url: str, token: str, client=None):
        from urllib.parse import urlsplit

        if urlsplit(base_url).hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("Tray control is restricted to the local service")
        self.base_url, self.token = base_url.rstrip("/"), token
        self.client = client or httpx.Client(timeout=5, trust_env=False)

    def status(self):
        response = self.client.get(
            self.base_url + "/control/status", headers={"Authorization": "Bearer " + self.token}
        )
        response.raise_for_status()
        return response.json()

    def action(self, name):
        if name not in ("pause", "resume", "restart"):
            raise ValueError("Unsupported control action")
        response = self.client.post(
            self.base_url + "/control/" + name, headers={"Authorization": "Bearer " + self.token}
        )
        response.raise_for_status()


def main():
    import pystray
    from PIL import Image

    controller = TrayController(
        os.environ.get("HUB_SERVICE_URL", "http://127.0.0.1:8080"), os.environ["HUB_CONTROL_TOKEN"]
    )

    def status_text(item):
        try:
            result = controller.status()
            return (
                ", ".join(f"{k}: {v['state']}" for k, v in result["adapters"].items())
                or "No adapters"
            )
        except httpx.HTTPError:
            return "Service unavailable"

    menu = pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.MenuItem("Open UI", lambda: webbrowser.open(controller.base_url + "/docs")),
        pystray.MenuItem("Pause All", lambda: controller.action("pause")),
        pystray.MenuItem("Resume All", lambda: controller.action("resume")),
        pystray.MenuItem("Restart service", lambda: controller.action("restart")),
        pystray.MenuItem("Exit tray", lambda icon: icon.stop()),
    )
    pystray.Icon("inbound-hub", Image.new("RGB", (32, 32), "#2457aa"), "Inbound Hub", menu).run()
