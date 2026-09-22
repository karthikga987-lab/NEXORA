class Reservation:

    def __init__(
        self,
        agent_id,
        agent_name,
        resource,
        confidence,
        score
    ):

        self.agent_id = agent_id
        self.agent_name = agent_name
        self.resource = resource
        self.confidence = confidence
        self.score = score

    def __str__(self):

        return (
            f"{self.agent_name} -> "
            f"{self.resource} | "
            f"Confidence: "
            f"{self.confidence * 100:.1f}% | "
            f"Score: {self.score:.2f}"
        )


class ReservationEngine:

    def __init__(
        self,
        registry,
        aging_factor=0.10
    ):

        self.registry = registry

        # Confirmed future reservations.
        self.reservations = []

        # Temporary reservation requests.
        self.requests = []

        # Requests that could not immediately
        # obtain a future slot.
        self.waitlist = []

        self.aging_factor = aging_factor

    # ======================================
    # RESERVATION COUNTS
    # ======================================

    def reserved_count(
        self,
        resource_name
    ):

        return sum(
            1
            for reservation
            in self.reservations
            if reservation.resource
            == resource_name
        )

    def reserved_for_others(
        self,
        resource_name,
        agent_id
    ):

        return sum(
            1
            for reservation
            in self.reservations
            if (
                reservation.resource
                == resource_name
                and
                reservation.agent_id
                != agent_id
            )
        )

    def available_for_reservation(
        self,
        resource_name
    ):

        resource = self.registry.get(
            resource_name
        )

        if resource is None:

            return 0

        return (
            resource.capacity
            -
            self.reserved_count(
                resource_name
            )
        )

    # ======================================
    # SCORING
    # ======================================

    def calculate_score(
        self,
        agent,
        confidence
    ):

        priority_score = min(
            agent.priority / 5.0,
            1.0
        )

        waiting_score = 0.0

        score = (
            (0.50 * confidence)
            +
            (0.30 * priority_score)
            +
            (0.20 * waiting_score)
        )

        return score

    def calculate_waitlist_score(
        self,
        request
    ):

        agent = request["agent"]

        confidence = request[
            "confidence"
        ]

        priority_score = min(
            agent.priority / 5.0,
            1.0
        )

        wait_cycles = request.get(
            "wait_cycles",
            0
        )

        aging_score = min(
            wait_cycles
            * self.aging_factor,
            1.0
        )

        score = (
            (0.45 * confidence)
            +
            (0.30 * priority_score)
            +
            (0.25 * aging_score)
        )

        return score

    # ======================================
    # CHECK DUPLICATES
    # ======================================

    def has_reservation(
        self,
        agent_id,
        resource_name
    ):

        return (
            self.get_reservation(
                agent_id,
                resource_name
            )
            is not None
        )

    def is_waitlisted(
        self,
        agent_id,
        resource_name
    ):

        for request in self.waitlist:

            agent = request["agent"]

            if (
                agent.agent_id
                == agent_id
                and
                request["resource"]
                == resource_name
            ):

                return True

        return False

    # ======================================
    # REQUEST RESERVATION
    # ======================================

    def request_reservation(
        self,
        agent,
        resource_name,
        confidence
    ):

        resource = self.registry.get(
            resource_name
        )

        if resource is None:

            print(
                f"[RESERVATION FAILED] "
                f"Resource "
                f"'{resource_name}' "
                f"not found."
            )

            return False

        if self.has_reservation(
            agent.agent_id,
            resource_name
        ):

            return False

        if self.is_waitlisted(
            agent.agent_id,
            resource_name
        ):

            return False

        score = self.calculate_score(
            agent,
            confidence
        )

        request = {
            "agent": agent,
            "resource": resource_name,
            "confidence": confidence,
            "score": score,
            "wait_cycles": 0
        }

        self.requests.append(
            request
        )

        print(
            f"[RESERVATION REQUEST] "
            f"{agent.name} -> "
            f"{resource_name} | "
            f"Confidence: "
            f"{confidence * 100:.1f}% | "
            f"Score: {score:.2f}"
        )

        return True

    # ======================================
    # PROCESS NEW REQUESTS
    # ======================================

    def process_requests(self):

        if not self.requests:

            return

        self.requests.sort(
            key=lambda request:
            request["score"],
            reverse=True
        )

        for request in self.requests:

            agent = request["agent"]

            resource_name = (
                request["resource"]
            )

            confidence = (
                request["confidence"]
            )

            score = request["score"]

            if self.has_reservation(
                agent.agent_id,
                resource_name
            ):

                continue

            if self.is_waitlisted(
                agent.agent_id,
                resource_name
            ):

                continue

            available = (
                self.available_for_reservation(
                    resource_name
                )
            )

            if available <= 0:

                self.add_to_waitlist(
                    request
                )

                continue

            self.create_reservation(
                agent,
                resource_name,
                confidence,
                score
            )

        self.requests.clear()

    # ======================================
    # CREATE RESERVATION
    # ======================================

    def create_reservation(
        self,
        agent,
        resource_name,
        confidence,
        score
    ):

        reservation = Reservation(
            agent.agent_id,
            agent.name,
            resource_name,
            confidence,
            score
        )

        self.reservations.append(
            reservation
        )

        print(
            f"[RESERVED] "
            f"{agent.name} -> "
            f"{resource_name} | "
            f"Score: {score:.2f}"
        )

        return reservation

    # ======================================
    # ADD TO WAITLIST
    # ======================================

    def add_to_waitlist(
        self,
        request
    ):

        request["wait_cycles"] = (
            request.get(
                "wait_cycles",
                0
            )
            + 1
        )

        request["score"] = (
            self.calculate_waitlist_score(
                request
            )
        )

        self.waitlist.append(
            request
        )

        self.sort_waitlist()

        position = self.get_waitlist_position(
            request
        )

        print(
            f"[RESERVATION QUEUED] "
            f"{request['agent'].name} -> "
            f"{request['resource']} | "
            f"Position: {position} | "
            f"Score: "
            f"{request['score']:.2f}"
        )

    # ======================================
    # SORT WAITLIST
    # ======================================

    def sort_waitlist(self):

        self.waitlist.sort(
            key=lambda request:
            request["score"],
            reverse=True
        )

    # ======================================
    # WAITLIST POSITION
    # ======================================

    def get_waitlist_position(
        self,
        request
    ):

        self.sort_waitlist()

        for index, item in enumerate(
            self.waitlist,
            start=1
        ):

            if item is request:

                return index

        return len(
            self.waitlist
        )

    # ======================================
    # PROCESS WAITLIST
    # ======================================

    def process_waitlist(
        self,
        resource_name=None
    ):

        if not self.waitlist:

            return

        # Increase aging for waiting requests.

        for request in self.waitlist:

            if (
                resource_name is not None
                and
                request["resource"]
                != resource_name
            ):

                continue

            request["wait_cycles"] = (
                request.get(
                    "wait_cycles",
                    0
                )
                + 1
            )

            request["score"] = (
                self.calculate_waitlist_score(
                    request
                )
            )

        self.sort_waitlist()

        promoted = []

        for request in list(
            self.waitlist
        ):

            resource = request[
                "resource"
            ]

            if (
                resource_name is not None
                and
                resource
                != resource_name
            ):

                continue

            if self.has_reservation(
                request["agent"].agent_id,
                resource
            ):

                promoted.append(
                    request
                )

                continue

            available = (
                self.available_for_reservation(
                    resource
                )
            )

            if available <= 0:

                continue

            agent = request["agent"]

            reservation = (
                self.create_reservation(
                    agent,
                    resource,
                    request["confidence"],
                    request["score"]
                )
            )

            print(
                f"[RESERVATION PROMOTED] "
                f"{agent.name} -> "
                f"{resource} | "
                f"Score: "
                f"{request['score']:.2f}"
            )

            promoted.append(
                request
            )

        for request in promoted:

            if request in self.waitlist:

                self.waitlist.remove(
                    request
                )

    # ======================================
    # RESERVE
    # ======================================

    def reserve(
        self,
        agent,
        resource_name,
        confidence
    ):

        requested = (
            self.request_reservation(
                agent,
                resource_name,
                confidence
            )
        )

        if requested:

            self.process_requests()

    # ======================================
    # GET RESERVATION
    # ======================================

    def get_reservation(
        self,
        agent_id,
        resource_name=None
    ):

        for reservation in (
            self.reservations
        ):

            if (
                reservation.agent_id
                != agent_id
            ):

                continue

            if (
                resource_name is not None
                and
                reservation.resource
                != resource_name
            ):

                continue

            return reservation

        return None

    # ======================================
    # GET AGENT RESERVATIONS
    # ======================================

    def get_agent_reservations(
        self,
        agent_id
    ):

        return [
            reservation
            for reservation
            in self.reservations
            if reservation.agent_id
            == agent_id
        ]

    # ======================================
    # GET RESERVATION OWNERS
    # ======================================

    def get_reservation_owner(
        self,
        resource_name,
        exclude_agent_id=None
    ):

        owners = []

        for reservation in (
            self.reservations
        ):

            if (
                reservation.resource
                == resource_name
                and
                reservation.agent_id
                != exclude_agent_id
            ):

                owners.append(
                    reservation.agent_id
                )

        return owners

    # ======================================
    # CONSUME RESERVATION
    # ======================================

    def consume_reservation(
        self,
        agent_id,
        resource_name
    ):

        for index, reservation in enumerate(
            self.reservations
        ):

            if (
                reservation.agent_id
                == agent_id
                and
                reservation.resource
                == resource_name
            ):

                self.reservations.pop(
                    index
                )

                print(
                    f"[RESERVATION CONSUMED] "
                    f"{reservation.agent_name} "
                    f"-> "
                    f"{resource_name}"
                )

                # The consumed reservation
                # has freed a future slot.
                #
                # Promote the next waiting
                # request immediately.

                self.process_waitlist(
                    resource_name
                )

                return True

        return False

    # ======================================
    # CANCEL RESERVATION
    # ======================================

    def cancel_reservation(
        self,
        agent_id
    ):

        removed = []

        remaining = []

        for reservation in (
            self.reservations
        ):

            if (
                reservation.agent_id
                == agent_id
            ):

                removed.append(
                    reservation
                )

            else:

                remaining.append(
                    reservation
                )

        self.reservations = remaining

        for reservation in removed:

            print(
                f"[DEADLOCK RECOVERY] "
                f"Cancelled reservation: "
                f"{reservation.agent_name} "
                f"-> "
                f"{reservation.resource}"
            )

            self.process_waitlist(
                reservation.resource
            )

        return bool(
            removed
        )

    # ======================================
    # RELEASE RESERVATIONS
    # ======================================

    def release_reservation(
        self,
        agent_id
    ):

        removed = []

        remaining = []

        for reservation in (
            self.reservations
        ):

            if (
                reservation.agent_id
                == agent_id
            ):

                removed.append(
                    reservation
                )

            else:

                remaining.append(
                    reservation
                )

        self.reservations = remaining

        for reservation in removed:

            print(
                f"[RESERVATION RELEASED] "
                f"{reservation.agent_name} "
                f"-> "
                f"{reservation.resource}"
            )

            self.process_waitlist(
                reservation.resource
            )

    # ======================================
    # CLEANUP AGENT
    # ======================================

    def cleanup_agent(
        self,
        agent
    ):

        if agent.status == "COMPLETED":

            self.release_reservation(
                agent.agent_id
            )

    # ======================================
    # SHOW ACTIVE RESERVATIONS
    # ======================================

    def show_reservations(self):

        print(
            "\n===== ACTIVE RESERVATIONS =====\n"
        )

        if not self.reservations:

            print(
                "No active reservations."
            )

        else:

            for reservation in (
                self.reservations
            ):

                print(
                    reservation
                )

            print(
                "\n===== RESERVATION CAPACITY =====\n"
            )

            resources = set(
                reservation.resource
                for reservation
                in self.reservations
            )

            for resource_name in resources:

                resource = self.registry.get(
                    resource_name
                )

                reserved = (
                    self.reserved_count(
                        resource_name
                    )
                )

                print(
                    f"{resource_name}: "
                    f"{reserved}/"
                    f"{resource.capacity} "
                    f"future slots reserved"
                )

        self.show_waitlist()

    # ======================================
    # SHOW WAITLIST
    # ======================================

    def show_waitlist(self):

        print(
            "\n===== RESERVATION WAITLIST =====\n"
        )

        if not self.waitlist:

            print(
                "No pending reservation requests."
            )

            return

        self.sort_waitlist()

        for position, request in enumerate(
            self.waitlist,
            start=1
        ):

            agent = request["agent"]

            print(
                f"{position}. "
                f"{agent.name} -> "
                f"{request['resource']} | "
                f"Confidence: "
                f"{request['confidence'] * 100:.1f}% | "
                f"Score: "
                f"{request['score']:.2f} | "
                f"Wait Cycles: "
                f"{request['wait_cycles']}"
            )