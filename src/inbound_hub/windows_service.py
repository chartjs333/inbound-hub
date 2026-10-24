"""Optional Windows SCM host. Import/installation has no effect unless explicitly invoked."""

import threading

import uvicorn

from inbound_hub.__main__ import configured_app


class ServiceHost:
    def __init__(self, factory=configured_app, server_factory=uvicorn.Server):
        self.factory, self.server_factory = factory, server_factory
        self.stopping = threading.Event()
        self.restart_requested = threading.Event()
        self.server = None

    def restart(self):
        self.restart_requested.set()
        if self.server:
            self.server.should_exit = True

    def stop(self):
        self.stopping.set()
        if self.server:
            self.server.should_exit = True

    def run(self):
        while not self.stopping.is_set():
            self.restart_requested.clear()
            app, port = self.factory(self.restart)
            self.server = self.server_factory(uvicorn.Config(app, host="127.0.0.1", port=port))
            self.server.run()
            if not self.restart_requested.is_set():
                break


def main():
    import win32service
    import win32serviceutil

    class InboundHubService(win32serviceutil.ServiceFramework):
        _svc_name_ = "InboundHub"
        _svc_display_name_ = "Inbound Hub"
        _svc_description_ = "Inbound coordination service; tray is optional."

        def __init__(self, args):
            super().__init__(args)
            self.host = ServiceHost()

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING, waitHint=60000)
            self.host.stop()

        def SvcDoRun(self):
            self.host.run()

    win32serviceutil.HandleCommandLine(InboundHubService)
