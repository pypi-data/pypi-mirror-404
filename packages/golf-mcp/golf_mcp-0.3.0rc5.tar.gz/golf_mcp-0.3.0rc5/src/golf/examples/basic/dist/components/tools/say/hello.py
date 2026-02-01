"Enhanced hello tool with elicitation capabilities."

from typing import Annotated
from pydantic import BaseModel, Field
from golf.utilities import elicit

class Output(BaseModel):
    """Response from the hello tool."""
    message: str

async def hello(name: Annotated[str, Field(description='The name of the person to greet')]='World', greeting: Annotated[str, Field(description='The greeting phrase to use')]='Hello', personalized: Annotated[bool, Field(description='Whether to ask for additional personal details to create a personalized greeting', default=False)]=False) -> Output:
    """Say hello with optional personalized elicitation.

    This enhanced tool can:
    - Provide basic greetings
    - Elicit additional personal information for personalized messages
    - Demonstrate Golf's elicitation capabilities

    Examples:
    - hello("Alice") → "Hello, Alice!"
    - hello("Bob", personalized=True) → Asks for details, then personalized greeting
    """
    basic_message = f'{greeting}, {name}!'
    if personalized:
        try:
            mood = await elicit('How are you feeling today?', ['happy', 'excited', 'calm', 'focused', 'creative'])
            personalized_message = f"{greeting}, {name}! Hope you're having a {mood} day!"
            return Output(message=personalized_message)
        except Exception as e:
            print(f'Personalization failed: {e}')
            return Output(message=f'{basic_message} (personalization unavailable)')
    print(f'{greeting} {name}...')
    return Output(message=basic_message)
export = hello