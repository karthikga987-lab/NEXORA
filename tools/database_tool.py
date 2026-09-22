from datetime import datetime


class DatabaseTool:

    name = "DATABASE"

    def __init__(self):

        self.data = {

            "NEXORA":
                {
                    "project":
                        "Predictive Runtime "
                        "Orchestration",

                    "agents":
                        3,

                    "resources":
                        [
                            "LLM",
                            "SEARCH",
                            "DATABASE",
                            "PYTHON"
                        ]
                },

            "RESOURCES":
                {
                    "LLM":
                        2,

                    "SEARCH":
                        2,

                    "DATABASE":
                        1,

                    "PYTHON":
                        2
                }
        }

    def run(
        self,
        query
    ):

        query_upper = (
            query.upper()
        )

        if "RESOURCE" in query_upper:

            result = (
                self.data["RESOURCES"]
            )

        elif "NEXORA" in query_upper:

            result = (
                self.data["NEXORA"]
            )

        else:

            result = {
                "available_records":
                    list(
                        self.data.keys()
                    )
            }

        return {
            "tool":
                self.name,

            "query":
                query,

            "result":
                result,

            "timestamp":
                datetime.now().isoformat()
        }