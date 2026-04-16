class RunStateStore:
    def __init__(self):
        self.data = {}

    def save(self, run_id, state):
        self.data[run_id] = state

    def load(self, run_id):
        return self.data.get(run_id)
