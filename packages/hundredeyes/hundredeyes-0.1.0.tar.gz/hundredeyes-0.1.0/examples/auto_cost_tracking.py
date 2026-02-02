"""
Example: Automatic cost tracking for OpenAI and Anthropic
"""

from argus import watch
import os

# Note: You need to install openai and anthropic packages
# pip install openai anthropic


def example_openai_auto_cost():
    """Example with automatic OpenAI cost calculation"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-test"))
        
        @watch.agent(
            name="gpt-4-assistant",
            provider="openai",
            model="gpt-4",
            tags=["production", "openai"]
        )
        def ask_gpt4(prompt: str):
            """
            Argus will automatically:
            1. Extract token usage from response
            2. Calculate cost based on GPT-4 pricing
            3. Log everything to dashboard
            """
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response
        
        # Use it
        print("🤖 Calling GPT-4 with automatic cost tracking...")
        result = ask_gpt4("Explain quantum computing in one sentence")
        
        print(f"✅ Response: {result.choices[0].message.content}")
        print(f"💰 Cost automatically calculated and logged!")
        
    except ImportError:
        print("⚠️  OpenAI package not installed. Run: pip install openai")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_gpt35_auto_cost():
    """Example with GPT-3.5 Turbo (cheaper model)"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-test"))
        
        @watch.agent(
            name="gpt-3.5-summarizer",
            provider="openai",
            model="gpt-3.5-turbo",
            tags=["production", "fast"]
        )
        def summarize_text(text: str):
            """GPT-3.5 is 10x cheaper than GPT-4"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Summarize in one sentence."},
                    {"role": "user", "content": text}
                ]
            )
            return response
        
        # Use it
        print("\n🤖 Calling GPT-3.5 Turbo...")
        long_text = "Artificial intelligence is transforming how we work..." * 10
        result = summarize_text(long_text)
        
        print(f"✅ Summary: {result.choices[0].message.content}")
        print(f"💰 Cost: ~$0.001 (automatically calculated)")
        
    except ImportError:
        print("⚠️  OpenAI package not installed")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_anthropic_auto_cost():
    """Example with automatic Anthropic Claude cost calculation"""
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "sk-test"))
        
        @watch.agent(
            name="claude-3-opus",
            provider="anthropic",
            model="claude-3-opus-20240229",
            tags=["production", "anthropic"]
        )
        def ask_claude(prompt: str):
            """
            Argus will automatically:
            1. Extract token usage from response
            2. Calculate cost based on Claude pricing
            3. Log everything to dashboard
            """
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response
        
        # Use it
        print("\n🤖 Calling Claude 3 Opus...")
        result = ask_claude("What is the meaning of life?")
        
        print(f"✅ Response: {result.content[0].text}")
        print(f"💰 Cost automatically calculated and logged!")
        
    except ImportError:
        print("⚠️  Anthropic package not installed. Run: pip install anthropic")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_cost_comparison():
    """Compare costs across different models"""
    from argus import watch
    
    print("\n📊 Cost Comparison Example")
    print("=" * 50)
    
    # Simulate different models
    models = [
        ("openai", "gpt-4", 1000, 500),           # $0.06
        ("openai", "gpt-3.5-turbo", 1000, 500),   # $0.0013
        ("anthropic", "claude-3-opus-20240229", 1000, 500),  # $0.0525
        ("anthropic", "claude-3-haiku-20240307", 1000, 500), # $0.00088
    ]
    
    from argus.pricing import calculate_cost
    
    for provider, model, input_tokens, output_tokens in models:
        cost = calculate_cost(provider, model, input_tokens, output_tokens)
        print(f"{provider:12} {model:30} ${cost:.6f}")
    
    print("\n💡 Tip: Use cheaper models for simple tasks!")


def example_manual_cost_override():
    """You can still manually set cost if needed"""
    
    @watch.agent(
        name="custom-model",
        cost_per_call=0.05,  # Manual override
        tags=["custom"]
    )
    def custom_llm_call(prompt: str):
        """For custom models or APIs without token info"""
        # Your custom LLM logic
        return {"response": "Custom model response"}
    
    result = custom_llm_call("Hello")
    print(f"\n✅ Custom model with manual cost: $0.05")


if __name__ == "__main__":
    print("🎯 Argus - Automatic Cost Tracking Examples\n")
    
    # Run examples
    example_openai_auto_cost()
    example_gpt35_auto_cost()
    example_anthropic_auto_cost()
    example_cost_comparison()
    example_manual_cost_override()
    
    print("\n" + "=" * 50)
    print("📊 View all costs in dashboard:")
    print("   argus dashboard")
    print("   Open: http://localhost:3000")
    print("=" * 50)
    
    # Show stats
    stats = watch.stats()
    print(f"\n📈 Total tracked:")
    print(f"   Agents: {stats.get('total_agents', 0)}")
    print(f"   Calls: {stats.get('total_calls', 0)}")
    print(f"   Cost: ${stats.get('total_cost', 0):.4f}")
