import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LocalTransformerClient:
    """Lazy-loaded local Hugging Face transformer client for offline processing"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LocalTransformerClient, cls).__new__(cls)
            cls._instance.pipeline = None
            # Using a highly-optimized, small causal LLM (Qwen 0.5B Instruct)
            cls._instance.model_name = "Qwen/Qwen2.5-0.5B-Instruct"
        return cls._instance

    def _ensure_model(self):
        """Lazy load the transformers pipeline on first inference request"""
        if self.pipeline is not None:
            return
            
        try:
            logger.info(f"Loading local causal transformer model: {self.model_name}...")
            # Monkeypatch packages_distributions to avoid slow filesystem scanning and hanging on import
            import importlib.metadata
            importlib.metadata.packages_distributions = lambda: {}
            
            import torch
            from transformers import pipeline
            
            # Use Apple Silicon GPU (Metal) if available, otherwise CPU
            device = -1
            if torch.backends.mps.is_available():
                device = "mps"
                logger.info("Using Apple Silicon Metal Performance Shaders (MPS) for local inference")
            elif torch.cuda.is_available():
                device = 0
                logger.info("Using CUDA GPU for local inference")
            else:
                logger.info("Using CPU for local inference")
                
            # Use text-generation task since it's fully supported in transformers v5
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device=device,
                torch_dtype=torch.float16 if device != -1 else torch.float32
            )
            logger.info("Successfully loaded local causal transformer model")
        except ImportError as e:
            logger.error(f"Failed to import torch/transformers: {e}")
            raise RuntimeError("Torch or Transformers library not installed in python environment")
        except Exception as e:
            logger.error(f"Failed to load local transformer pipeline: {e}")
            raise e

    def generate(self, prompt: str, max_new_tokens: int = 250) -> str:
        """Text generation using causal Qwen model"""
        self._ensure_model()
        if not self.pipeline:
            raise RuntimeError("Model pipeline not initialized")
            
        try:
            # Format prompt with Qwen Instruct chat template structure
            formatted_prompt = f"<|im_start|>system\nYou are Smart Bee, the user's premium email assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
            
            # Clamp tokens to 150 max to speed up local execution and prevent runaway generation
            max_tokens_clamp = min(max_new_tokens, 150)
            
            outputs = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_tokens_clamp,
                return_full_text=False,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                pad_token_id=self.pipeline.tokenizer.eos_token_id
            )
            
            response = outputs[0]["generated_text"].strip()
            # Clean up potential chat markers if any
            if "<|im_end|>" in response:
                response = response.split("<|im_end|>")[0].strip()
            return response
            
        except Exception as e:
            logger.error(f"Local inference error: {e}")
            return f"Error running local inference: {str(e)}"

    def summarize(self, text: str) -> str:
        """Summarize email body text"""
        prompt = f"Summarize this email subject and body concisely in one bulleted sentence:\n\n{text}"
        return self.generate(prompt, max_new_tokens=100)

    def answer_question(self, context: str, question: str) -> str:
        """Answer question based on context text"""
        prompt = f"Using the following email context, answer this question: {question}\n\nContext:\n{context}"
        return self.generate(prompt, max_new_tokens=200)

    def rewrite_email(self, text: str, instruction: str = "Rewrite this email to be professional and clear") -> str:
        """Rewrite a text string according to instructions"""
        prompt = f"Rewrite this email body based on the following instruction: {instruction}.\n\nEmail body:\n{text}"
        return self.generate(prompt, max_new_tokens=300)
