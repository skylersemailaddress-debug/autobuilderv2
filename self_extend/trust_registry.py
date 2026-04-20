class TrustRegistry:
    def __init__(self):
        self.registry = {}

    def register(self, name: str, status: str):
        self.registry[name] = status

    def get(self, name: str):
        return self.registry.get(name)
