import time


class RuntimeInterceptor:

    def __init__(
        self,
        scheduler,
        reservation_engine,
        history,
        predictor
    ):

        self.scheduler = scheduler

        self.reservation_engine = (
            reservation_engine
        )

        self.history = history

        self.predictor = predictor

        self.events = []

    def record_event(
        self,
        agent,
        event_type,
        logical_service=None,
        physical_service=None,
        prediction=None,
        confidence=None,
        details=None
    ):

        event = {

            "timestamp":
                time.strftime(
                    "%H:%M:%S"
                ),

            "agent_id":
                agent.agent_id,

            "agent_name":
                agent.name,

            "event":
                event_type,

            "logical_service":
                logical_service,

            "physical_service":
                physical_service,

            "prediction":
                prediction,

            "confidence":
                confidence,

            "details":
                details
        }

        self.events.append(
            event
        )

        print(
            f"[LIVE] "
            f"{event['timestamp']} | "
            f"{agent.name} | "
            f"{event_type}"
        )

        if logical_service:

            print(
                f"       Logical: "
                f"{logical_service}"
            )

        if physical_service:

            print(
                f"       Physical: "
                f"{physical_service}"
            )

        if prediction:

            confidence_text = ""

            if confidence is not None:

                confidence_text = (
                    f" | "
                    f"Confidence: "
                    f"{confidence * 100:.1f}%"
                )

            print(
                f"       Prediction: "
                f"{prediction}"
                f"{confidence_text}"
            )

        if details:

            print(
                f"       Details: "
                f"{details}"
            )

    def get_events(self):

        return list(
            self.events
        )

    def latest_events(
        self,
        count=20
    ):

        return self.events[
            -count:
        ]