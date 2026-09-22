from collections import defaultdict


class PredictionEngine:

    def __init__(self, history):
        self.history = history

    # ============================================================
    # PREDICT NEXT SERVICE
    # ============================================================

    def predict_next(
        self,
        current_service,
        agent_id=None
    ):
        """
        Predict the next service.

        If agent_id is provided:
            Only that agent's runtime history is used.

        If agent_id is None:
            All runtime history is used.

        This keeps backward compatibility with the
        original global prediction API.
        """

        transition_counts = defaultdict(int)
        total = 0

        for event in self.history.get_events():

            # Match current service
            if event["current_service"] != current_service:
                continue

            # Optional agent-specific filtering
            if (
                agent_id is not None
                and event["agent_id"] != agent_id
            ):
                continue

            next_service = event["next_service"]

            # Terminal transition means workflow finished.
            # It is not a future resource dependency.
            if next_service is None:
                continue

            transition_counts[
                next_service
            ] += 1

            total += 1

        if total == 0:
            return {}

        predictions = {}

        for service, count in transition_counts.items():

            predictions[service] = (
                count / total
            )

        return dict(
            sorted(
                predictions.items(),
                key=lambda item: item[1],
                reverse=True
            )
        )

    # ============================================================
    # EXPLICIT AGENT-AWARE PREDICTION
    # ============================================================

    def predict_next_for_agent(
        self,
        agent_id,
        current_service
    ):
        """
        Convenience method for explicitly requesting
        an agent-specific prediction.
        """

        return self.predict_next(
            current_service=current_service,
            agent_id=agent_id
        )

    # ============================================================
    # BUILD AGENT-SPECIFIC SERVICE GRAPH
    # ============================================================

    def build_agent_graph(
        self,
        agent_id
    ):
        """
        Build a learned service graph using only
        one agent's runtime history.
        """

        graph = defaultdict(
            lambda: defaultdict(int)
        )

        for event in self.history.get_events():

            if event["agent_id"] != agent_id:
                continue

            current_service = (
                event["current_service"]
            )

            next_service = (
                event["next_service"]
            )

            if (
                current_service is None
                or next_service is None
            ):
                continue

            graph[
                current_service
            ][
                next_service
            ] += 1

        return graph

    # ============================================================
    # BEST PREDICTION
    # ============================================================

    def get_best_prediction(
        self,
        current_service,
        agent_id=None
    ):
        """
        Return the highest-confidence predicted
        next service.
        """

        predictions = self.predict_next(
            current_service=current_service,
            agent_id=agent_id
        )

        if not predictions:
            return None

        next_service = next(
            iter(predictions)
        )

        return {
            "service": next_service,
            "confidence": predictions[
                next_service
            ]
        }

    # ============================================================
    # SHOW SINGLE PREDICTION
    # ============================================================

    def show_prediction(
        self,
        current_service,
        agent_id=None,
        agent_name=None
    ):
        """
        Display either a global or agent-specific
        prediction.
        """

        predictions = self.predict_next(
            current_service=current_service,
            agent_id=agent_id
        )

        if agent_name is not None:

            print(
                f"\nPrediction for "
                f"{agent_name}: "
                f"{current_service}"
            )

        else:

            print(
                f"\nPrediction for: "
                f"{current_service}"
            )

        if not predictions:

            print(
                "No historical data available."
            )

            return

        for service, probability in (
            predictions.items()
        ):

            print(
                f"  {service}: "
                f"{probability * 100:.1f}%"
            )

    # ============================================================
    # SHOW COMPLETE AGENT-AWARE GRAPH
    # ============================================================

    def show_agent_prediction(
        self,
        agent_id,
        agent_name
    ):
        """
        Display the learned service graph for
        one specific agent.
        """

        print()
        print(
            f"{agent_name} "
            f"(Agent ID: {agent_id})"
        )

        graph = self.build_agent_graph(
            agent_id
        )

        if not graph:

            print(
                "  No learned transitions yet."
            )

            return

        for service in graph:

            total = sum(
                graph[service].values()
            )

            predictions = []

            for (
                next_service,
                count
            ) in graph[service].items():

                probability = (
                    count / total
                )

                predictions.append(
                    (
                        next_service,
                        probability
                    )
                )

            predictions.sort(
                key=lambda item: item[1],
                reverse=True
            )

            for (
                next_service,
                probability
            ) in predictions:

                print(
                    f"  {service} -> "
                    f"{next_service}: "
                    f"{probability * 100:.1f}%"
                )

    # ============================================================
    # SHOW ALL AGENT-AWARE PREDICTIONS
    # ============================================================

    def show_agent_predictions(
        self,
        agents
    ):

        print()
        print(
            "==================================="
        )
        print(
            "       AGENT-AWARE PREDICTIONS"
        )
        print(
            "==================================="
        )

        for agent in agents:

            self.show_agent_prediction(
                agent_id=agent.agent_id,
                agent_name=agent.name
            )