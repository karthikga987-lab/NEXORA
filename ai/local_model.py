import json
import re
import urllib.request
import urllib.error


class LocalAI:

    def __init__(
        self,
        model="llama3.2:3b",
        host="http://localhost:11434"
    ):

        self.model = model
        self.host = host.rstrip("/")

    def generate(
        self,
        prompt,
        temperature=0.1
    ):

        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        data = json.dumps(
            payload
        ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type":
                    "application/json"
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=120
            ) as response:

                response_data = (
                    response.read()
                    .decode("utf-8")
                )

            result = json.loads(
                response_data
            )

            return result.get(
                "response",
                ""
            )

        except urllib.error.URLError as error:

            raise RuntimeError(
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
                f"\nDetails: {error}"
            )

    def choose_action(
        self,
        task,
        context,
        available_tools
    ):

        tools_text = "\n".join(
            f"- {tool}"
            for tool in available_tools
        )

        prompt = f"""
You are the planning brain of NEXORA.

USER TASK:
{task}

AVAILABLE TOOLS:
{tools_text}

RUNTIME STATE:
{context}

FOLLOW THESE RULES EXACTLY:

1. Complete every explicit operation
   requested by the user.

2. If a required tool is listed as missing,
   select that tool.

3. SEARCH is for research, current
   information, web information, and
   external information.

4. PYTHON is for calculations and arithmetic.

5. DATABASE is for stored NEXORA system
   information.

6. Never select a tool that is already listed
   as completed unless absolutely necessary.

7. If "Remaining required tools" is "none",
   select FINISH.

8. FINISH is allowed only when all required
   operations are complete.

9. When selecting SEARCH, the "query" must
   be a SHORT, SPECIFIC WEB SEARCH QUERY.

10. SEARCH queries must contain the important
    subject nouns from the task.

11. Do NOT use vague filler words such as:
    "current", "latest", "information",
    "please", "find", "look for".

12. Do NOT turn the entire user task into
    the search query.

13. Good SEARCH queries:

    "AI agent orchestration patterns"

    "NEXORA multi-agent orchestration"

    "runtime resource reservation multi-agent systems"

14. Bad SEARCH queries:

    "Current AI agent orchestration patterns"

    "Find current information about AI agents"

    "Research current AI agent orchestration
     patterns and find information relevant
     to NEXORA"

15. For PYTHON, the query must contain the
    actual mathematical expression.

16. For DATABASE, the query should describe
    the information that needs to be retrieved.

17. Return ONLY one JSON object.

18. Do not include markdown.

19. Do not explain outside the JSON.

EXAMPLE SEARCH:

{{"tool":"SEARCH","query":"AI agent orchestration patterns","reason":"Research the requested orchestration patterns."}}

EXAMPLE PYTHON:

{{"tool":"PYTHON","query":"125 * 32","reason":"Calculate the requested expression."}}

EXAMPLE DATABASE:

{{"tool":"DATABASE","query":"NEXORA system information","reason":"Retrieve NEXORA system information."}}

EXAMPLE FINISH:

{{"tool":"FINISH","query":"","reason":"All required operations are complete."}}

The tool value must be exactly one of:
{", ".join(available_tools)}
"""

        response = self.generate(
            prompt
        )

        return self._parse_action(
            response,
            available_tools
        )

    def _parse_action(
        self,
        response,
        available_tools
    ):

        cleaned = response.strip()

        cleaned = re.sub(
            r"```(?:json)?",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = cleaned.replace(
            "```",
            ""
        ).strip()

        try:

            result = json.loads(
                cleaned
            )

            return self._validate_action(
                result,
                available_tools
            )

        except Exception:
            pass

        matches = re.findall(
            r"\{.*?\}",
            cleaned,
            flags=re.DOTALL
        )

        for candidate in matches:

            try:

                result = json.loads(
                    candidate
                )

                return self._validate_action(
                    result,
                    available_tools
                )

            except Exception:
                continue

        upper_response = response.upper()

        if re.search(
            r"\bFINISH\b",
            upper_response
        ):

            return {
                "tool":
                    "FINISH",
                "query":
                    "",
                "reason":
                    "Recovered FINISH from local AI response."
            }

        for tool in [
            "SEARCH",
            "DATABASE",
            "PYTHON"
        ]:

            if tool not in available_tools:
                continue

            if re.search(
                rf"\b{tool}\b",
                upper_response
            ):

                return {
                    "tool":
                        tool,
                    "query":
                        "",
                    "reason":
                        "Recovered from local AI response."
                }

        raise RuntimeError(
            "Local AI returned an "
            "unrecognized action."
            "\nResponse:\n"
            f"{response}"
        )

    def _validate_action(
        self,
        result,
        available_tools
    ):

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "AI response is not a JSON object."
            )

        tool = str(
            result.get(
                "tool",
                ""
            )
        ).upper().strip()

        query = str(
            result.get(
                "query",
                ""
            )
        ).strip()

        reason = str(
            result.get(
                "reason",
                ""
            )
        ).strip()

        if tool not in available_tools:

            raise ValueError(
                f"Invalid tool: {tool}"
            )

        return {
            "tool":
                tool,
            "query":
                query,
            "reason":
                reason
        }

    def test_connection(self):

        response = self.generate(
            "Reply with exactly: "
            "NEXORA LOCAL AI ONLINE"
        )

        return response.strip()