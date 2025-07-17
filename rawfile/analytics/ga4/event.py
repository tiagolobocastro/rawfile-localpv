class OpenEBSEventBuilder:
    def __init__(self):
        self.params = {}

    def project(self, value):
        self.params["project"] = value
        return self

    def k8s_version(self, value):
        self.params["k8s_version"] = value
        return self

    def engine_name(self, value):
        self.params["engine_name"] = value
        return self

    def engine_version(self, value):
        self.params["engine_version"] = value
        return self

    def category(self, value):
        self.params["event_category"] = value
        return self

    def k8s_default_ns_uid(self, value):
        self.params["k8s_default_ns_uid"] = value
        return self

    def engine_installer(self, value):
        self.params["engine_installer"] = value
        return self

    def node_os(self, value):
        self.params["node_os"] = value
        return self

    def node_kernel_version(self, value):
        self.params["node_kernel_version"] = value
        return self

    def node_arch(self, value):
        self.params["node_arch"] = value
        return self

    def volume_name(self, value):
        self.params["vol_name"] = value
        return self

    def volume_claim_name(self, value):
        self.params["vol_claim_name"] = value
        return self

    def node_count(self, value):
        self.params["node_count"] = value
        return self

    def replica_count(self, value):
        self.params["vol_replica_count"] = value
        return self

    def volume_capacity(self, value):
        self.params["vol_capacity"] = value
        return self

    def build(self):
        return self.params
