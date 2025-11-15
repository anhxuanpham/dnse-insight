#!/usr/bin/env python3
"""
Example: Using AI Trading Assistant
"""
from ai_assistant.trading_assistant import trading_assistant
from loguru import logger


def main():
    """Run AI assistant example"""
    logger.info("AI Trading Assistant Example")

    # Example queries (works without OpenAI API)
    queries = [
        "What is the price of VCB?",
        "Show my portfolio",
        "Get signals for VCB",
        "Analyze VCB",
    ]

    for query in queries:
        logger.info(f"\n💬 User: {query}")
        response = trading_assistant.chat(query)
        logger.success(f"🤖 Assistant: {response}")


if __name__ == "__main__":
    # Note: For full AI capabilities, set OPENAI_API_KEY environment variable
    # export OPENAI_API_KEY="your-api-key"

    # Initialize with API key (optional)
    import os
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        from ai_assistant.trading_assistant import TradingAssistant
        global trading_assistant
        trading_assistant = TradingAssistant(api_key=api_key)
        logger.info("AI Assistant initialized with OpenAI")
    else:
        logger.warning("Running in basic mode (no OpenAI API key)")

    main()
