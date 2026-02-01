"Enhanced calculator tool with optional LLM-powered explanations."

from typing import Annotated
from pydantic import BaseModel, Field
from golf.utilities import sample

class CalculationResult(BaseModel):
    """Result of a mathematical calculation."""
    result: float
    operation: str
    expression: str

async def calculate(expression: Annotated[str, Field(description="Mathematical expression to evaluate (e.g., '2 + 3', '10 * 5', '100 / 4')", examples=['2 + 3', '10 * 5.5', '(8 - 3) * 2'])], explain: Annotated[bool, Field(description='Whether to provide an LLM-powered step-by-step explanation', default=False)]=False) -> CalculationResult:
    """Evaluate a mathematical expression with optional LLM explanation.

    This enhanced calculator can:
    - Perform basic arithmetic operations (+, -, *, /, parentheses)
    - Handle decimal numbers
    - Optionally provide LLM-powered step-by-step explanations

    Examples:
    - calculate("2 + 3") → 5
    - calculate("10 * 5.5") → 55.0
    - calculate("(8 - 3) * 2", explain=True) → 10 with explanation
    """
    try:
        allowed_chars = set('0123456789+-*/.() ')
        if not all((c in allowed_chars for c in expression)):
            raise ValueError('Expression contains invalid characters')
        result = eval(expression, {'__builtins__': {}}, {})
        if not isinstance(result, (int, float)):
            raise ValueError('Expression did not evaluate to a number')
        result_expression = expression
        if explain:
            try:
                explanation = await sample(f'Explain this mathematical expression step by step: {expression} = {result}', system_prompt='You are a helpful math tutor. Provide clear, step-by-step explanations.', max_tokens=200)
                result_expression = f'{expression}\n\nExplanation: {explanation}'
            except Exception:
                result_expression = f'{expression}\n\n(Explanation unavailable)'
        return CalculationResult(result=float(result), operation='evaluate', expression=result_expression)
    except ZeroDivisionError:
        return CalculationResult(result=float('inf'), operation='error', expression=f'{expression} → Division by zero')
    except Exception as e:
        return CalculationResult(result=0.0, operation='error', expression=f'{expression} → Error: {str(e)}')
export = calculate