import asyncio

from resources.resource import Resource
from resources.registry import ResourceRegistry

from scheduler.scheduler import Scheduler

from prediction.history import RuntimeHistory
from prediction.predictor import PredictionEngine

from reservation.reservation import ReservationEngine

from runtime.monitor import RuntimeMonitor
from runtime.interceptor import RuntimeInterceptor

from ai.local_model import LocalAI

from agents.live_agent import LiveAgent

from tools.search_tool import SearchTool
from tools.database_tool import DatabaseTool
from tools.python_tool import PythonTool


def create_live_system():

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

    registry.add_substitution(
        source="DATABASE",
        alternative="SEARCH",
        penalty=0.20,
        reason="Read-only retrieval fallback"
    )

    history = RuntimeHistory()

    predictor = PredictionEngine(
        history
    )

    reservation_engine = (
        ReservationEngine(
            registry
        )
    )

    scheduler = Scheduler(
        registry,
        reservation_engine
    )

    monitor = RuntimeMonitor(
        scheduler=scheduler,
        reservation_engine=reservation_engine
    )

    interceptor = RuntimeInterceptor(
        scheduler=scheduler,
        reservation_engine=reservation_engine,
        history=history,
        predictor=predictor
    )

    ai = LocalAI(
        model="llama3.2:3b"
    )

    tools = {
        "SEARCH": SearchTool(),
        "DATABASE": DatabaseTool(),
        "PYTHON": PythonTool()
    }

    return (
        registry,
        history,
        predictor,
        reservation_engine,
        scheduler,
        monitor,
        interceptor,
        ai,
        tools
    )


async def run_agent(live_agent):

    return await live_agent.execute()


async def main():

    (
        registry,
        history,
        predictor,
        reservation_engine,
        scheduler,
        monitor,
        interceptor,
        ai,
        tools
    ) = create_live_system()

    print()
    print("=========================================")
    print("          NEXORA MULTI-AGENT LIVE")
    print("=========================================")
    print()
    print("Predictive Runtime Orchestration")
    print("Concurrent Local AI Agents")
    print()
    print("LOCAL MODEL")
    print("-----------")
    print("llama3.2:3b via Ollama")
    print()
    print("Testing local AI connection...")

    response = await asyncio.to_thread(
        ai.test_connection
    )

    print(
        f"AI Response: {response}"
    )

    print()
    print("INITIAL RESOURCES")
    print("------------------------")

    registry.show_status()

    print()
    print("=========================================")
    print("          LIVE AGENT WORKLOAD")
    print("=========================================")
    print()

    agent1 = LiveAgent(
        agent_id=101,
        name="Research Agent",
        task=(
            "Research current AI agent "
            "orchestration patterns and find "
            "information relevant to NEXORA."
        ),
        ai=ai,
        scheduler=scheduler,
        reservation_engine=reservation_engine,
        history=history,
        predictor=predictor,
        interceptor=interceptor,
        tools=tools,
        monitor=monitor,
        priority=3,
        max_steps=6
    )

    agent2 = LiveAgent(
        agent_id=102,
        name="Data Agent",
        task=(
            "Calculate 125 multiplied by 32 "
            "and retrieve the current NEXORA "
            "resource information from the "
            "database."
        ),
        ai=ai,
        scheduler=scheduler,
        reservation_engine=reservation_engine,
        history=history,
        predictor=predictor,
        interceptor=interceptor,
        tools=tools,
        monitor=monitor,
        priority=4,
        max_steps=6
    )

    agent3 = LiveAgent(
        agent_id=103,
        name="Analysis Agent",
        task=(
            "Research NEXORA and current "
            "multi-agent orchestration, "
            "retrieve NEXORA system information, "
            "then calculate 17 multiplied by 6."
        ),
        ai=ai,
        scheduler=scheduler,
        reservation_engine=reservation_engine,
        history=history,
        predictor=predictor,
        interceptor=interceptor,
        tools=tools,
        monitor=monitor,
        priority=2,
        max_steps=8
    )

    agents = [
        agent1,
        agent2,
        agent3
    ]

    for live_agent in agents:

        monitor.register_agent(
            live_agent.agent
        )

    print()

    for live_agent in agents:

        print(
            f"{live_agent.agent.name}"
        )

        print(
            f"  Priority: "
            f"{live_agent.agent.priority}"
        )

        print(
            f"  Required: "
            f"{', '.join(live_agent._required_tools())}"
        )

        print(
            f"  Task: "
            f"{live_agent.task}"
        )

        print()

    print("=========================================")
    print("       CONCURRENT EXECUTION START")
    print("=========================================")
    print()

    tasks = []

    for live_agent in agents:

        tasks.append(
            asyncio.create_task(
                run_agent(live_agent)
            )
        )

    monitor_task = asyncio.create_task(
        monitor_runtime(
            agents,
            monitor
        )
    )

    results = await asyncio.gather(
        *tasks,
        return_exceptions=True
    )

    monitor_task.cancel()

    print()
    print("=========================================")
    print("       CONCURRENT EXECUTION COMPLETE")
    print("=========================================")
    print()

    for index, result in enumerate(
        results,
        start=1
    ):

        if isinstance(
            result,
            Exception
        ):

            print(
                f"Agent {index}: ERROR"
            )

            print(result)

        else:

            print(
                f"Agent {index}: "
                f"{len(result)} tool operations"
            )

    print()

    history.show_history()

    # ============================================================
    # AGENT-AWARE LEARNING
    # ============================================================

    print()
    print("=========================================")
    print("       AGENT-AWARE SERVICE GRAPH")
    print("=========================================")

    predictor.show_agent_predictions(
        [
            live_agent.agent
            for live_agent in agents
        ]
    )

    print()
    print("=========================================")
    print("       GLOBAL SERVICE GRAPH")
    print("=========================================")

    for service in [
        "SEARCH",
        "DATABASE",
        "PYTHON"
    ]:

        predictor.show_prediction(
            service
        )

    print()

    reservation_engine.show_reservations()

    print()

    scheduler.show_substitution_metrics()

    monitor.print_metrics()

    print()
    print("=========================================")
    print("          FINAL RESOURCE STATUS")
    print("=========================================")

    registry.show_status()

    print()
    print("=========================================")
    print("             AGENT STATUS")
    print("=========================================")

    for live_agent in agents:

        print(
            f"{live_agent.agent.name} | "
            f"{live_agent.agent.status}"
        )

        print(
            f"  Tools: "
            f"{', '.join(item['tool'] for item in live_agent.tool_history)}"
        )

    print()
    print("=========================================")
    print("        NEXORA MULTI-AGENT COMPLETE")
    print("=========================================")


async def monitor_runtime(
    live_agents,
    monitor
):

    while True:

        await asyncio.sleep(
            0.5
        )

        all_completed = all(
            agent.agent.status == "COMPLETED"
            for agent in live_agents
        )

        if all_completed:

            break

        for live_agent in live_agents:

            monitor.update_waiting(
                live_agent.agent
            )

        monitor.recover(
            [
                live_agent.agent
                for live_agent in live_agents
            ]
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )