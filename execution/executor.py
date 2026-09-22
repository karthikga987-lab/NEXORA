import asyncio
import time


class Executor:

    def __init__(
        self,
        scheduler,
        history=None,
        predictor=None,
        reservation_engine=None
    ):

        self.scheduler = scheduler

        self.history = history

        self.predictor = predictor

        self.reservation_engine = (
            reservation_engine
        )

    # ======================================
    # PREDICT AND RESERVE
    # ======================================

    def predict_and_reserve(
        self,
        agent,
        current_service
    ):

        if self.predictor is None:

            return

        if self.reservation_engine is None:

            return

        predictions = (
            self.predictor.predict_next(
                current_service
            )
        )

        if not predictions:

            return

        next_service = next(
            iter(predictions)
        )

        confidence = predictions[
            next_service
        ]

        if next_service == current_service:

            return

        self.reservation_engine.reserve(
            agent,
            next_service,
            confidence
        )

    # ======================================
    # EXECUTE ONE STEP
    # ======================================

    async def execute_agent_step(
        self,
        agent
    ):

        logical_service = (
            agent.current_service()
        )

        if logical_service is None:

            agent.status = "COMPLETED"

            return True

        waiting_start = (
            time.perf_counter()
        )

        while True:

            allocated = (
                self.scheduler
                .request_resource(
                    agent
                )
            )

            if allocated:

                break

            await asyncio.sleep(
                0.2
            )

        waiting_time = (
            time.perf_counter()
            -
            waiting_start
        )

        # ==================================
        # PHYSICAL RESOURCE
        # ==================================

        physical_service = (
            self.scheduler
            .get_allocated_resource(
                agent.agent_id
            )
        )

        if physical_service is None:

            physical_service = (
                logical_service
            )

        substituted = (
            physical_service
            != logical_service
        )

        substitution_penalty = 0.0

        if substituted:

            rules = (
                self.scheduler
                .registry
                .get_substitutes(
                    logical_service
                )
            )

            for rule in rules:

                if (
                    rule["resource"]
                    == physical_service
                ):

                    substitution_penalty = (
                        rule["penalty"]
                    )

                    break

        # ==================================
        # FAIRNESS
        # ==================================

        if waiting_time > 0.05:

            fairness_score = (
                self.scheduler
                .calculate_fairness_score(
                    agent,
                    waiting_time
                )
            )

            print(
                f"[FAIRNESS] "
                f"{agent.name} | "
                f"Waited: "
                f"{waiting_time:.2f}s | "
                f"Score: "
                f"{fairness_score:.2f}"
            )

        # ==================================
        # EXECUTION MESSAGE
        # ==================================

        if substituted:

            print(
                f"[EXECUTING - SUBSTITUTE] "
                f"{agent.name} | "
                f"Logical: "
                f"{logical_service} | "
                f"Physical: "
                f"{physical_service}"
            )

        else:

            print(
                f"[EXECUTING] "
                f"{agent.name} is using "
                f"{logical_service}"
            )

        execution_start = (
            time.perf_counter()
        )

        await asyncio.sleep(
            1
        )

        execution_time = (
            time.perf_counter()
            -
            execution_start
        )

        # ==================================
        # NEXT SERVICE
        # ==================================

        next_step = (
            agent.current_step
            + 1
        )

        if next_step < len(
            agent.workflow
        ):

            next_service = (
                agent.workflow[
                    next_step
                ]
            )

        else:

            next_service = None

        # ==================================
        # RELEASE PHYSICAL RESOURCE
        # ==================================

        self.scheduler.release_resource(
            logical_service,
            agent.agent_id
        )

        # ==================================
        # RECORD HISTORY
        # ==================================

        if self.history:

            self.history.record(

                agent_id=
                    agent.agent_id,

                agent_name=
                    agent.name,

                current_service=
                    logical_service,

                next_service=
                    next_service,

                execution_time=
                    execution_time,

                waiting_time=
                    waiting_time,

                success=True,

                physical_service=
                    physical_service,

                substituted=
                    substituted,

                substitution_penalty=
                    substitution_penalty
            )

        # ==================================
        # PREDICT NEXT SERVICE
        # ==================================

        if next_service is not None:

            self.predict_and_reserve(
                agent,
                logical_service
            )

        # ==================================
        # ADVANCE
        # ==================================

        agent.advance()

        if agent.status != "COMPLETED":

            agent.status = "READY"

        # ==================================
        # CLEANUP
        # ==================================

        if (
            agent.status
            == "COMPLETED"
        ):

            if self.reservation_engine:

                self.reservation_engine\
                    .cleanup_agent(
                        agent
                    )

        print(
            f"[COMPLETED STEP] "
            f"{agent.name}"
        )

        return True

    # ======================================
    # RUN AGENT
    # ======================================

    async def run_agent(
        self,
        agent
    ):

        print(
            f"[STARTED] "
            f"{agent.name}"
        )

        while (
            agent.status
            != "COMPLETED"
        ):

            await self.execute_agent_step(
                agent
            )

        if self.reservation_engine:

            self.reservation_engine\
                .cleanup_agent(
                    agent
                )

        print(
            f"[FINISHED] "
            f"{agent.name}"
        )