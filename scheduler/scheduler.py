import time


class Scheduler:

    def __init__(
        self,
        registry,
        reservation_engine=None
    ):

        self.registry = registry

        self.reservation_engine = (
            reservation_engine
        )

        # Agents currently waiting.
        self.waiting_agents = []

        # Time at which each agent started waiting.
        self.wait_start_times = {}

        # Aging contribution.
        self.aging_factor = 0.10

        # Resource ownership.
        self.resource_holders = {}

        # Actual physical resource allocated
        # to each agent.
        #
        # Example:
        #
        # {
        #     3: "SEARCH"
        # }
        #
        # means agent 3 logically requested
        # DATABASE but is physically using SEARCH.
        self.agent_allocations = {}

        # Statistics.
        self.substitutions = 0

    # ======================================
    # WAITING TIME
    # ======================================

    def get_waiting_time(
        self,
        agent
    ):

        if agent.agent_id not in (
            self.wait_start_times
        ):

            return 0.0

        return (
            time.perf_counter()
            -
            self.wait_start_times[
                agent.agent_id
            ]
        )

    # ======================================
    # FAIRNESS SCORE
    # ======================================

    def calculate_fairness_score(
        self,
        agent,
        waiting_time
    ):

        priority_score = min(
            agent.priority / 5.0,
            1.0
        )

        waiting_score = min(
            waiting_time / 5.0,
            1.0
        )

        score = (
            (0.40 * priority_score)
            +
            (0.60 * waiting_score)
        )

        return score

    # ======================================
    # SCHEDULING SCORE
    # ======================================

    def calculate_scheduling_score(
        self,
        agent
    ):

        waiting_time = (
            self.get_waiting_time(
                agent
            )
        )

        return (
            self.calculate_fairness_score(
                agent,
                waiting_time
            )
        )

    # ======================================
    # START WAITING
    # ======================================

    def mark_waiting(
        self,
        agent
    ):

        if agent.agent_id not in (
            self.wait_start_times
        ):

            self.wait_start_times[
                agent.agent_id
            ] = time.perf_counter()

        if agent not in self.waiting_agents:

            self.waiting_agents.append(
                agent
            )

        agent.status = "WAITING"

    # ======================================
    # STOP WAITING
    # ======================================

    def stop_waiting(
        self,
        agent
    ):

        if agent.agent_id in (
            self.wait_start_times
        ):

            del self.wait_start_times[
                agent.agent_id
            ]

        self.remove_from_waiting(
            agent
        )

    # ======================================
    # REGISTER HOLDER
    # ======================================

    def register_holder(
        self,
        resource_name,
        agent_id
    ):

        if resource_name not in (
            self.resource_holders
        ):

            self.resource_holders[
                resource_name
            ] = set()

        self.resource_holders[
            resource_name
        ].add(
            agent_id
        )

    # ======================================
    # REMOVE HOLDER
    # ======================================

    def remove_holder(
        self,
        resource_name,
        agent_id
    ):

        if resource_name not in (
            self.resource_holders
        ):

            return

        self.resource_holders[
            resource_name
        ].discard(
            agent_id
        )

        if not self.resource_holders[
            resource_name
        ]:

            del self.resource_holders[
                resource_name
            ]

    # ======================================
    # GET HOLDERS
    # ======================================

    def get_holders(
        self,
        resource_name
    ):

        return set(
            self.resource_holders.get(
                resource_name,
                set()
            )
        )

    # ======================================
    # WAITING AGENTS
    # ======================================

    def get_waiting_for_resource(
        self,
        resource_name
    ):

        agents = []

        for agent in self.waiting_agents:

            if (
                agent.status == "WAITING"
                and
                agent.current_service()
                == resource_name
            ):

                agents.append(
                    agent
                )

        return agents

    # ======================================
    # SELECT BEST WAITING AGENT
    # ======================================

    def select_best_waiting_agent(
        self,
        resource_name
    ):

        candidates = (
            self.get_waiting_for_resource(
                resource_name
            )
        )

        if not candidates:

            return None

        return self.select_best_candidate(
            candidates
        )

    # ======================================
    # SELECT BEST CANDIDATE
    # ======================================

    def select_best_candidate(
        self,
        candidates
    ):

        ranked = []

        for agent in candidates:

            waiting_time = (
                self.get_waiting_time(
                    agent
                )
            )

            score = (
                self.calculate_scheduling_score(
                    agent
                )
            )

            ranked.append(
                (
                    score,
                    waiting_time,
                    agent.priority,
                    agent
                )
            )

        ranked.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2]
            ),
            reverse=True
        )

        return ranked[0][3]

    # ======================================
    # FAIRNESS ARBITRATION
    # ======================================

    def can_allocate_fairly(
        self,
        agent,
        service
    ):

        candidates = (
            self.get_waiting_for_resource(
                service
            )
        )

        if agent not in candidates:

            candidates.append(
                agent
            )

        if len(candidates) <= 1:

            return True

        best_agent = (
            self.select_best_candidate(
                candidates
            )
        )

        return (
            best_agent.agent_id
            == agent.agent_id
        )

    # ======================================
    # GET ACTUAL ALLOCATION
    # ======================================

    def get_allocated_resource(
        self,
        agent_id
    ):

        return self.agent_allocations.get(
            agent_id
        )

    # ======================================
    # CHECK RESERVATION
    # ======================================

    def has_own_reservation(
        self,
        agent,
        service
    ):

        if not self.reservation_engine:

            return False

        return (
            self.reservation_engine
            .has_reservation(
                agent.agent_id,
                service
            )
        )

    # ======================================
    # CHECK RESERVED CAPACITY
    # ======================================

    def reserved_for_others(
        self,
        service,
        agent
    ):

        if not self.reservation_engine:

            return 0

        return (
            self.reservation_engine
            .reserved_for_others(
                service,
                agent.agent_id
            )
        )

    # ======================================
    # ALLOCATE PHYSICAL RESOURCE
    # ======================================

    def allocate_physical_resource(
        self,
        agent,
        logical_service,
        physical_service
    ):

        resource = self.registry.get(
            physical_service
        )

        if resource is None:

            return False

        if resource.available <= 0:

            return False

        resource.allocate()

        self.register_holder(
            physical_service,
            agent.agent_id
        )

        self.agent_allocations[
            agent.agent_id
        ] = physical_service

        self.stop_waiting(
            agent
        )

        agent.status = "RUNNING"

        if logical_service != physical_service:

            self.substitutions += 1

            print(
                f"[RESOURCE SUBSTITUTION] "
                f"{agent.name} | "
                f"Requested: "
                f"{logical_service} | "
                f"Using: "
                f"{physical_service}"
            )

            rules = (
                self.registry
                .get_substitutes(
                    logical_service
                )
            )

            for rule in rules:

                if (
                    rule["resource"]
                    == physical_service
                ):

                    print(
                        f"  Reason: "
                        f"{rule['reason']}"
                    )

                    print(
                        f"  Penalty: "
                        f"{rule['penalty']:.2f}"
                    )

                    break

        else:

            print(
                f"[ALLOCATED] "
                f"{agent.name} -> "
                f"{physical_service}"
            )

        return True

    # ======================================
    # REQUEST RESOURCE
    # ======================================

    def request_resource(
        self,
        agent
    ):

        logical_service = (
            agent.current_service()
        )

        if logical_service is None:

            return False

        resource = self.registry.get(
            logical_service
        )

        if resource is None:

            print(
                f"[ERROR] Resource "
                f"'{logical_service}' "
                f"not found."
            )

            return False

        # ==================================
        # RESERVATION-AWARE LOGIC
        # ==================================

        if self.reservation_engine:

            own_reservation = (
                self.reservation_engine
                .has_reservation(
                    agent.agent_id,
                    logical_service
                )
            )

            reserved_for_others = (
                self.reservation_engine
                .reserved_for_others(
                    logical_service,
                    agent.agent_id
                )
            )

            # --------------------------------
            # OWN RESERVATION
            # --------------------------------

            if own_reservation:

                if resource.available > 0:

                    allocated = (
                        self.allocate_physical_resource(
                            agent,
                            logical_service,
                            logical_service
                        )
                    )

                    if allocated:

                        self.reservation_engine\
                            .consume_reservation(
                                agent.agent_id,
                                logical_service
                            )

                        print(
                            f"[ALLOCATED - RESERVED] "
                            f"{agent.name} -> "
                            f"{logical_service}"
                        )

                        return True

            # --------------------------------
            # RESERVED FOR OTHERS
            # --------------------------------

            else:

                effective_available = (
                    resource.available
                    -
                    reserved_for_others
                )

                if effective_available <= 0:

                    # Before waiting, check whether
                    # a valid fallback exists.

                    substitute = (
                        self.registry
                        .find_available_substitute(
                            logical_service,
                            self.reservation_engine,
                            agent.agent_id
                        )
                    )

                    if substitute:

                        physical_service = (
                            substitute["resource"]
                        )

                        print(
                            f"[SUBSTITUTION CHECK] "
                            f"{agent.name} -> "
                            f"{logical_service}"
                        )

                        print(
                            f"[ALTERNATIVE FOUND] "
                            f"{physical_service}"
                        )

                        return (
                            self.allocate_physical_resource(
                                agent,
                                logical_service,
                                physical_service
                            )
                        )

                    self.mark_waiting(
                        agent
                    )

                    waiting_time = (
                        self.get_waiting_time(
                            agent
                        )
                    )

                    fairness_score = (
                        self.calculate_fairness_score(
                            agent,
                            waiting_time
                        )
                    )

                    print(
                        f"[WAITING - RESERVED] "
                        f"{agent.name} -> "
                        f"{logical_service} | "
                        f"Wait: "
                        f"{waiting_time:.1f}s | "
                        f"Fairness: "
                        f"{fairness_score:.2f}"
                    )

                    return False

        # ==================================
        # FAIRNESS ARBITRATION
        # ==================================

        waiting_candidates = (
            self.get_waiting_for_resource(
                logical_service
            )
        )

        if waiting_candidates:

            candidates = list(
                waiting_candidates
            )

            if agent not in candidates:

                candidates.append(
                    agent
                )

            best_agent = (
                self.select_best_candidate(
                    candidates
                )
            )

            if (
                best_agent.agent_id
                != agent.agent_id
            ):

                # Check fallback before waiting.

                substitute = (
                    self.registry
                    .find_available_substitute(
                        logical_service,
                        self.reservation_engine,
                        agent.agent_id
                    )
                )

                if substitute:

                    physical_service = (
                        substitute["resource"]
                    )

                    print(
                        f"[SUBSTITUTION CHECK] "
                        f"{agent.name} -> "
                        f"{logical_service}"
                    )

                    print(
                        f"[ALTERNATIVE FOUND] "
                        f"{physical_service}"
                    )

                    return (
                        self.allocate_physical_resource(
                            agent,
                            logical_service,
                            physical_service
                        )
                    )

                self.mark_waiting(
                    agent
                )

                waiting_time = (
                    self.get_waiting_time(
                        agent
                    )
                )

                fairness_score = (
                    self.calculate_fairness_score(
                        agent,
                        waiting_time
                    )
                )

                print(
                    f"[WAITING - FAIRNESS] "
                    f"{agent.name} -> "
                    f"{logical_service} | "
                    f"Wait: "
                    f"{waiting_time:.1f}s | "
                    f"Fairness: "
                    f"{fairness_score:.2f} | "
                    f"Selected: "
                    f"{best_agent.name}"
                )

                return False

        # ==================================
        # NORMAL ALLOCATION
        # ==================================

        if resource.available > 0:

            return (
                self.allocate_physical_resource(
                    agent,
                    logical_service,
                    logical_service
                )
            )

        # ==================================
        # RESOURCE UNAVAILABLE
        # ==================================

        substitute = (
            self.registry
            .find_available_substitute(
                logical_service,
                self.reservation_engine,
                agent.agent_id
            )
        )

        if substitute:

            physical_service = (
                substitute["resource"]
            )

            print(
                f"[SUBSTITUTION CHECK] "
                f"{agent.name} -> "
                f"{logical_service}"
            )

            print(
                f"[ALTERNATIVE FOUND] "
                f"{physical_service}"
            )

            return (
                self.allocate_physical_resource(
                    agent,
                    logical_service,
                    physical_service
                )
            )

        # ==================================
        # WAIT
        # ==================================

        self.mark_waiting(
            agent
        )

        waiting_time = (
            self.get_waiting_time(
                agent
            )
        )

        fairness_score = (
            self.calculate_fairness_score(
                agent,
                waiting_time
            )
        )

        print(
            f"[WAITING] "
            f"{agent.name} -> "
            f"{logical_service} | "
            f"Wait: "
            f"{waiting_time:.1f}s | "
            f"Fairness: "
            f"{fairness_score:.2f}"
        )

        return False

    # ======================================
    # RELEASE RESOURCE
    # ======================================

    def release_resource(
        self,
        service,
        agent_id=None
    ):

        # Prefer actual physical allocation.
        actual_resource = None

        if agent_id is not None:

            actual_resource = (
                self.agent_allocations.get(
                    agent_id
                )
            )

        if actual_resource is None:

            actual_resource = service

        resource = self.registry.get(
            actual_resource
        )

        if resource is None:

            return

        resource.release()

        if agent_id is not None:

            self.remove_holder(
                actual_resource,
                agent_id
            )

            if agent_id in (
                self.agent_allocations
            ):

                del self.agent_allocations[
                    agent_id
                ]

        print(
            f"[RELEASED] "
            f"{actual_resource}"
        )

        # ----------------------------------
        # SHOW WHO SHOULD GET NEXT
        # ----------------------------------

        best_agent = (
            self.select_best_waiting_agent(
                service
            )
        )

        if best_agent:

            score = (
                self.calculate_scheduling_score(
                    best_agent
                )
            )

            print(
                f"[FAIRNESS ARBITRATION] "
                f"{service} -> "
                f"{best_agent.name} | "
                f"Score: {score:.2f}"
            )

    # ======================================
    # REMOVE HOLDER
    # ======================================

    def remove_from_waiting(
        self,
        agent
    ):

        if agent in self.waiting_agents:

            self.waiting_agents.remove(
                agent
            )

    # ======================================
    # SHOW SUBSTITUTION METRICS
    # ======================================

    def show_substitution_metrics(
        self
    ):

        print(
            "\n===== RESOURCE SUBSTITUTION METRICS =====\n"
        )

        print(
            f"Substitutions Used: "
            f"{self.substitutions}"
        )