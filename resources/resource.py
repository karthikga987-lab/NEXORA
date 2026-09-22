class Resource:

    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity
        self.available = capacity

    def allocate(self):
        if self.available > 0:
            self.available -= 1
            return True

        return False

    def release(self):
        if self.available < self.capacity:
            self.available += 1

    def __str__(self):
        return f"{self.name}: {self.available}/{self.capacity} available"