import json
import os
from datetime import datetime


class RuntimeHistory:

    def __init__(
        self,
        storage_path="runtime_history.json"
    ):

        self.storage_path = storage_path
        self.events = []

        self.load()

    # ============================================================
    # RECORD EVENT
    # ============================================================

    def record(
        self,
        agent_id,
        agent_name,
        current_service,
        next_service,
        execution_time,
        waiting_time=0.0,
        success=True,
        physical_service=None,
        substituted=False,
        substitution_penalty=0.0
    ):

        if physical_service is None:
            physical_service = current_service

        event = {
            "timestamp":
                datetime.now().isoformat(),

            "agent_id":
                agent_id,

            "agent_name":
                agent_name,

            "current_service":
                current_service,

            "physical_service":
                physical_service,

            "next_service":
                next_service,

            "execution_time":
                execution_time,

            "waiting_time":
                waiting_time,

            "success":
                success,

            "substituted":
                substituted,

            "substitution_penalty":
                substitution_penalty
        }

        self.events.append(event)

        self.save()

    # ============================================================
    # SAVE
    # ============================================================

    def save(self):

        try:

            with open(
                self.storage_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.events,
                    file,
                    indent=2
                )

        except Exception as error:

            print(
                f"[HISTORY WARNING] "
                f"Could not save runtime history: "
                f"{error}"
            )

    # ============================================================
    # LOAD
    # ============================================================

    def load(self):

        if not os.path.exists(
            self.storage_path
        ):

            self.events = []

            return

        try:

            with open(
                self.storage_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(data, list):

                self.events = data

            else:

                self.events = []

        except Exception as error:

            print(
                f"[HISTORY WARNING] "
                f"Could not load runtime history: "
                f"{error}"
            )

            self.events = []

    # ============================================================
    # ACCESS
    # ============================================================

    def get_events(self):

        return self.events

    # ============================================================
    # METRICS
    # ============================================================

    def get_substitution_count(self):

        return sum(
            1
            for event in self.events
            if event["substituted"]
        )

    def get_total_waiting_time(self):

        return sum(
            event["waiting_time"]
            for event in self.events
        )

    def get_total_execution_time(self):

        return sum(
            event["execution_time"]
            for event in self.events
        )

    # ============================================================
    # DISPLAY
    # ============================================================

    def show_history(self):

        print(
            "\n===== RUNTIME HISTORY =====\n"
        )

        if not self.events:

            print(
                "No runtime history available."
            )

            return

        for event in self.events:

            logical = (
                event["current_service"]
            )

            physical = (
                event["physical_service"]
            )

            if event["substituted"]:

                service_display = (
                    f"{logical} "
                    f"-> "
                    f"{physical} "
                    f"(SUBSTITUTED)"
                )

            else:

                service_display = logical

            print(
                f"{event['agent_name']}: "
                f"{service_display} -> "
                f"{event['next_service']} | "
                f"Execution: "
                f"{event['execution_time']:.2f}s | "
                f"Waiting: "
                f"{event['waiting_time']:.2f}s"
            )