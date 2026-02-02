"""
LangChain integration for Argus

Automatically track all LangChain LLM calls with Argus observability.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
import time

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseCallbackHandler = object

from ..storage import Storage
from ..pricing import calculate_cost


class ArgusCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for Argus observability
    
    Automatically tracks:
    - All LLM calls (OpenAI, Anthropic, etc.)
    - Token usage and costs
    - Latency and performance
    - Errors and failures
    - Chain execution
    
    Usage:
        from argus.integrations import ArgusCallbackHandler
        from langchain.llms import OpenAI
        
        # Add to LLM
        llm = OpenAI(callbacks=[ArgusCallbackHandler()])
        
        # Or add to chain
        chain = LLMChain(llm=llm, callbacks=[ArgusCallbackHandler()])
        
        # All calls are now tracked in Argus!
    """
    
    def __init__(
        self,
        agent_name: str = "langchain-agent",
        tags: Optional[List[str]] = None,
        db_path: str = "argus.db"
    ):
        """
        Initialize Argus callback handler
        
        Args:
            agent_name: Name for this agent in Argus dashboard
            tags: Optional tags for categorization
            db_path: Path to Argus database
        """
        super().__init__()
        self.agent_name = agent_name
        self.tags = tags or ["langchain"]
        self.storage = Storage(db_path)
        self._call_data = {}
        
        # Register agent
        self.storage.register_agent(
            name=self.agent_name,
            tags=self.tags
        )
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts running"""
        run_id = kwargs.get("run_id")
        if run_id:
            self._call_data[str(run_id)] = {
                "start_time": time.time(),
                "prompts": prompts,
                "model": serialized.get("name", "unknown"),
                "provider": self._detect_provider(serialized),
            }
    
    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any
    ) -> None:
        """Called when LLM ends running"""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._call_data:
            return
        
        call_data = self._call_data.pop(str(run_id))
        
        # Calculate duration
        duration_ms = int((time.time() - call_data["start_time"]) * 1000)
        
        # Extract token usage and calculate cost
        cost = 0.0
        token_usage = {}
        
        if hasattr(response, "llm_output") and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            
            if token_usage:
                input_tokens = token_usage.get("prompt_tokens", 0)
                output_tokens = token_usage.get("completion_tokens", 0)
                
                # Calculate cost
                cost = calculate_cost(
                    provider=call_data["provider"],
                    model=call_data["model"],
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )
        
        # Get response text
        output_text = ""
        if response.generations:
            output_text = response.generations[0][0].text[:500]
        
        # Log to Argus
        from datetime import datetime
        self.storage.log_call(
            call_id=str(run_id),
            agent_name=self.agent_name,
            input_data={
                "prompts": [p[:500] for p in call_data["prompts"]],
                "model": call_data["model"],
                "provider": call_data["provider"]
            },
            output_data={
                "text": output_text,
                "tokens": token_usage
            },
            status="success",
            error=None,
            duration_ms=duration_ms,
            cost=cost,
            timestamp=datetime.utcnow()
        )
    
    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Called when LLM errors"""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._call_data:
            return
        
        call_data = self._call_data.pop(str(run_id))
        
        # Calculate duration
        duration_ms = int((time.time() - call_data["start_time"]) * 1000)
        
        # Log error to Argus
        from datetime import datetime
        self.storage.log_call(
            call_id=str(run_id),
            agent_name=self.agent_name,
            input_data={
                "prompts": [p[:500] for p in call_data["prompts"]],
                "model": call_data["model"]
            },
            output_data={},
            status="error",
            error=str(error),
            duration_ms=duration_ms,
            cost=0.0,
            timestamp=datetime.utcnow()
        )
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when chain starts running"""
        # We track individual LLM calls, not chains
        pass
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when chain ends running"""
        pass
    
    def on_chain_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Called when chain errors"""
        pass
    
    def _detect_provider(self, serialized: Dict[str, Any]) -> str:
        """Detect LLM provider from serialized data"""
        name = serialized.get("name", "").lower()
        id_list = serialized.get("id", [])
        
        # Check name
        if "openai" in name:
            return "openai"
        elif "anthropic" in name or "claude" in name:
            return "anthropic"
        elif "cohere" in name:
            return "cohere"
        
        # Check id list
        for id_item in id_list:
            id_lower = str(id_item).lower()
            if "openai" in id_lower:
                return "openai"
            elif "anthropic" in id_lower:
                return "anthropic"
            elif "cohere" in id_lower:
                return "cohere"
        
        return "unknown"


# Convenience function
def create_callback(
    agent_name: str = "langchain-agent",
    tags: Optional[List[str]] = None
) -> ArgusCallbackHandler:
    """
    Create an Argus callback handler for LangChain
    
    Args:
        agent_name: Name for this agent in Argus dashboard
        tags: Optional tags for categorization
    
    Returns:
        ArgusCallbackHandler instance
    
    Example:
        from argus.integrations import create_callback
        from langchain.llms import OpenAI
        
        callback = create_callback(agent_name="my-bot", tags=["production"])
        llm = OpenAI(callbacks=[callback])
    """
    return ArgusCallbackHandler(agent_name=agent_name, tags=tags)
