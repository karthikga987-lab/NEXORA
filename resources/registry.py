class ResourceRegistry:

    def __init__(self):

        self.resources = {}

        # Explicit resource substitution policies.
        #
        # Format:
        #
        # {
        #     "DATABASE": [
        #         {
        #             "resource": "SEARCH",
        #             "penalty": 0.20,
        #             "reason": "Read-only retrieval fallback"
        #         }
        #     ]
        # }
        #
        self.substitution_rules = {}

    # ======================================
    # ADD RESOURCE
    # ======================================

    def add_resource(
        self,
        resource
    ):

        self.resources[
            resource.name
        ] = resource

    # ======================================
    # GET RESOURCE
    # ======================================

    def get(
        self,
        name
    ):

        return self.resources.get(
            name
        )

    # ======================================
    # ADD SUBSTITUTION RULE
    # ======================================

    def add_substitution(
        self,
        source,
        alternative,
        penalty=0.20,
        reason="Compatible fallback"
    ):

        if source not in (
            self.substitution_rules
        ):

            self.substitution_rules[
                source
            ] = []

        self.substitution_rules[
            source
        ].append(
            {
                "resource": alternative,
                "penalty": penalty,
                "reason": reason
            }
        )

    # ======================================
    # GET SUBSTITUTES
    # ======================================

    def get_substitutes(
        self,
        source
    ):

        return list(
            self.substitution_rules.get(
                source,
                []
            )
        )

    # ======================================
    # FIND AVAILABLE SUBSTITUTE
    # ======================================

    def find_available_substitute(
        self,
        source,
        reservation_engine=None,
        agent_id=None
    ):

        alternatives = (
            self.get_substitutes(
                source
            )
        )

        candidates = []

        for alternative in alternatives:

            resource_name = (
                alternative["resource"]
            )

            resource = self.get(
                resource_name
            )

            if resource is None:

                continue

            if resource.available <= 0:

                continue

            # Respect future reservations.
            #
            # If this alternative is already
            # reserved for somebody else,
            # don't steal that capacity.

            if reservation_engine:

                reserved_for_others = (
                    reservation_engine
                    .reserved_for_others(
                        resource_name,
                        agent_id
                    )
                )

                effective_available = (
                    resource.available
                    -
                    reserved_for_others
                )

                if effective_available <= 0:

                    continue

            candidates.append(
                alternative
            )

        if not candidates:

            return None

        # Lowest substitution penalty wins.

        candidates.sort(
            key=lambda item:
            item["penalty"]
        )

        return candidates[0]

    # ======================================
    # SHOW SUBSTITUTION POLICIES
    # ======================================

    def show_substitution_rules(self):

        print(
            "\n===== RESOURCE SUBSTITUTION POLICIES =====\n"
        )

        if not self.substitution_rules:

            print(
                "No substitution policies configured."
            )

            return

        for source, rules in (
            self.substitution_rules.items()
        ):

            for rule in rules:

                print(
                    f"{source} -> "
                    f"{rule['resource']} | "
                    f"Penalty: "
                    f"{rule['penalty']:.2f} | "
                    f"{rule['reason']}"
                )

    # ======================================
    # SHOW STATUS
    # ======================================

    def show_status(self):

        for resource in (
            self.resources.values()
        ):

            print(resource)