"""Research agent example using OpenAI function calling.

This example shows how to create an AI research assistant that
automatically uses the research plugins to answer questions.

Requirements:
    pip install semantic-kernel-builtsimple openai

Environment:
    Set OPENAI_API_KEY environment variable
"""

import asyncio
import os

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel_builtsimple import BuiltSimpleResearchPlugin


async def main():
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Create kernel
    kernel = Kernel()

    # Add OpenAI chat service
    service_id = "chat"
    kernel.add_service(OpenAIChatCompletion(
        service_id=service_id,
        ai_model_id="gpt-4o-mini",  # or "gpt-4o" for better results
    ))

    # Add research plugin (includes PubMed, ArXiv, Wikipedia)
    kernel.add_plugin(BuiltSimpleResearchPlugin(), plugin_name="research")

    # Configure function calling
    settings: OpenAIChatPromptExecutionSettings = (
        kernel.get_prompt_execution_settings_from_service_id(service_id)
    )
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
        filters={"included_plugins": ["research"]}
    )

    # Create chat history with system message
    chat_history = ChatHistory()
    chat_history.add_system_message("""You are a helpful research assistant with access to:
- PubMed: peer-reviewed biomedical and life sciences literature
- ArXiv: preprints in physics, mathematics, computer science, and AI/ML
- Wikipedia: general knowledge and factual information

When answering questions:
1. Search the most relevant source(s) for the topic
2. Synthesize information from the papers/articles
3. Always cite your sources with titles and identifiers (PMID, ArXiv ID, etc.)
4. Be accurate and acknowledge limitations

Use PubMed for medical/biological topics, ArXiv for CS/ML/physics, and Wikipedia for general facts.""")

    # Interactive chat loop
    print("Research Assistant Ready! (type 'quit' to exit)")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        chat_history.add_user_message(user_input)

        # Get response with function calling
        result = await kernel.invoke_prompt(
            prompt="{{$chat_history}}",
            settings=settings,
            chat_history=chat_history,
        )

        response = str(result)
        print(f"\nAssistant: {response}")
        chat_history.add_assistant_message(response)


if __name__ == "__main__":
    asyncio.run(main())
