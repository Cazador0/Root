"""
Conversation context management (chunking and summarization).
"""
from utils.logger import get_logger


class ContextManager:
    """Manage conversation context to fit within model limits."""
    
    def __init__(self, model_manager, max_context_length=4096):
        """
        Initialize context manager.
        
        Args:
            model_manager: ModelManager instance for token estimation
            max_context_length: Maximum context length in tokens
        """
        self.model_manager = model_manager
        self.max_context_length = max_context_length
        self.summary_threshold = max_context_length
        self.logger = get_logger("ContextManager")
    
    def update_max_context(self, max_context_length):
        """Update the maximum context length."""
        self.max_context_length = max_context_length
        self.summary_threshold = max_context_length
        self.logger.info(f"Updated max context length to {max_context_length}")
    
    def manage_context(self, messages):
        """
        Manage conversation context using chunking or summarization.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            list: Managed message list that fits within context
        """
        total_tokens = sum(
            self.model_manager.estimate_tokens(msg.get("content", "")) 
            for msg in messages
        )
        
        # If context is within limit, return as-is
        if total_tokens <= self.max_context_length:
            return messages
        
        self.logger.info(f"Context exceeds limit ({total_tokens} > {self.max_context_length}), managing...")
        
        # For very long conversations, create a summary
        if total_tokens > self.max_context_length * 2:
            return self._create_context_summary(messages)
        else:
            # For moderately long conversations, chunk
            return self._chunk_conversation(messages)
    
    def _chunk_conversation(self, messages):
        """
        Chunk conversation to fit within context limit.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            list: Chunked message list
        """
        if not messages:
            return messages
        
        # Keep system message and most recent messages
        system_msg = [msg for msg in messages if msg["role"] == "system"]
        non_system_msgs = [msg for msg in messages if msg["role"] != "system"]
        
        # Start with system messages
        chunked_messages = system_msg.copy()
        current_tokens = sum(
            self.model_manager.estimate_tokens(msg.get("content", "")) 
            for msg in chunked_messages
        )
        
        # Add messages from newest to oldest until we hit the limit
        for msg in reversed(non_system_msgs):
            msg_tokens = self.model_manager.estimate_tokens(msg.get("content", ""))
            
            if current_tokens + msg_tokens <= self.max_context_length:
                chunked_messages.append(msg)
                current_tokens += msg_tokens
            else:
                # Try to truncate the message if there's still room
                if current_tokens < self.max_context_length:
                    available_tokens = self.max_context_length - current_tokens
                    max_chars = available_tokens * 4
                    truncated_content = msg.get("content", "")[:max_chars] + " [truncated]"
                    truncated_msg = msg.copy()
                    truncated_msg["content"] = truncated_content
                    chunked_messages.append(truncated_msg)
                break
        
        # Reverse non-system messages to maintain chronological order
        non_system_chunked = [msg for msg in chunked_messages if msg["role"] != "system"]
        chunked_messages = system_msg + list(reversed(non_system_chunked))
        
        self.logger.info(f"Chunked conversation: {len(messages)} -> {len(chunked_messages)} messages")
        return chunked_messages
    
    def _create_context_summary(self, messages):
        """
        Create a summary of the conversation context.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            list: Messages with summary replacing old context
        """
        if not self.model_manager.is_loaded() or len(messages) <= 3:
            return self._chunk_conversation(messages)
        
        try:
            summary_prompt = [
                {
                    "role": "system", 
                    "content": "You are a concise summarizer. Create a brief summary of the conversation so far."
                },
                {
                    "role": "user", 
                    "content": f"Summarize this conversation in 2-3 sentences:\n\n{self._format_messages_for_summary(messages)}"
                }
            ]
            
            # Generate summary (non-streaming)
            summary_response = ""
            for response in self.model_manager.generate(
                messages=summary_prompt,
                temperature=0.3,
                max_tokens=150,
                stream=False
            ):
                summary_response = response
            
            # Replace conversation history with summary
            result = [
                {"role": "system", "content": messages[0]["content"]},
                {"role": "assistant", "content": f"Previous conversation summary: {summary_response}"}
            ]
            
            self.logger.info(f"Created context summary: {summary_response[:100]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"Summarization failed: {str(e)}")
            # Fall back to chunking
            return self._chunk_conversation(messages)
    
    def _format_messages_for_summary(self, messages):
        """
        Format messages for summary generation.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            str: Formatted message string
        """
        formatted = []
        for msg in messages:
            if msg["role"] != "system":
                formatted.append(f"{msg['role'].title()}: {msg.get('content', '')}")
        return "\n".join(formatted)
    
    def calculate_stats(self, messages):
        """
        Calculate statistics about the conversation context.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            dict: Statistics dictionary
        """
        total_messages = len(messages)
        total_tokens = sum(
            self.model_manager.estimate_tokens(msg.get("content", "")) 
            for msg in messages
        )
        
        system_tokens = sum(
            self.model_manager.estimate_tokens(msg.get("content", "")) 
            for msg in messages if msg["role"] == "system"
        )
        
        user_tokens = sum(
            self.model_manager.estimate_tokens(msg.get("content", "")) 
            for msg in messages if msg["role"] == "user"
        )
        
        assistant_tokens = sum(
            self.model_manager.estimate_tokens(msg.get("content", "")) 
            for msg in messages if msg["role"] == "assistant"
        )
        
        usage_percent = (total_tokens / self.max_context_length * 100) if self.max_context_length > 0 else 0
        
        return {
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "system_tokens": system_tokens,
            "user_tokens": user_tokens,
            "assistant_tokens": assistant_tokens,
            "max_context": self.max_context_length,
            "usage_percent": usage_percent
        }
