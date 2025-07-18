from typing import Final
import dns.resolver
from requests.adapters import HTTPAdapter
import requests
import tldextract


_GA4_COLLECT_URL: Final[str] = "https://www.google-analytics.com/mp/collect"


class DNSAdapter(HTTPAdapter):
    def __init__(self, nameservers):
        self.nameservers = nameservers
        super().__init__()

    def resolve(self, host, nameservers, record_type):
        dns_resolver = dns.resolver.Resolver()
        dns_resolver.nameservers = nameservers
        answers = dns_resolver.query(host, record_type)
        for rdata in answers:
            return str(rdata)

    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        if not request.url:
            raise
        ext = tldextract.extract(request.url)
        fqdn = ".".join([ext.subdomain, ext.domain, ext.suffix])
        a_record = self.resolve(fqdn, self.nameservers, "A")
        if not a_record:
            raise
        resolved_url = request.url.replace(fqdn, a_record)
        request.url = resolved_url
        self.poolmanager.connection_pool_kw["server_hostname"] = fqdn
        self.poolmanager.connection_pool_kw["assert_hostname"] = fqdn
        request.headers["Host"] = fqdn

        return super().get_connection_with_tls_context(request, verify, proxies, cert)


class GA4Client:
    def __init__(self, api_secret, measurement_id, client_id):
        self.api_secret = api_secret
        self.measurement_id = measurement_id
        self.client_id = client_id

    def send_event(self, event_name, params):
        url = f"{_GA4_COLLECT_URL}?measurement_id={self.measurement_id}&api_secret={self.api_secret}"

        payload = {
            "client_id": self.client_id,
            "events": [{"name": event_name, "params": params}],
        }
        session = requests.Session()
        session.mount("https://", DNSAdapter(["8.8.8.8"]))
        response = session.post(url, json=payload)
        response.raise_for_status()
        return response
