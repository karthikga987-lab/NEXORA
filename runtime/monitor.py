import time


class RuntimeMonitor:

    def __init__(
        self,
        scheduler=None,
        reservation_engine=None
    ):

        self.scheduler = scheduler

        self.reservation_engine = (
            reservation_engine
        )

        self.agent_waiting = {}

        self.agent_last_progress = {}

        self.deadlock_threshold = 3.0

        self.completed_steps = 0

        self.recoveries = 0

        self.deadlocks_detected = 0

    # ==========================================
    # REGISTER AGENT
    # ==========================================

    def register_agent(
        self,
        agent
    ):

        now = time.perf_counter()

        self.agent_waiting[
            agent.agent_id
        ] = 0.0

        self.agent_last_progress[
            agent.agent_id
        ] = now

    # ==========================================
    # RECORD PROGRESS
    # ==========================================

    def progress(
        self,
        agent
    ):

        self.agent_last_progress[
            agent.agent_id
        ] = time.perf_counter()

        self.agent_waiting[
            agent.agent_id
        ] = 0.0

        self.completed_steps += 1

    # ==========================================
    # UPDATE WAITING
    # ==========================================

    def update_waiting(
        self,
        agent
    ):

        if agent.agent_id not in (
            self.agent_last_progress
        ):

            self.register_agent(
                agent
            )

        now = time.perf_counter()

        waiting = (
            now
            -
            self.agent_last_progress[
                agent.agent_id
            ]
        )

        if agent.status != "WAITING":

            waiting = 0.0

        self.agent_waiting[
            agent.agent_id
        ] = waiting

        return waiting

    # ==========================================
    # BUILD WAIT-FOR GRAPH
    # ==========================================

    def build_wait_for_graph(
        self,
        agents
    ):

        graph = {
            agent.agent_id: set()
            for agent in agents
        }

        agent_map = {
            agent.agent_id: agent
            for agent in agents
        }

        for agent in agents:

            if agent.status != "WAITING":

                continue

            requested_resource = (
                agent.current_service()
            )

            if requested_resource is None:

                continue

            # ----------------------------------
            # DEPENDENCY 1:
            # RESOURCE CURRENTLY HELD
            # ----------------------------------

            if self.scheduler:

                holders = (
                    self.scheduler
                    .get_holders(
                        requested_resource
                    )
                )

                for holder_id in holders:

                    if (
                        holder_id
                        != agent.agent_id
                        and
                        holder_id
                        in agent_map
                    ):

                        graph[
                            agent.agent_id
                        ].add(
                            holder_id
                        )

            # ----------------------------------
            # DEPENDENCY 2:
            # FUTURE RESERVATION
            # ----------------------------------

            if self.reservation_engine:

                reservation_owners = (
                    self.reservation_engine
                    .get_reservation_owner(
                        requested_resource,
                        agent.agent_id
                    )
                )

                for owner_id in (
                    reservation_owners
                ):

                    if owner_id in agent_map:

                        graph[
                            agent.agent_id
                        ].add(
                            owner_id
                        )

        return graph

    # ==========================================
    # FIND CYCLES
    # ==========================================

    def find_cycles(
        self,
        graph
    ):

        visited = set()

        recursion_stack = set()

        cycles = []

        def dfs(
            node,
            path
        ):

            visited.add(node)

            recursion_stack.add(node)

            path.append(node)

            for neighbour in graph.get(
                node,
                set()
            ):

                if neighbour not in visited:

                    dfs(
                        neighbour,
                        path
                    )

                elif neighbour in (
                    recursion_stack
                ):

                    if neighbour in path:

                        start = path.index(
                            neighbour
                        )

                        cycle = path[
                            start:
                        ].copy()

                        if cycle:

                            normalized = tuple(
                                sorted(
                                    cycle
                                )
                            )

                            existing = [
                                tuple(
                                    sorted(
                                        item
                                    )
                                )
                                for item
                                in cycles
                            ]

                            if normalized not in (
                                existing
                            ):

                                cycles.append(
                                    cycle
                                )

            path.pop()

            recursion_stack.remove(
                node
            )

        for node in graph:

            if node not in visited:

                dfs(
                    node,
                    []
                )

        return cycles

    # ==========================================
    # CHECK DEADLOCK
    # ==========================================

    def check_deadlock(
        self,
        agents
    ):

        graph = (
            self.build_wait_for_graph(
                agents
            )
        )

        cycles = self.find_cycles(
            graph
        )

        if cycles:

            return True, graph, cycles

        return False, graph, []

    # ==========================================
    # CHOOSE RECOVERY VICTIM
    # ==========================================

    def choose_victim(
        self,
        cycle,
        agents
    ):

        agent_map = {
            agent.agent_id: agent
            for agent in agents
        }

        candidates = []

        for agent_id in cycle:

            agent = agent_map.get(
                agent_id
            )

            if agent is None:

                continue

            waiting_time = (
                self.agent_waiting.get(
                    agent_id,
                    0.0
                )
            )

            # Lower priority and shorter
            # waiting time are preferred
            # as recovery victims.

            candidates.append(
                (
                    agent.priority,
                    waiting_time,
                    agent_id
                )
            )

        if not candidates:

            return None

        candidates.sort()

        victim_id = candidates[0][2]

        return agent_map[
            victim_id
        ]

    # ==========================================
    # RECOVER DEADLOCK
    # ==========================================

    def recover(
        self,
        agents
    ):

        deadlocked, graph, cycles = (
            self.check_deadlock(
                agents
            )
        )

        if not deadlocked:

            return False

        self.deadlocks_detected += 1

        print()

        print(
            "==================================="
        )

        print(
            "       DEADLOCK DETECTED"
        )

        print(
            "==================================="
        )

        for cycle in cycles:

            names = []

            for agent_id in cycle:

                for agent in agents:

                    if (
                        agent.agent_id
                        == agent_id
                    ):

                        names.append(
                            agent.name
                        )

            if names:

                print(
                    "[CYCLE] "
                    +
                    " -> ".join(
                        names
                    )
                    +
                    " -> "
                    +
                    names[0]
                )

        # --------------------------------------
        # SELECT VICTIM
        # --------------------------------------

        largest_cycle = max(
            cycles,
            key=len
        )

        victim = self.choose_victim(
            largest_cycle,
            agents
        )

        if victim is None:

            return False

        print()

        print(
            f"[RECOVERY] Selected victim: "
            f"{victim.name}"
        )

        print(
            f"[RECOVERY] Priority: "
            f"{victim.priority}"
        )

        # --------------------------------------
        # CANCEL FUTURE RESERVATION
        # --------------------------------------

        if self.reservation_engine:

            self.reservation_engine\
                .cancel_reservation(
                    victim.agent_id
                )

        # --------------------------------------
        # RESET WAITING STATE
        # --------------------------------------

        if self.scheduler:

            self.scheduler.stop_waiting(
                victim
            )

        victim.status = "READY"

        now = time.perf_counter()

        self.agent_last_progress[
            victim.agent_id
        ] = now

        self.agent_waiting[
            victim.agent_id
        ] = 0.0

        self.recoveries += 1

        print(
            f"[RECOVERY] "
            f"{victim.name} yielded "
            f"its reservation."
        )

        print(
            "[RECOVERY COMPLETE]"
        )

        print(
            "==================================="
        )

        return True

    # ==========================================
    # METRICS
    # ==========================================

    def print_metrics(
        self
    ):

        print()

        print(
            "==================================="
        )

        print(
            "        RUNTIME MONITOR"
        )

        print(
            "==================================="
        )

        print(
            f"Completed Steps : "
            f"{self.completed_steps}"
        )

        print(
            f"Deadlocks       : "
            f"{self.deadlocks_detected}"
        )

        print(
            f"Recoveries      : "
            f"{self.recoveries}"
        )

        print(
            "==================================="
        )