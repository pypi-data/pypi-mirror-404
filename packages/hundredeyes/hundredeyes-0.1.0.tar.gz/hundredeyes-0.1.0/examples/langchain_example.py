"""
Example: LangChain integration with Argus

Automatically track all LangChain LLM calls with zero code changes!
"""

import os


def example_basic_llm():
    """Basic LLM tracking with LangChain"""
    try:
        from langchain.llms import OpenAI
        from argus.integrations import ArgusCallbackHandler
        
        # Create Argus callback
        callback = ArgusCallbackHandler(
            agent_name="langchain-openai",
            tags=["langchain", "openai", "production"]
        )
        
        # Add callback to LLM
        llm = OpenAI(
            temperature=0.7,
            callbacks=[callback]  # That's it! All calls tracked
        )
        
        # Use LLM normally
        print("🤖 Calling OpenAI via LangChain...")
        response = llm("Explain quantum computing in one sentence")
        
        print(f"✅ Response: {response}")
        print(f"💰 Cost automatically tracked in Argus!")
        
    except ImportError:
        print("⚠️  LangChain not installed. Run: pip install langchain openai")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_chat_model():
    """Chat model tracking"""
    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        from argus.integrations import ArgusCallbackHandler
        
        callback = ArgusCallbackHandler(
            agent_name="langchain-chat",
            tags=["langchain", "chat"]
        )
        
        chat = ChatOpenAI(
            model="gpt-3.5-turbo",
            callbacks=[callback]
        )
        
        print("\n🤖 Calling ChatGPT via LangChain...")
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is the capital of France?")
        ]
        
        response = chat(messages)
        print(f"✅ Response: {response.content}")
        print(f"💰 Cost: ~$0.001 (automatically tracked)")
        
    except ImportError:
        print("⚠️  LangChain not installed")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_chain():
    """Track entire LangChain chains"""
    try:
        from langchain.llms import OpenAI
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        from argus.integrations import ArgusCallbackHandler
        
        callback = ArgusCallbackHandler(
            agent_name="langchain-chain",
            tags=["langchain", "chain"]
        )
        
        # Create chain
        llm = OpenAI(temperature=0.9)
        prompt = PromptTemplate(
            input_variables=["product"],
            template="What is a good name for a company that makes {product}?"
        )
        
        chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callbacks=[callback]  # Track entire chain
        )
        
        print("\n🤖 Running LangChain chain...")
        response = chain.run("AI-powered code review tools")
        
        print(f"✅ Response: {response}")
        print(f"💰 All LLM calls in chain tracked!")
        
    except ImportError:
        print("⚠️  LangChain not installed")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_multiple_calls():
    """Track multiple LLM calls"""
    try:
        from langchain.llms import OpenAI
        from argus.integrations import ArgusCallbackHandler
        
        callback = ArgusCallbackHandler(
            agent_name="langchain-batch",
            tags=["langchain", "batch"]
        )
        
        llm = OpenAI(callbacks=[callback])
        
        print("\n🤖 Making multiple LLM calls...")
        
        questions = [
            "What is Python?",
            "What is JavaScript?",
            "What is Rust?"
        ]
        
        for i, question in enumerate(questions, 1):
            response = llm(question)
            print(f"  {i}. {question[:30]}... ✅")
        
        print(f"💰 All {len(questions)} calls tracked in Argus!")
        
    except ImportError:
        print("⚠️  LangChain not installed")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_anthropic():
    """Track Anthropic Claude via LangChain"""
    try:
        from langchain.chat_models import ChatAnthropic
        from langchain.schema import HumanMessage
        from argus.integrations import ArgusCallbackHandler
        
        callback = ArgusCallbackHandler(
            agent_name="langchain-claude",
            tags=["langchain", "anthropic"]
        )
        
        chat = ChatAnthropic(
            model="claude-3-opus-20240229",
            callbacks=[callback]
        )
        
        print("\n🤖 Calling Claude via LangChain...")
        response = chat([HumanMessage(content="Hello Claude!")])
        
        print(f"✅ Response: {response.content}")
        print(f"💰 Cost automatically calculated for Claude!")
        
    except ImportError:
        print("⚠️  LangChain or Anthropic not installed")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_error_tracking():
    """Track errors in LangChain calls"""
    try:
        from langchain.llms import OpenAI
        from argus.integrations import ArgusCallbackHandler
        
        callback = ArgusCallbackHandler(
            agent_name="langchain-errors",
            tags=["langchain", "testing"]
        )
        
        # Invalid API key to trigger error
        llm = OpenAI(
            openai_api_key="invalid-key",
            callbacks=[callback]
        )
        
        print("\n🤖 Testing error tracking...")
        try:
            llm("This will fail")
        except Exception as e:
            print(f"❌ Error caught: {str(e)[:50]}...")
            print(f"💰 Error logged in Argus dashboard!")
        
    except ImportError:
        print("⚠️  LangChain not installed")


def show_stats():
    """Show Argus statistics"""
    from argus import watch
    
    print("\n" + "=" * 60)
    print("📊 Argus Statistics")
    print("=" * 60)
    
    stats = watch.stats()
    
    print(f"Total agents: {stats.get('total_agents', 0)}")
    print(f"Total calls: {stats.get('total_calls', 0)}")
    print(f"Total cost: ${stats.get('total_cost', 0):.4f}")
    
    if stats.get('agents'):
        print("\n🤖 Agents:")
        for agent in stats['agents']:
            print(f"  • {agent['name']}: {agent['total_calls']} calls, ${agent['total_cost']:.4f}")
    
    print("\n💡 View dashboard: argus dashboard")
    print("=" * 60)


if __name__ == "__main__":
    print("🎯 Argus + LangChain Integration Examples\n")
    
    # Run examples
    example_basic_llm()
    example_chat_model()
    example_chain()
    example_multiple_calls()
    example_anthropic()
    example_error_tracking()
    
    # Show stats
    show_stats()
    
    print("\n✅ All LangChain calls tracked in Argus!")
    print("📊 Open dashboard: http://localhost:3000")
