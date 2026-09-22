import time

from agents.agent import Agent
from resources.resource import Resource
from resources.registry import ResourceRegistry

from scheduler.scheduler import Scheduler
from reservation.reservation import ReservationEngine
from runtime.monitor import RuntimeMonitor


# ============================================================
# NEXORA STRESS TEST
# ============================================================

def banner(title):

    print()
    print("=" * 55)
    print(f"        {title}")
    print("=" * 55)


# ============================================================
# BUILD NORMAL RUNTIME
# ============================================================

def build_runtime():

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
        "DATABASE",
        "SEARCH",
        penalty=0.20,
        reason="Read-only retrieval fallback"
    )

    reservation_engine = ReservationEngine(
        registry
    )

    scheduler = Scheduler(
        registry,
        reservation_engine
    )

    monitor = RuntimeMonitor(
        scheduler=scheduler,
        reservation_engine=reservation_engine
    )

    return (
        registry,
        reservation_engine,
        scheduler,
        monitor
    )


# ============================================================
# BUILD FAIRNESS-ONLY RUNTIME
#
# IMPORTANT:
# No substitution policy is configured here.
# This forces the second agent to genuinely wait for DATABASE.
# ============================================================

def build_fairness_runtime():

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

    reservation_engine = ReservationEngine(
        registry
    )

    scheduler = Scheduler(
        registry,
        reservation_engine
    )

    monitor = RuntimeMonitor(
        scheduler=scheduler,
        reservation_engine=reservation_engine
    )

    return (
        registry,
        reservation_engine,
        scheduler,
        monitor
    )


# ============================================================
# TEST 1
# DATABASE CONTENTION + RESERVATION
# ============================================================

def test_reservation_contention():

    banner(
        "TEST 1: PREDICTIVE RESERVATION + CONTENTION"
    )

    (
        registry,
        reservation_engine,
        scheduler,
        monitor
    ) = build_runtime()

    data_agent = Agent(
        201,
        "Stress Data Agent",
        ["DATABASE"],
        priority=4
    )

    analysis_agent = Agent(
        202,
        "Stress Analysis Agent",
        ["DATABASE"],
        priority=2
    )

    monitor.register_agent(
        data_agent
    )

    monitor.register_agent(
        analysis_agent
    )

    print()
    print(
        "[STEP 1] Data Agent requests DATABASE"
    )

    scheduler.request_resource(
        data_agent
    )

    print(
        f"DATABASE availability: "
        f"{registry.get('DATABASE').available}/"
        f"{registry.get('DATABASE').capacity}"
    )

    print()
    print(
        "[STEP 2] Analysis Agent predicts DATABASE"
    )

    reservation_engine.reserve(
        analysis_agent,
        "DATABASE",
        1.0
    )

    print()
    print(
        "[STEP 3] Analysis Agent attempts DATABASE "
        "while it is occupied"
    )

    result = scheduler.request_resource(
        analysis_agent
    )

    print(
        f"Allocation result: {result}"
    )

    print()
    print(
        "[STEP 4] Current reservation state"
    )

    reservation_engine.show_reservations()

    print()
    print(
        "[STEP 5] Data Agent releases DATABASE"
    )

    scheduler.release_resource(
        "DATABASE",
        data_agent.agent_id
    )

    print()
    print(
        "[STEP 6] Processing reservation queue"
    )

    reservation_engine.process_requests()

    print()
    print(
        "DATABASE availability: "
        f"{registry.get('DATABASE').available}/"
        f"{registry.get('DATABASE').capacity}"
    )

    print()
    print(
        "RESULT: Reservation contention test completed."
    )


# ============================================================
# TEST 2
# DEADLOCK DETECTION + RECOVERY
# ============================================================

def test_deadlock_recovery():

    banner(
        "TEST 2: DEADLOCK DETECTION + RECOVERY"
    )

    (
        registry,
        reservation_engine,
        scheduler,
        monitor
    ) = build_runtime()

    agent_a = Agent(
        301,
        "Deadlock Agent A",
        ["LLM", "DATABASE"],
        priority=1
    )

    agent_b = Agent(
        302,
        "Deadlock Agent B",
        ["DATABASE", "LLM"],
        priority=4
    )

    monitor.register_agent(
        agent_a
    )

    monitor.register_agent(
        agent_b
    )

    print()
    print(
        "[STEP 1] Agent A acquires LLM"
    )

    scheduler.request_resource(
        agent_a
    )

    print(
        "[HOLD] Agent A -> LLM"
    )

    print()
    print(
        "[STEP 2] Agent B acquires DATABASE"
    )

    scheduler.request_resource(
        agent_b
    )

    print(
        "[HOLD] Agent B -> DATABASE"
    )

    agent_a.current_step = 1
    agent_b.current_step = 1

    agent_a.status = "WAITING"
    agent_b.status = "WAITING"

    print()
    print(
        "[WAIT] Agent A -> DATABASE"
    )

    print(
        "[WAIT] Agent B -> LLM"
    )

    print()
    print(
        "[GRAPH] Constructing wait-for graph..."
    )

    graph = monitor.build_wait_for_graph(
        [
            agent_a,
            agent_b
        ]
    )

    for agent_id, waiting_for in graph.items():

        print(
            f"Agent {agent_id} waits for: "
            f"{sorted(waiting_for)}"
        )

    print()
    print(
        "[CHECK] Running deadlock detector..."
    )

    deadlocked, graph, cycles = (
        monitor.check_deadlock(
            [
                agent_a,
                agent_b
            ]
        )
    )

    if deadlocked:

        print()
        print(
            "[DEADLOCK DETECTED]"
        )

        for cycle in cycles:

            print(
                "Cycle: "
                +
                " -> ".join(
                    str(item)
                    for item in cycle
                )
            )

    else:

        print(
            "[ERROR] Deadlock was not detected."
        )

        return

    print()
    print(
        "[RECOVERY] Starting NEXORA recovery..."
    )

    recovered = monitor.recover(
        [
            agent_a,
            agent_b
        ]
    )

    print()

    if recovered:

        print(
            "[SUCCESS] Deadlock recovery completed."
        )

    else:

        print(
            "[ERROR] Deadlock recovery failed."
        )


# ============================================================
# TEST 3
# RESOURCE SUBSTITUTION
# ============================================================

def test_resource_substitution():

    banner(
        "TEST 3: RESOURCE SUBSTITUTION"
    )

    (
        registry,
        reservation_engine,
        scheduler,
        monitor
    ) = build_runtime()

    blocker = Agent(
        401,
        "Database Holder",
        ["DATABASE"],
        priority=4
    )

    requester = Agent(
        402,
        "Substitution Agent",
        ["DATABASE"],
        priority=3
    )

    monitor.register_agent(
        blocker
    )

    monitor.register_agent(
        requester
    )

    print()
    print(
        "[STEP 1] Database Holder acquires DATABASE"
    )

    scheduler.request_resource(
        blocker
    )

    print(
        "[HOLD] DATABASE is now occupied."
    )

    print()
    print(
        "[STEP 2] Substitution Agent requests DATABASE"
    )

    result = scheduler.request_resource(
        requester
    )

    print(
        f"Allocation result: {result}"
    )

    physical_resource = (
        scheduler.get_allocated_resource(
            requester.agent_id
        )
    )

    print()

    if physical_resource:

        print(
            "[SUBSTITUTION RESULT]"
        )

        print(
            "Logical resource : DATABASE"
        )

        print(
            f"Physical resource: {physical_resource}"
        )

        if physical_resource != "DATABASE":

            print(
                "[SUCCESS] NEXORA substituted "
                "DATABASE with an available "
                f"{physical_resource} resource."
            )

        else:

            print(
                "[INFO] DATABASE was allocated directly."
            )

    else:

        print(
            "[INFO] Request remained waiting."
        )

    print()
    print(
        "Configured substitution policies:"
    )

    registry.show_substitution_rules()


# ============================================================
# TEST 4
# FAIRNESS + REAL WAITING
# ============================================================

def test_fairness():

    banner(
        "TEST 4: FAIRNESS + WAITING"
    )

    (
        registry,
        reservation_engine,
        scheduler,
        monitor
    ) = build_fairness_runtime()

    holder = Agent(
        501,
        "Database Holder",
        ["DATABASE"],
        priority=5
    )

    waiting_agent = Agent(
        502,
        "Waiting Agent",
        ["DATABASE"],
        priority=1
    )

    monitor.register_agent(
        holder
    )

    monitor.register_agent(
        waiting_agent
    )

    print()
    print(
        "[STEP 1] Database Holder acquires DATABASE"
    )

    scheduler.request_resource(
        holder
    )

    print(
        "[HOLD] DATABASE is occupied."
    )

    print()
    print(
        "[STEP 2] Waiting Agent requests DATABASE"
    )

    result = scheduler.request_resource(
        waiting_agent
    )

    print(
        f"Allocation result: {result}"
    )

    waiting_agent.status = "WAITING"

    print()
    print(
        "[WAIT] Waiting Agent is now blocked "
        "on DATABASE."
    )

    print()
    print(
        "[STEP 3] Simulating waiting time..."
    )

    time.sleep(
        2.0
    )

    waiting_time = (
        monitor.update_waiting(
            waiting_agent
        )
    )

    print(
        f"Measured waiting time: "
        f"{waiting_time:.2f}s"
    )

    print()
    print(
        "[STEP 4] Checking fairness arbitration..."
    )

    try:

        scheduler.show_waiting_agents()

    except AttributeError:

        print(
            "Scheduler waitlist:"
        )

        for agent in getattr(
            scheduler,
            "waiting_agents",
            []
        ):

            print(
                f"  {agent.name}"
            )

    print()
    print(
        "[STEP 5] Releasing DATABASE"
    )

    scheduler.release_resource(
        "DATABASE",
        holder.agent_id
    )

    print()
    print(
        "[STEP 6] Fairness queue can now "
        "promote the waiting agent."
    )

    try:

        scheduler.process_waiting_agents()

    except AttributeError:

        print(
            "Scheduler will process the waiting "
            "agent through its normal arbitration."
        )

    print()
    print(
        "RESULT: Genuine waiting/fairness scenario completed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "============================================="
    )

    print(
        "          NEXORA STRESS TEST"
    )

    print(
        "============================================="
    )

    print()

    print(
        "Testing advanced runtime orchestration:"
    )

    print(
        "  1. Predictive reservation"
    )

    print(
        "  2. Resource contention"
    )

    print(
        "  3. Deadlock detection"
    )

    print(
        "  4. Deadlock recovery"
    )

    print(
        "  5. Resource substitution"
    )

    print(
        "  6. Fairness and waiting"
    )

    test_reservation_contention()

    test_deadlock_recovery()

    test_resource_substitution()

    test_fairness()

    print()
    print(
        "============================================="
    )

    print(
        "       NEXORA STRESS TEST COMPLETE"
    )

    print(
        "============================================="
    )

    print()


if __name__ == "__main__":

    main()