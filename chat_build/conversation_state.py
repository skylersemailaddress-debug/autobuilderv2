class ConversationState:
    def __init__(self) -> None:
        self.history = []

    def append(self, message: str) -> None:
        self.history.append(message)

    def get(self) -> list:
        return self.history
