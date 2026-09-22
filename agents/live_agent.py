import asyncio
import re
import time

from agents.agent import Agent


class LiveAgent:

    def __init__(
        self,
        agent_id,
        name,
        task,
        ai,
        scheduler,
        reservation_engine,
        history,
        predictor,
        interceptor,
        tools,
        monitor=None,
        priority=3,
        max_steps=8
    ):

        self.agent = Agent(
            agent_id,
            name,
            [],
            priority
        )

        self.task = task
        self.ai = ai
        self.scheduler = scheduler
        self.reservation_engine = reservation_engine
        self.history = history
        self.predictor = predictor
        self.interceptor = interceptor
        self.tools = tools
        self.monitor = monitor
        self.priority = priority
        self.max_steps = max_steps

        self.tool_history = []
        self.running = False

        self.previous_service = None
        self.previous_execution_time = 0.0
        self.previous_waiting_time = 0.0
        self.previous_success = True
        self.previous_physical_service = None
        self.previous_substituted = False

        self.completed_requirements = []

        self.execution_plan = (
            self._build_execution_plan()
        )

        self.plan_index = 0

    # ============================================================
    # BUILD EXECUTION PLAN
    # ============================================================

    def _build_execution_plan(self):

        task = self.task.lower()

        operations = []

        python_patterns = [
            r"\bcalculate\b",
            r"\bcalculation\b",
            r"\bcompute\b",
            r"\bmultipl(?:y|ied|ication)\b",
            r"\badd\b",
            r"\bsubtract\b",
            r"\bdivide\b",
            r"\barithmetic\b",
            r"\bequation\b"
        ]

        database_patterns = [
            r"\bdatabase\b",
            r"retrieve .*?(?:resource|system|nexora).*?information",
            r"resource information .*?database",
            r"nexora system information",
            r"stored .*?information"
        ]

        search_patterns = [
            r"\bresearch\b",
            r"\bweb search\b",
            r"\bsearch\b",
            r"\blook up\b",
            r"find .*?information",
            r"current .*?(?:ai|agent|orchestration|external)",
            r"latest .*?(?:ai|agent|orchestration|external)"
        ]

        def first_position(patterns):

            positions = []

            for pattern in patterns:

                match = re.search(
                    pattern,
                    task
                )

                if match:
                    positions.append(
                        match.start()
                    )

            if not positions:
                return None

            return min(positions)

        python_pos = first_position(
            python_patterns
        )

        database_pos = first_position(
            database_patterns
        )

        search_pos = first_position(
            search_patterns
        )

        if search_pos is not None:
            operations.append(
                (
                    search_pos,
                    "SEARCH"
                )
            )

        if database_pos is not None:
            operations.append(
                (
                    database_pos,
                    "DATABASE"
                )
            )

        if python_pos is not None:
            operations.append(
                (
                    python_pos,
                    "PYTHON"
                )
            )

        operations.sort(
            key=lambda item: item[0]
        )

        plan = []

        for _, service in operations:

            if service not in plan:
                plan.append(service)

        if not plan:
            plan = self._fallback_required_tools()

        return plan

    # ============================================================
    # FALLBACK TOOL DETECTION
    # ============================================================

    def _fallback_required_tools(self):

        task = self.task.lower()

        required = []

        if any(
            word in task
            for word in [
                "research",
                "search",
                "web",
                "look up",
                "external information"
            ]
        ):

            required.append(
                "SEARCH"
            )

        if any(
            phrase in task
            for phrase in [
                "calculate",
                "calculation",
                "multiply",
                "multiplied",
                "add",
                "subtract",
                "divide",
                "compute",
                "equation"
            ]
        ):

            required.append(
                "PYTHON"
            )

        if any(
            word in task
            for word in [
                "database",
                "stored",
                "resource information",
                "system information"
            ]
        ):

            required.append(
                "DATABASE"
            )

        return list(
            dict.fromkeys(required)
        )

    def _required_tools(self):

        return list(
            self.execution_plan
        )

    def _missing_requirements(self):

        return [
            tool
            for tool in self.execution_plan
            if tool not in self.completed_requirements
        ]

    def _next_planned_tool(self):

        if (
            self.plan_index
            <
            len(self.execution_plan)
        ):

            return self.execution_plan[
                self.plan_index
            ]

        return None

    # ============================================================
    # BUILD LLM CONTEXT
    # ============================================================

    def _build_context(self):

        context = []

        context.append(
            "NEXORA EXECUTION PLAN:"
        )

        context.append(
            " -> ".join(
                self.execution_plan
            )
            if self.execution_plan
            else
            "No explicit tool operations detected."
        )

        context.append(
            "Current planned operation: "
            +
            str(
                self._next_planned_tool()
            )
        )

        context.append(
            "Completed tools: "
            +
            (
                ", ".join(
                    self.completed_requirements
                )
                if self.completed_requirements
                else
                "none"
            )
        )

        missing = (
            self._missing_requirements()
        )

        context.append(
            "Remaining required tools: "
            +
            (
                ", ".join(missing)
                if missing
                else
                "none"
            )
        )

        if not self.tool_history:

            context.append(
                "\nNo previous tool results."
            )

            return "\n".join(
                context
            )

        context.append(
            "\nPREVIOUS TOOL RESULTS:"
        )

        for index, item in enumerate(
            self.tool_history,
            start=1
        ):

            context.append(
                f"\nSTEP {index}\n"
                f"Tool: {item['tool']}\n"
                f"Query: {item['query']}\n"
                f"Result: {item['result']}"
            )

        return "\n".join(
            context[-35:]
        )

    # ============================================================
    # HISTORY TRANSITION
    # ============================================================

    def _record_transition(
        self,
        next_service
    ):

        if self.previous_service is None:
            return

        self.history.record(
            agent_id=self.agent.agent_id,
            agent_name=self.agent.name,
            current_service=self.previous_service,
            next_service=next_service,
            execution_time=self.previous_execution_time,
            waiting_time=self.previous_waiting_time,
            success=self.previous_success,
            physical_service=self.previous_physical_service,
            substituted=self.previous_substituted,
            substitution_penalty=0.0
        )

        self.previous_service = None

    def _set_previous_execution(
        self,
        service,
        execution_time,
        waiting_time,
        success,
        physical_service,
        substituted
    ):

        self.previous_service = service

        self.previous_execution_time = (
            execution_time
        )

        self.previous_waiting_time = (
            waiting_time
        )

        self.previous_success = success

        self.previous_physical_service = (
            physical_service
        )

        self.previous_substituted = (
            substituted
        )

    # ============================================================
    # REQUEST RESOURCE
    # ============================================================

    async def _request_resource(
        self,
        requested_tool
    ):

        waiting_start = (
            time.perf_counter()
        )

        while True:

            allocated = (
                self.scheduler.request_resource(
                    self.agent
                )
            )

            if allocated:
                break

            self.agent.status = "WAITING"

            self.interceptor.record_event(
                self.agent,
                "WAITING",
                logical_service=requested_tool
            )

            if self.monitor:

                self.monitor.update_waiting(
                    self.agent
                )

            await asyncio.sleep(
                0.2
            )

        waiting_time = (
            time.perf_counter()
            -
            waiting_start
        )

        if self.monitor:

            self.monitor.update_waiting(
                self.agent
            )

        return waiting_time

    # ============================================================
    # CALCULATION EXTRACTION
    # ============================================================

    def _extract_calculation(self):

        task = self.task.lower()

        patterns = [

            (
                r"(\d+)\s*(?:multiplied by|times|x)\s*(\d+)",
                lambda a, b:
                    f"{a} * {b}"
            ),

            (
                r"(\d+)\s*(?:plus|added to)\s*(\d+)",
                lambda a, b:
                    f"{a} + {b}"
            ),

            (
                r"(\d+)\s*(?:minus|subtracted by)\s*(\d+)",
                lambda a, b:
                    f"{a} - {b}"
            ),

            (
                r"(\d+)\s*(?:divided by)\s*(\d+)",
                lambda a, b:
                    f"{a} / {b}"
            )
        ]

        for pattern, builder in patterns:

            match = re.search(
                pattern,
                task
            )

            if match:

                return builder(
                    match.group(1),
                    match.group(2)
                )

        return self.task

    # ============================================================
    # TOOL INPUT
    # ============================================================

    def _get_tool_input(
        self,
        requested_tool,
        query
    ):

        if requested_tool == "PYTHON":

            return self._extract_calculation()

        if query.strip():

            return query

        if requested_tool == "SEARCH":

            return self.task

        if requested_tool == "DATABASE":

            return (
                "Retrieve current NEXORA "
                "resource and system information."
            )

        return self.task

    # ============================================================
    # RUNTIME PLAN ENFORCEMENT
    # ============================================================

    def _enforce_runtime_plan(
        self,
        ai_decision
    ):

        next_tool = (
            self._next_planned_tool()
        )

        if next_tool is None:

            return {
                "tool": "FINISH",
                "query": "",
                "reason":
                    "NEXORA execution plan is complete."
            }

        ai_tool = ai_decision.get(
            "tool",
            "FINISH"
        )

        if ai_tool == next_tool:

            return ai_decision

        self.interceptor.record_event(
            self.agent,
            "ORCHESTRATOR_OVERRIDE",
            logical_service=next_tool,
            details=(
                f"AI proposed {ai_tool}, "
                f"but NEXORA runtime plan "
                f"requires {next_tool} next."
            )
        )

        return {
            "tool": next_tool,
            "query":
                ai_decision.get(
                    "query",
                    ""
                ),
            "reason": (
                "NEXORA enforced planned "
                f"dependency: {next_tool}."
            )
        }

    # ============================================================
    # PREDICTIVE RESERVATION
    # ============================================================

    def _reserve_next_planned_service(
        self,
        completed_service
    ):

        next_tool = (
            self._next_planned_tool()
        )

        if next_tool is None:
            return

        confidence = 1.0

        prediction_source = (
            "EXECUTION PLAN"
        )

        predicted_service = None

        # --------------------------------------------------------
        # Use learned agent-specific history.
        # --------------------------------------------------------

        prediction = (
            self.predictor.get_best_prediction(
                current_service=completed_service,
                agent_id=self.agent.agent_id
            )
        )

        if prediction is not None:

            predicted_service = (
                prediction["service"]
            )

            predicted_confidence = (
                prediction["confidence"]
            )

            # Learned prediction agrees with the
            # required runtime dependency.
            if predicted_service == next_tool:

                confidence = (
                    predicted_confidence
                )

                prediction_source = (
                    "LEARNED RUNTIME HISTORY"
                )

            # Prediction disagrees with the plan.
            else:

                confidence = (
                    predicted_confidence
                    * 0.50
                )

                prediction_source = (
                    "PLAN + LEARNED MODEL DISAGREEMENT"
                )

            self.interceptor.record_event(
                self.agent,
                "PREDICTIVE_DECISION",
                logical_service=next_tool,
                prediction=predicted_service,
                confidence=confidence,
                details=(
                    f"Completed service: "
                    f"{completed_service} | "
                    f"Source: "
                    f"{prediction_source}"
                )
            )

        else:

            self.interceptor.record_event(
                self.agent,
                "PREDICTIVE_DECISION",
                logical_service=next_tool,
                prediction=next_tool,
                confidence=confidence,
                details=(
                    f"Completed service: "
                    f"{completed_service} | "
                    "No learned prediction available; "
                    "using execution plan."
                )
            )

        # --------------------------------------------------------
        # Reserve using learned confidence.
        # --------------------------------------------------------

        try:

            self.reservation_engine.reserve(
                self.agent,
                next_tool,
                confidence
            )

            self.interceptor.record_event(
                self.agent,
                "PLAN_RESERVATION",
                logical_service=next_tool,
                prediction=(
                    predicted_service
                    if predicted_service
                    else next_tool
                ),
                confidence=confidence,
                details=(
                    f"Reservation confidence: "
                    f"{confidence * 100:.1f}% | "
                    f"Source: "
                    f"{prediction_source}"
                )
            )

        except Exception as error:

            self.interceptor.record_event(
                self.agent,
                "RESERVATION_WARNING",
                logical_service=next_tool,
                details=str(error)
            )

    # ============================================================
    # MAIN EXECUTION
    # ============================================================

    async def execute(self):

        self.running = True

        self.agent.status = "READY"

        print()
        print("===================================")
        print(
            f"       {self.agent.name.upper()}"
        )
        print("===================================")

        print(
            f"Task: {self.task}"
        )

        print(
            "Required execution plan:"
        )

        print(
            " -> ".join(
                self.execution_plan
            )
            if self.execution_plan
            else
            "None detected"
        )

        for step_number in range(
            1,
            self.max_steps + 1
        ):

            if not self.running:
                break

            print()

            print(
                f"[{self.agent.name}] "
                f"LIVE STEP {step_number}"
            )

            context = (
                self._build_context()
            )

            ai_decision = (
                self.ai.choose_action(
                    task=self.task,
                    context=context,
                    available_tools=[
                        "SEARCH",
                        "DATABASE",
                        "PYTHON",
                        "FINISH"
                    ]
                )
            )

            print(
                f"[{self.agent.name}] "
                f"[AI PROPOSAL] "
                f"{ai_decision['tool']}"
            )

            if ai_decision.get("reason"):

                print(
                    f"[{self.agent.name}] "
                    f"[AI REASON] "
                    f"{ai_decision['reason']}"
                )

            decision = (
                self._enforce_runtime_plan(
                    ai_decision
                )
            )

            requested_tool = (
                decision["tool"]
            )

            query = decision.get(
                "query",
                ""
            )

            reason = decision.get(
                "reason",
                ""
            )

            print(
                f"[{self.agent.name}] "
                f"[AI DECISION] "
                f"{requested_tool}"
            )

            print(
                f"[{self.agent.name}] "
                f"[AI REASON] "
                f"{reason}"
            )

            if query:

                print(
                    f"[{self.agent.name}] "
                    f"[AI QUERY] "
                    f"{query}"
                )

            self.interceptor.record_event(
                self.agent,
                "AI_DECISION",
                logical_service=requested_tool,
                details=reason
            )

            if requested_tool == "FINISH":

                self._record_transition(
                    None
                )

                self.interceptor.record_event(
                    self.agent,
                    "AI_FINISHED",
                    details=reason
                )

                break

            self._record_transition(
                requested_tool
            )

            predictions = (
                self.predictor.predict_next(
                    requested_tool,
                    agent_id=self.agent.agent_id
                )
            )

            if predictions:

                next_prediction = (
                    next(
                        iter(predictions)
                    )
                )

                confidence = (
                    predictions[
                        next_prediction
                    ]
                )

                self.interceptor.record_event(
                    self.agent,
                    "PREDICTION",
                    prediction=next_prediction,
                    confidence=confidence,
                    details=(
                        "Prediction learned "
                        "from this agent's "
                        "runtime history."
                    )
                )

            self.agent.workflow = [
                requested_tool
            ]

            self.agent.current_step = 0

            self.agent.status = "READY"

            waiting_time = (
                await self._request_resource(
                    requested_tool
                )
            )

            physical_resource = (
                self.scheduler.get_allocated_resource(
                    self.agent.agent_id
                )
            )

            if physical_resource is None:

                physical_resource = (
                    requested_tool
                )

            substituted = (
                physical_resource
                !=
                requested_tool
            )

            self.interceptor.record_event(
                self.agent,
                "RESOURCE_ALLOCATED",
                logical_service=requested_tool,
                physical_service=physical_resource,
                details=(
                    "SUBSTITUTED"
                    if substituted
                    else
                    "DIRECT ALLOCATION"
                )
            )

            self.agent.status = "RUNNING"

            execution_start = (
                time.perf_counter()
            )

            if physical_resource not in self.tools:

                self.scheduler.release_resource(
                    requested_tool,
                    self.agent.agent_id
                )

                self.interceptor.record_event(
                    self.agent,
                    "TOOL_ERROR",
                    logical_service=requested_tool,
                    physical_service=physical_resource,
                    details=(
                        "No tool implementation exists."
                    )
                )

                self._set_previous_execution(
                    requested_tool,
                    0.0,
                    waiting_time,
                    False,
                    physical_resource,
                    substituted
                )

                self.plan_index += 1

                continue

            tool = self.tools[
                physical_resource
            ]

            tool_input = (
                self._get_tool_input(
                    requested_tool,
                    query
                )
            )

            result = tool.run(
                tool_input
            )

            execution_time = (
                time.perf_counter()
                -
                execution_start
            )

            success = (
                "error"
                not in result
            )

            result_value = result.get(
                "result",
                result
            )

            self.interceptor.record_event(
                self.agent,
                "TOOL_COMPLETED",
                logical_service=requested_tool,
                physical_service=physical_resource,
                details=str(result_value)
            )

            self.scheduler.release_resource(
                requested_tool,
                self.agent.agent_id
            )

            self.agent.status = "READY"

            self.tool_history.append(
                {
                    "tool":
                        requested_tool,
                    "query":
                        tool_input,
                    "result":
                        str(result_value)
                }
            )

            if requested_tool not in (
                self.completed_requirements
            ):

                self.completed_requirements.append(
                    requested_tool
                )

            self._set_previous_execution(
                requested_tool,
                execution_time,
                waiting_time,
                success,
                physical_resource,
                substituted
            )

            if self.monitor:

                self.monitor.progress(
                    self.agent
                )

            self.plan_index += 1

            # IMPORTANT:
            # Pass the service that just completed.
            # This allows the learned model to predict
            # the next dependency using previous runs.
            self._reserve_next_planned_service(
                completed_service=requested_tool
            )

            await asyncio.sleep(
                0.2
            )

        if self.previous_service:

            self._record_transition(
                None
            )

        self.agent.status = (
            "COMPLETED"
        )

        self.running = False

        self.interceptor.record_event(
            self.agent,
            "WORKFLOW_COMPLETED"
        )

        print()

        print(
            "==================================="
        )

        print(
            f"       {self.agent.name} FINISHED"
        )

        print(
            "==================================="
        )

        print()

        print(
            "TOOLS USED: "
            +
            ", ".join(
                item["tool"]
                for item in self.tool_history
            )
        )

        return self.tool_history