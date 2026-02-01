from typing import List, Optional

class BitLlamaConfig:
    vocab_size: int
    hidden_dim: int
    num_layers: int
    inner_lr: float
    n_gpu_layers: Optional[int]

    def __init__(self, vocab_size: int, hidden_dim: int, num_layers: int, inner_lr: float) -> None: ...

class BitLlama:
    """BitLlama model wrapper for inference.
    
    Args:
        config: BitLlamaConfig object with model configuration
        checkpoint_path: Path to the model checkpoint file (.safetensors)
        device: Device to run on ("cpu" or "cuda"). Defaults to "cpu"
        tokenizer_path: Path to tokenizer.json file for text encoding/decoding
    """
    def __init__(
        self, 
        config: BitLlamaConfig, 
        checkpoint_path: str, 
        device: Optional[str] = None,
        tokenizer_path: Optional[str] = None
    ) -> None: ...
    
    def forward(self, token_id: int) -> List[float]: 
        """Forward pass on a single token.
        
        Args:
            token_id: Token ID to process
            
        Returns:
            Logits over the vocabulary
        """
        ...
    
    def generate(self, prompt: str, max_tokens: int) -> str:
        """Generate text from a prompt.
        
        Requires tokenizer to be loaded during initialization.
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text (excluding the prompt)
            
        Raises:
            ValueError: If tokenizer was not provided during initialization
        """
        ...
    
    def generate_tokens(self, start_tokens: List[int], max_new_tokens: int) -> List[int]:
        """Generate tokens from a list of starting token IDs.
        
        Args:
            start_tokens: List of token IDs to start from
            max_new_tokens: Maximum number of new tokens to generate
            
        Returns:
            Full list of tokens (prompt + generated)
        """
        ...

class PyTrainer:
    """BitLlama trainer for model training."""
    def __init__(
        self, 
        config: BitLlamaConfig, 
        checkpoint_path: Optional[str] = None, 
        device: Optional[str] = None
    ) -> None: ...
    
    def set_learning_rate(self, lr: float) -> None: 
        """Set the learning rate for the optimizer."""
        ...
    
    def train_step(self, py_input_ids: List[int], py_targets: List[int]) -> float:
        """Execute one training step.
        
        Args:
            py_input_ids: Input token IDs
            py_targets: Target token IDs (labels)
            
        Returns:
            Loss value for this step
        """
        ...
    
    def save_checkpoint(self, path: str) -> None:
        """Save model checkpoint and optimizer state.
        
        Args:
            path: Path to save checkpoint (creates .safetensors and .safetensors.optim files)
        """
        ...
