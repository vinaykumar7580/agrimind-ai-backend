class MemoryStore:

    def __init__(self):
        self.memory = {}

    def get(self, user_id: str):

        return self.memory.get(user_id, [])

    def add(self, user_id: str, message: str):

        if user_id not in self.memory:
            self.memory[user_id] = []

        self.memory[user_id].append(message)


memory_store = MemoryStore()