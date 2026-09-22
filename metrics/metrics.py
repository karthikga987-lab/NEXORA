class RuntimeMetrics:

    def __init__(
        self,
        agents,
        history,
        scheduler,
        monitor,
        reservation_engine
    ):

        self.agents = agents

        self.history = history

        self.scheduler = scheduler

        self.monitor = monitor

        self.reservation_engine = (
            reservation_engine
        )

    # ======================================
    # AGENT METRICS
    # ======================================

    def completed_agents(self):

        return sum(
            1
            for agent in self.agents
            if agent.status == "COMPLETED"
        )

    def total_agents(self):

        return len(
            self.agents
        )

    # ======================================
    # STEP METRICS
    # ======================================

    def completed_steps(self):

        return (
            self.monitor.completed_steps
        )

    # ======================================
    # WAITING METRICS
    # ======================================

    def total_waiting_time(self):

        return (
            self.history
            .get_total_waiting_time()
        )

    def average_waiting_time(self):

        events = (
            self.history
            .get_events()
        )

        if not events:

            return 0.0

        return (
            self.total_waiting_time()
            /
            len(events)
        )

    # ======================================
    # EXECUTION METRICS
    # ======================================

    def total_execution_time(self):

        return (
            self.history
            .get_total_execution_time()
        )

    def average_execution_time(self):

        events = (
            self.history
            .get_events()
        )

        if not events:

            return 0.0

        return (
            self.total_execution_time()
            /
            len(events)
        )

    # ======================================
    # SUBSTITUTION
    # ======================================

    def substitutions(self):

        return (
            self.history
            .get_substitution_count()
        )

    # ======================================
    # DEADLOCK
    # ======================================

    def deadlocks(self):

        return (
            self.monitor.deadlocks_detected
        )

    def recoveries(self):

        return (
            self.monitor.recoveries
        )

    # ======================================
    # RESERVATION METRICS
    # ======================================

    def active_reservations(self):

        reservations = (
            self.reservation_engine
            .reservations
        )

        # Current ReservationEngine stores
        # reservations as a list.

        if isinstance(
            reservations,
            list
        ):

            return len(
                reservations
            )

        # Compatibility with a dictionary-based
        # reservation structure.

        if isinstance(
            reservations,
            dict
        ):

            return sum(
                len(items)
                for items
                in reservations.values()
            )

        return 0

    def waitlist_size(self):

        waitlist = (
            self.reservation_engine
            .waitlist
        )

        # Dictionary-based waitlist.

        if isinstance(
            waitlist,
            dict
        ):

            return sum(
                len(items)
                for items
                in waitlist.values()
            )

        # List-based waitlist.

        if isinstance(
            waitlist,
            list
        ):

            return len(
                waitlist
            )

        return 0

    # ======================================
    # RESOURCE UTILIZATION
    # ======================================

    def resource_status(self):

        result = {}

        for name, resource in (
            self.scheduler
            .registry
            .resources
            .items()
        ):

            used = (
                resource.capacity
                -
                resource.available
            )

            if resource.capacity > 0:

                utilization = (
                    used
                    /
                    resource.capacity
                )

            else:

                utilization = 0.0

            result[name] = {

                "capacity":
                    resource.capacity,

                "available":
                    resource.available,

                "used":
                    used,

                "utilization":
                    utilization
            }

        return result

    # ======================================
    # COMPLETE SNAPSHOT
    # ======================================

    def snapshot(self):

        return {

            "agents": {

                "total":
                    self.total_agents(),

                "completed":
                    self.completed_agents()
            },

            "steps":
                self.completed_steps(),

            "waiting_time":
                self.total_waiting_time(),

            "average_waiting":
                self.average_waiting_time(),

            "execution_time":
                self.total_execution_time(),

            "average_execution":
                self.average_execution_time(),

            "substitutions":
                self.substitutions(),

            "deadlocks":
                self.deadlocks(),

            "recoveries":
                self.recoveries(),

            "active_reservations":
                self.active_reservations(),

            "waitlist":
                self.waitlist_size(),

            "resources":
                self.resource_status()
        }