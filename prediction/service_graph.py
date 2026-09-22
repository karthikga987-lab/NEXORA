from collections import defaultdict


class ServiceGraphForecaster:

    def __init__(
        self,
        registry,
        reservation_horizon=2
    ):

        self.registry = registry

        # Number of future workflow steps to
        # consider for pre-execution reservation.
        self.reservation_horizon = (
            reservation_horizon
        )

    # ======================================
    # BUILD SERVICE GRAPH
    # ======================================

    def build_graph(
        self,
        agents
    ):

        graph = defaultdict(
            lambda: defaultdict(int)
        )

        for agent in agents:

            workflow = agent.workflow

            for index in range(
                len(workflow) - 1
            ):

                current_service = (
                    workflow[index]
                )

                next_service = (
                    workflow[index + 1]
                )

                graph[
                    current_service
                ][
                    next_service
                ] += 1

        return graph

    # ======================================
    # GET FUTURE SERVICES
    # ======================================

    def get_future_services(
        self,
        agent
    ):

        current_step = (
            agent.current_step
        )

        start = current_step + 1

        end = min(
            start + self.reservation_horizon,
            len(agent.workflow)
        )

        return agent.workflow[
            start:end
        ]

    # ======================================
    # FORECAST AGENT DEMAND
    # ======================================

    def forecast_agent(
        self,
        agent
    ):

        future_services = (
            self.get_future_services(
                agent
            )
        )

        demand = defaultdict(int)

        for service in future_services:

            demand[service] += 1

        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "current_service":
                agent.current_service(),
            "future_services":
                future_services,
            "demand":
                dict(demand)
        }

    # ======================================
    # FORECAST ALL AGENTS
    # ======================================

    def forecast_all(
        self,
        agents
    ):

        forecasts = []

        for agent in agents:

            forecasts.append(
                self.forecast_agent(
                    agent
                )
            )

        return forecasts

    # ======================================
    # AGGREGATE RESOURCE DEMAND
    # ======================================

    def aggregate_demand(
        self,
        agents
    ):

        total_demand = defaultdict(int)

        for agent in agents:

            future_services = (
                self.get_future_services(
                    agent
                )
            )

            for service in future_services:

                total_demand[
                    service
                ] += 1

        return dict(
            total_demand
        )

    # ======================================
    # CAPACITY PRESSURE
    # ======================================

    def calculate_pressure(
        self,
        resource_name,
        demand
    ):

        resource = self.registry.get(
            resource_name
        )

        if resource is None:

            return 0.0

        if resource.capacity <= 0:

            return 1.0

        return (
            demand
            /
            resource.capacity
        )

    # ======================================
    # SHOW SERVICE GRAPH
    # ======================================

    def show_graph(
        self,
        agents
    ):

        graph = self.build_graph(
            agents
        )

        print()

        print(
            "==================================="
        )

        print(
            "       SERVICE DEPENDENCY GRAPH"
        )

        print(
            "==================================="
        )

        for current_service in graph:

            for next_service in graph[
                current_service
            ]:

                count = graph[
                    current_service
                ][
                    next_service
                ]

                print(
                    f"{current_service} "
                    f"-> "
                    f"{next_service}"
                    f" | Observed Workflow Links: "
                    f"{count}"
                )

    # ======================================
    # SHOW FUTURE FORECAST
    # ======================================

    def show_forecast(
        self,
        agents
    ):

        forecasts = (
            self.forecast_all(
                agents
            )
        )

        print()

        print(
            "==================================="
        )

        print(
            "       PRE-EXECUTION FORECAST"
        )

        print(
            "==================================="
        )

        for forecast in forecasts:

            print()

            print(
                f"{forecast['agent_name']}"
            )

            print(
                f"  Current: "
                f"{forecast['current_service']}"
            )

            print(
                f"  Future:  "
                f"{' -> '.join(forecast['future_services'])}"
            )

            if forecast["demand"]:

                for service, count in (
                    forecast["demand"].items()
                ):

                    resource = self.registry.get(
                        service
                    )

                    if resource:

                        pressure = (
                            self.calculate_pressure(
                                service,
                                count
                            )
                        )

                        print(
                            f"    {service}: "
                            f"{count} future use(s) "
                            f"| Capacity: "
                            f"{resource.capacity} "
                            f"| Pressure: "
                            f"{pressure:.2f}"
                        )

    # ======================================
    # SHOW GLOBAL DEMAND
    # ======================================

    def show_global_demand(
        self,
        agents
    ):

        demand = (
            self.aggregate_demand(
                agents
            )
        )

        print()

        print(
            "==================================="
        )

        print(
            "       FUTURE RESOURCE DEMAND"
        )

        print(
            "==================================="
        )

        for resource_name, count in (
            demand.items()
        ):

            resource = self.registry.get(
                resource_name
            )

            if resource is None:

                continue

            pressure = (
                self.calculate_pressure(
                    resource_name,
                    count
                )
            )

            print(
                f"{resource_name}: "
                f"{count} future request(s) "
                f"/ Capacity {resource.capacity} "
                f"| Pressure: {pressure:.2f}"
            )

    # ======================================
    # GET RESERVATION PLAN
    # ======================================

    def get_reservation_plan(
        self,
        agents
    ):

        plan = []

        for agent in agents:

            future_services = (
                self.get_future_services(
                    agent
                )
            )

            # Avoid reserving the same resource
            # multiple times for the same agent
            # within the short forecast horizon.

            seen = set()

            for service in future_services:

                if service in seen:

                    continue

                seen.add(service)

                plan.append(
                    {
                        "agent": agent,
                        "resource": service,
                        "confidence": 1.0
                    }
                )

        return plan

    # ======================================
    # SHOW RESERVATION PLAN
    # ======================================

    def show_reservation_plan(
        self,
        agents
    ):

        plan = (
            self.get_reservation_plan(
                agents
            )
        )

        print()

        print(
            "==================================="
        )

        print(
            "       PRE-EXECUTION RESERVATION PLAN"
        )

        print(
            "==================================="
        )

        if not plan:

            print(
                "No future reservations required."
            )

            return

        for item in plan:

            agent = item["agent"]

            resource = item["resource"]

            print(
                f"{agent.name} -> "
                f"{resource} | "
                f"Forecast Confidence: 100.0%"
            )