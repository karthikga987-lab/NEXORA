class Agent:

    def __init__(self, agent_id, name, workflow, priority=1):

        self.agent_id = agent_id
        self.name = name
        self.workflow = workflow
        self.priority = priority

        self.current_step = 0
        self.status = "READY"

    def current_service(self):

        if self.current_step < len(self.workflow):
            return self.workflow[self.current_step]

        return None

    def advance(self):

        self.current_step += 1

        if self.current_step >= len(self.workflow):
            self.status = "COMPLETED"

    def __str__(self):

        return (
            f"{self.name} | "
            f"Status: {self.status} | "
            f"Current Service: {self.current_service()}"
        )