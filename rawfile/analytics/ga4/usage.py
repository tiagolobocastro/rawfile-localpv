from .client import GA4Client
from .event import OpenEBSEventBuilder


class Usage:
    def __init__(self, api_secret, measurement_id, client_id):
        self.client = GA4Client(api_secret, measurement_id, client_id)
        self.builder = OpenEBSEventBuilder()

    def install(self):
        return self.builder.category("install")

    def volume_provision(self):
        return self.builder.category("volume_provision")

    def send(self):
        event = self.builder.build()
        self.client.send_event("openebs_event", event)
