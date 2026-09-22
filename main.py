import asyncio

from resources.resource import Resource
from resources.registry import ResourceRegistry

from agents.agent import Agent

from scheduler.scheduler import Scheduler

from execution.executor import Executor

from prediction.history import RuntimeHistory
from prediction.predictor import PredictionEngine
from prediction.service_graph import ServiceGraphForecaster

from reservation.reservation import ReservationEngine

from runtime.monitor import RuntimeMonitor


def create_system():

    # ======================================
    # RESOURCE REGISTRY
    # ======================================

    registry = ResourceRegistry()

    registry.add_resource(
        Resource("LLM", 2)
    )

    registry.add_resource(
        Resource("SEARCH", 2)
    )

    registry.add_resource(
        Resource("DATABASE", 1)
    )

    registry.add_resource(
        Resource("PYTHON", 2)
    )

    # ======================================
    # RESOURCE SUBSTITUTION POLICIES
    # ======================================
    #
    # DATABASE can be substituted by SEARCH
    # for read-only retrieval operations.
    #
    # The penalty represents the cost/risk
    # of using an alternative resource.
    #
    # Lower penalty = better substitute.
    #

    registry.add_substitution(
        source="DATABASE",
        alternative="SEARCH",
        penalty=0.20,
        reason="Read-only retrieval fallback"
    )

    # ======================================
    # AGENTS
    # ======================================

    agent1 = Agent(
        1,
        "Research Agent",
        [
            "LLM",
            "SEARCH",
            "LLM",
            "DATABASE",
            "PYTHON"
        ],
        priority=2
    )

    agent2 = Agent(
        2,
        "Data Agent",
        [
            "LLM",
            "PYTHON",
            "DATABASE",
            "LLM"
        ],
        priority=4
    )

    agent3 = Agent(
        3,
        "Report Agent",
        [
            "SEARCH",
            "LLM",
            "DATABASE",
            "LLM"
        ],
        priority=3
    )

    agents = [
        agent1,
        agent2,
        agent3
    ]

    # ======================================
    # RUNTIME HISTORY
    # ======================================

    history = RuntimeHistory()

    # ======================================
    # PREDICTION ENGINE
    # ======================================

    predictor = PredictionEngine(
        history
    )

    # ======================================
    # RESERVATION ENGINE
    # ======================================

    reservation_engine = (
        ReservationEngine(
            registry
        )
    )

    # ======================================
    # SCHEDULER
    # ======================================

    scheduler = Scheduler(
        registry,
        reservation_engine
    )

    # ======================================
    # RUNTIME MONITOR
    # ======================================

    monitor = RuntimeMonitor(
        scheduler=scheduler,
        reservation_engine=reservation_engine
    )

    for agent in agents:

        monitor.register_agent(
            agent
        )

    # ======================================
    # EXECUTOR
    # ======================================

    executor = Executor(
        scheduler=scheduler,
        history=history,
        predictor=predictor,
        reservation_engine=reservation_engine
    )

    # ======================================
    # SERVICE GRAPH FORECASTER
    # ======================================

    service_graph = (
        ServiceGraphForecaster(
            registry,
            reservation_horizon=2
        )
    )

    return (
        registry,
        agents,
        scheduler,
        history,
        predictor,
        reservation_engine,
        executor,
        monitor,
        service_graph
    )


# ==========================================
# RUN ONE AGENT
# ==========================================

async def run_agent(
    agent,
    executor,
    monitor
):

    while (
        agent.status
        != "COMPLETED"
    ):

        previous_step = (
            agent.current_step
        )

        await executor.execute_agent_step(
            agent
        )

        current_step = (
            agent.current_step
        )

        if current_step > previous_step:

            monitor.progress(
                agent
            )


# ==========================================
# BACKGROUND RUNTIME MONITOR
# ==========================================

async def monitor_runtime(
    agents,
    monitor
):

    while True:

        await asyncio.sleep(
            0.5
        )

        all_completed = all(
            agent.status == "COMPLETED"
            for agent in agents
        )

        if all_completed:

            break

        monitor.recover(
            agents
        )


# ==========================================
# MAIN
# ==========================================

async def main():

    (
        registry,
        agents,
        scheduler,
        history,
        predictor,
        reservation_engine,
        executor,
        monitor,
        service_graph
    ) = create_system()

    # ======================================
    # TITLE
    # ======================================

    print()

    print(
        "==================================="
    )

    print(
        "      NEXORA CONCURRENT ENGINE"
    )

    print(
        "==================================="
    )

    print()

    print(
        "Predictive Runtime Orchestration"
    )

    print(
        "for Multi-Agent Systems"
    )

    print()

    # ======================================
    # INITIAL RESOURCE STATUS
    # ======================================

    print(
        "INITIAL RESOURCE STATUS"
    )

    print(
        "------------------------"
    )

    registry.show_status()

    print()

    # ======================================
    # SUBSTITUTION POLICIES
    # ======================================

    registry.show_substitution_rules()

    print()

    # ======================================
    # INITIAL AGENTS
    # ======================================

    print(
        "INITIAL AGENTS"
    )

    print(
        "------------------------"
    )

    for agent in agents:

        print(agent)

    # ======================================
    # SERVICE DEPENDENCY GRAPH
    # ======================================

    service_graph.show_graph(
        agents
    )

    # ======================================
    # PRE-EXECUTION FORECAST
    # ======================================

    service_graph.show_forecast(
        agents
    )

    # ======================================
    # GLOBAL FUTURE DEMAND
    # ======================================

    service_graph.show_global_demand(
        agents
    )

    # ======================================
    # RESERVATION PLAN
    # ======================================

    service_graph.show_reservation_plan(
        agents
    )

    # ======================================
    # PRE-EXECUTION RESERVATIONS
    # ======================================

    print()

    print(
        "==================================="
    )

    print(
        "      PRE-EXECUTION RESERVATION"
    )

    print(
        "==================================="
    )

    reservation_plan = (
        service_graph.get_reservation_plan(
            agents
        )
    )

    for item in reservation_plan:

        reservation_engine.reserve(
            item["agent"],
            item["resource"],
            item["confidence"]
        )

    print()

    reservation_engine.show_reservations()

    print()

    # ======================================
    # PREDICTIVE RUNTIME
    # ======================================

    print(
        "==================================="
    )

    print(
        "       PREDICTIVE RUNTIME"
    )

    print(
        "==================================="
    )

    print()

    print(
        "Prediction + Reservation + "
        "Fairness + Substitution + "
        "Deadlock Monitoring"
    )

    print()

    # ======================================
    # START AGENTS CONCURRENTLY
    # ======================================

    agent_tasks = []

    for agent in agents:

        task = asyncio.create_task(
            run_agent(
                agent,
                executor,
                monitor
            )
        )

        agent_tasks.append(
            task
        )

    # ======================================
    # START RUNTIME MONITOR
    # ======================================

    monitor_task = asyncio.create_task(
        monitor_runtime(
            agents,
            monitor
        )
    )

    # ======================================
    # WAIT FOR ALL AGENTS
    # ======================================

    await asyncio.gather(
        *agent_tasks
    )

    # ======================================
    # STOP MONITOR
    # ======================================

    monitor_task.cancel()

    # ======================================
    # RUNTIME HISTORY
    # ======================================

    history.show_history()

    # ======================================
    # LEARNED PREDICTIONS
    # ======================================

    print()

    print(
        "==================================="
    )

    print(
        "       LEARNED PREDICTIONS"
    )

    print(
        "==================================="
    )

    predictor.show_prediction(
        "LLM"
    )

    predictor.show_prediction(
        "SEARCH"
    )

    predictor.show_prediction(
        "DATABASE"
    )

    predictor.show_prediction(
        "PYTHON"
    )

    # ======================================
    # FINAL RESERVATIONS
    # ======================================

    reservation_engine.show_reservations()

    # ======================================
    # SUBSTITUTION METRICS
    # ======================================

    scheduler.show_substitution_metrics()

    # ======================================
    # RUNTIME METRICS
    # ======================================

    monitor.print_metrics()

    # ======================================
    # COMPLETION
    # ======================================

    print()

    print(
        "==================================="
    )

    print(
        "      ALL WORKFLOWS COMPLETED"
    )

    print(
        "==================================="
    )

    print()

    # ======================================
    # FINAL RESOURCE STATUS
    # ======================================

    print(
        "FINAL RESOURCE STATUS"
    )

    print(
        "------------------------"
    )

    registry.show_status()

    print()

    # ======================================
    # FINAL AGENT STATUS
    # ======================================

    print(
        "FINAL AGENT STATUS"
    )

    print(
        "------------------------"
    )

    for agent in agents:

        print(agent)

    print()


# ==========================================
# PROGRAM ENTRY POINT
# ==========================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )