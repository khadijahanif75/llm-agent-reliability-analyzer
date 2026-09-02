import ast
import operator
from tools.base import BaseTool, ToolResult
from tracing.events import ErrorType

class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Safely evaluates basic mathematical expressions (+, -, *, /, **, %)."
        )
        self._operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

    def _eval_node(self, node):
        if isinstance(node, ast.Num):  # Number
            return node.n
        elif isinstance(node, ast.Constant):  # Python 3.8+ Constant
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.BinOp):  # Binary operation (e.g., 5 * 10)
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type in self._operators:
                if op_type == ast.Div and right == 0:
                    raise ZeroDivisionError("Division by zero is not allowed.")
                return self._operators[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):  # Unary operation (e.g., -5)
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in self._operators:
                return self._operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        else:
            raise ValueError(f"Unsupported syntax: {type(node).__name__}")

    def _run(self, expression: str) -> ToolResult:
        if not expression or not isinstance(expression, str):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.INVALID_TOOL_INPUT,
                error_message="Invalid expression. String expression required."
            )

        # Sanitize basic characters
        cleaned_expr = expression.strip().replace("×", "*").replace("÷", "/")

        try:
            parsed_ast = ast.parse(cleaned_expr, mode='eval')
            result = self._eval_node(parsed_ast.body)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result
            )
        except ZeroDivisionError as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.TOOL_EXECUTION_ERROR,
                error_message=str(e)
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.INVALID_TOOL_INPUT,
                error_message=f"Failed to parse mathematical expression: {str(e)}"
            )