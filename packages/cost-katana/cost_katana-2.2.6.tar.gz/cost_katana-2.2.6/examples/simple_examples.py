#!/usr/bin/env python3
"""
Simple Examples - Cost Katana Python SDK

Shows the easiest ways to use Cost Katana for common tasks.
"""

import cost_katana as ck
from cost_katana import openai, anthropic, google


def example_1_hello_world():
    """The simplest possible example."""
    print("📝 Example 1: Hello World")
    print("-" * 50)

    # NEW: Type-safe model selection
    response = ck.ai(openai.gpt_4, "Hello, world!")
    print(response.text)
    print(f"Cost: ${response.cost:.6f}")
    print()


def example_2_model_comparison():
    """Compare costs across different models."""
    print("📝 Example 2: Model Comparison")
    print("-" * 50)

    # NEW: Using type-safe constants
    models = [
        ("gpt-4", openai.gpt_4),
        ("gpt-3.5-turbo", openai.gpt_3_5_turbo),
        ("claude-3-haiku", anthropic.claude_3_haiku_20240307),
    ]
    prompt = "Explain machine learning in one sentence"

    for name, constant in models:
        try:
            response = ck.ai(constant, prompt)
            print(f"{name:20s} ${response.cost:.6f} - {response.text[:60]}...")
        except Exception as e:
            print(f"{name:20s} Failed: {str(e)[:40]}")
    print()


def example_3_chat_conversation():
    """Multi-turn conversation with cost tracking."""
    print("📝 Example 3: Chat Conversation")
    print("-" * 50)

    # NEW: Type-safe model
    chat = ck.chat(openai.gpt_3_5_turbo, system_message="You are a helpful Python expert.")

    questions = [
        "Hello! Can you help me with Python?",
        "How do I read a file?",
        "Show me an example",
    ]

    for question in questions:
        print(f"You: {question}")
        response = chat.send(question)
        print(f"AI: {response[:100]}...")
        print()

    print(f"💰 Total cost: ${chat.total_cost:.6f}")
    print(f"📊 Total messages: {len(chat.history)}")
    print()


def example_4_cost_optimization():
    """Compare standard vs optimized costs."""
    print("📝 Example 4: Cost Optimization")
    print("-" * 50)

    prompt = "Write a comprehensive guide to lists in Python"

    # Standard
    standard = ck.ai(openai.gpt_4, prompt)
    print(f"Standard cost: ${standard.cost:.6f}")

    # Optimized with Cortex
    optimized = ck.ai(openai.gpt_4, prompt, cortex=True)
    print(f"Optimized cost: ${optimized.cost:.6f}")

    savings = standard.cost - optimized.cost
    if savings > 0:
        percent = (savings / standard.cost) * 100
        print(f"💰 Saved: ${savings:.6f} ({percent:.1f}%)")
    print()


def example_5_smart_caching():
    """Demonstrate smart caching."""
    print("📝 Example 5: Smart Caching")
    print("-" * 50)

    question = "What is the capital of France?"

    # First call
    r1 = ck.ai(openai.gpt_3_5_turbo, question, cache=True)
    print(f"First call:  ${r1.cost:.6f}, Cached: {r1.cached}")

    # Second call - should be cached
    r2 = ck.ai(openai.gpt_3_5_turbo, question, cache=True)
    print(f"Second call: ${r2.cost:.6f}, Cached: {r2.cached}")

    if r2.cached:
        print("✅ Second call was free from cache!")
    print()


def example_6_content_generation():
    """Generate different types of content."""
    print("📝 Example 6: Content Generation")
    print("-" * 50)

    # Blog post
    blog = ck.ai(openai.gpt_4, "Write a 100-word blog post about AI", max_tokens=200)
    print(f"Blog post: {len(blog.text.split())} words, ${blog.cost:.6f}")

    # Code
    code = ck.ai(
        anthropic.claude_3_5_sonnet_20241022, "Write a Python function to sort a list", cache=True
    )
    print(f"Code generated: {len(code.text)} chars, ${code.cost:.6f}")

    # Translation
    translation = ck.ai(
        openai.gpt_3_5_turbo, "Translate to Spanish: Hello world", cache=True
    )
    print(f"Translation: {translation.text}, ${translation.cost:.6f}")
    print()


def example_7_error_handling():
    """Handle errors gracefully."""
    print("📝 Example 7: Error Handling")
    print("-" * 50)

    try:
        # Try with invalid model
        response = ck.ai("invalid-model", "Hello")
    except ck.CostKatanaError as e:
        print(f"Caught error: {str(e)[:100]}...")
        print("Error includes helpful troubleshooting steps ✅")
    print()


def example_8_batch_processing():
    """Process multiple prompts efficiently."""
    print("📝 Example 8: Batch Processing")
    print("-" * 50)

    prompts = ["What is Python?", "What is JavaScript?", "What is TypeScript?"]

    total_cost = 0

    for prompt in prompts:
        response = ck.ai(openai.gpt_3_5_turbo, prompt, cache=True)
        total_cost += response.cost
        print(f"• {prompt}: ${response.cost:.6f}")

    print(f"\n💰 Total cost: ${total_cost:.6f}")
    print(f"📊 Average: ${total_cost/len(prompts):.6f} per question")
    print()


def main():
    """Run all examples."""
    print("\n🥷 Cost Katana Python - Simple Examples\n")

    try:
        # Check if configured
        has_key = False
        try:
            # Try to use without explicit config
            test = ck.ai(openai.gpt_3_5_turbo, "test", max_tokens=5)
            has_key = True
        except:
            pass

        if not has_key:
            print("⚠️  No API key found!")
            print("\nTo run these examples, set your API key:")
            print("  export COST_KATANA_API_KEY='dak_your_key'")
            print("\nOr configure in the code:")
            print("  ck.configure(api_key='dak_your_key')")
            print("\nGet your key at: https://costkatana.com/settings\n")
            return

        # Run examples
        example_1_hello_world()
        example_2_model_comparison()
        example_3_chat_conversation()
        example_4_cost_optimization()
        example_5_smart_caching()
        example_6_content_generation()
        example_7_error_handling()
        example_8_batch_processing()

        print("=" * 50)
        print("\n✅ All examples completed successfully!")
        print("\n💡 Tips:")
        print("  • The simple API auto-detects your configuration")
        print("  • Use ck.chat() for conversations with cost tracking")
        print("  • Enable cortex=True for 40-75% cost savings")
        print("  • Check your dashboard at https://costkatana.com for analytics")
        print()

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("  1. Valid API key set")
        print("  2. Active internet connection")
        print("  3. Cost Katana account at costkatana.com")


if __name__ == "__main__":
    main()
