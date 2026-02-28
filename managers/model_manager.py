"""
Model loading and inference management.
"""
from llama_cpp import Llama
from utils.logger import get_logger


class ModelManager:
    """Manage llama.cpp model loading and inference."""
    
    def __init__(self, config):
        """
        Initialize the model manager.
        
        Args:
            config: Config instance containing model configurations
        """
        self.config = config
        self.logger = get_logger("ModelManager")
        self.llm = None
        self.current_model = None
        self.model_config = {}
    
    def load_model(self, model_name, on_progress=None, on_complete=None):
        """
        Load a model by name.
        
        Args:
            model_name: Name of the model to load
            on_progress: Callback function(message) for progress updates
            on_complete: Callback function(success, message) when loading completes
        
        Returns:
            bool: True if loading started successfully
        """
        if model_name not in self.config.get_model_names():
            error_msg = f"Model '{model_name}' not found in configuration"
            self.logger.error(error_msg)
            if on_complete:
                on_complete(False, error_msg)
            return False
        
        model_path = self.config.get_model_path(model_name)
        self.model_config = self.config.get_model_config(model_name)
        
        # Check if file exists
        import os
        if not os.path.exists(model_path):
            error_msg = f"Model file not found: {model_path}"
            self.logger.error(error_msg)
            if on_complete:
                on_complete(False, error_msg)
            return False
        
        if on_progress:
            on_progress(f"Loading {model_name}...")
        
        try:
            self.logger.info(f"Loading model: {model_name} from {model_path}")
            self.logger.info(f"Config: {self.model_config}")
            
            # Load the model
            self.llm = Llama(
                model_path=model_path,
                n_ctx=self.model_config.get("n_ctx", 4096),
                n_threads=self.model_config.get("n_threads", 8),
                n_gpu_layers=self.model_config.get("n_gpu_layers", -1),
                verbose=True,
                use_mlock=True,
                f16_kv=True
            )
            
            self.current_model = model_name
            success_msg = f"{model_name} loaded successfully! (ctx: {self.model_config.get('n_ctx', 4096)})"
            self.logger.info(f"Successfully loaded {model_name}")
            
            if on_complete:
                on_complete(True, success_msg)
            
            return True
            
        except Exception as e:
            self.llm = None
            self.current_model = None
            error_msg = f"Error loading model: {str(e)}"
            self.logger.error(f"Failed to load {model_name}: {str(e)}", exc_info=True)
            
            if on_complete:
                on_complete(False, error_msg)
            
            return False
    
    def unload_model(self):
        """Unload the current model to free resources."""
        if self.llm:
            self.logger.info(f"Unloading model: {self.current_model}")
            self.llm = None
            self.current_model = None
            self.model_config = {}
    
    def generate(self, messages, temperature=0.7, max_tokens=4096, top_p=0.95,
                 stream=True, on_stop_check=None):
        """
        Generate a response from the model.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            stream: Whether to stream the response
            on_stop_check: Function that returns True if generation should stop
        
        Yields:
            str: Generated text chunks (if streaming) or full response
        """
        if not self.llm:
            self.logger.error("Attempted to generate without loaded model")
            raise RuntimeError("No model loaded")
        
        try:
            self.logger.info(f"Generating response (temp={temperature}, max_tokens={max_tokens})")
            
            if stream:
                response_text = ""
                for chunk in self.llm.create_chat_completion(
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=True
                ):
                    # Check if we should stop
                    if on_stop_check and on_stop_check():
                        response_text += " [stopped by user]"
                        yield response_text
                        break
                    
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            response_text += delta['content']
                            yield response_text
            else:
                response = self.llm.create_chat_completion(
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=False
                )
                response_text = response['choices'][0]['message']['content']
                yield response_text
            
            self.logger.info(f"Generated {len(response_text)} characters")
            
        except Exception as e:
            self.logger.error(f"Error during generation: {str(e)}", exc_info=True)
            raise
    
    def estimate_tokens(self, text):
        """
        Estimate token count for given text.
        
        Args:
            text: Text to tokenize
        
        Returns:
            int: Estimated token count
        """
        if self.llm:
            try:
                return len(self.llm.tokenize(text.encode('utf-8')))
            except:
                return len(text) // 4
        return len(text) // 4
    
    def is_loaded(self):
        """Check if a model is currently loaded."""
        return self.llm is not None
    
    def get_current_model(self):
        """Get the name of the currently loaded model."""
        return self.current_model
    
    def get_context_size(self):
        """Get the context size of the current model."""
        return self.model_config.get("n_ctx", 4096) if self.model_config else 4096
