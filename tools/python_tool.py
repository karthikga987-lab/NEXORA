import ast
import operator
from datetime import datetime


class PythonTool:

    name = "PYTHON"

    OPERATORS = {

        ast.Add:
            operator.add,

        ast.Sub:
            operator.sub,

        ast.Mult:
            operator.mul,

        ast.Div:
            operator.truediv,

        ast.Mod:
            operator.mod,

        ast.Pow:
            operator.pow
    }

    def run(
        self,
        expression
    ):

        try:

            tree = ast.parse(
                expression,
                mode="eval"
            )

            result = self._evaluate(
                tree.body
            )

            return {

                "tool":
                    self.name,

                "expression":
                    expression,

                "result":
                    result,

                "timestamp":
                    datetime.now().isoformat()
            }

        except Exception as error:

            return {

                "tool":
                    self.name,

                "expression":
                    expression,

                "result":
                    None,

                "error":
                    str(error),

                "timestamp":
                    datetime.now().isoformat()
            }

    def _evaluate(
        self,
        node
    ):

        if isinstance(
            node,
            ast.Constant
        ):

            if isinstance(
                node.value,
                (int, float)
            ):

                return node.value

            raise ValueError(
                "Only numeric values "
                "are allowed."
            )

        if isinstance(
            node,
            ast.BinOp
        ):

            left = self._evaluate(
                node.left
            )

            right = self._evaluate(
                node.right
            )

            operation = self.OPERATORS.get(
                type(node.op)
            )

            if operation is None:

                raise ValueError(
                    "Unsupported operation."
                )

            return operation(
                left,
                right
            )

        if isinstance(
            node,
            ast.UnaryOp
        ):

            value = self._evaluate(
                node.operand
            )

            if isinstance(
                node.op,
                ast.USub
            ):

                return -value

            if isinstance(
                node.op,
                ast.UAdd
            ):

                return value

            raise ValueError(
                "Unsupported unary operation."
            )

        raise ValueError(
            "Only simple arithmetic "
            "expressions are allowed."
        )