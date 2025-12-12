import google.generativeai as genai
from backend.app.core.config import settings, Settings
import logging
from typing import List, Dict, Any

class GenerativeService:
    """
    A service to connect to a multimodal LLM (Google Gemini) and generate responses
    based on retrieved context.
    """
    def __init__(self, config: Settings):
        """
        Initializes the Google Generative AI client.
        """
        self.model = None
        if config.GOOGLE_API_KEY and "YOUR_GOOGLE_API_KEY" not in config.GOOGLE_API_KEY:
            logging.info("GenerativeService: Google API key found. Initializing Gemini client.")
            try:
                genai.configure(api_key=config.GOOGLE_API_KEY)
                # Using gemini-pro-vision for multimodal capabilities
                self.model = genai.GenerativeModel('gemini-pro-vision')
                logging.info("GenerativeService: Gemini client initialized successfully.")
            except (RuntimeError, ValueError) as e:
                logging.error("GenerativeService: Error initializing Gemini client: %s", e)
        else:
            logging.warning("GenerativeService: Google API key not configured. Service will be disabled.")

    def generate_response(self, query: str, context_items: List[Dict[str, Any]]) -> str:
        """
        Formats a prompt with retrieved context and generates a response from the LLM.

        Args:
            query: The user's original question.
            context_items: A list of context items. Each item is a dict that can be
                           either {'type': 'text', 'content': str} or
                           {'type': 'image', 'content': PIL.Image}.

        Returns:
            The generated text response from the LLM.
        """
        if not self.model:
            return "Generative AI service is not configured."

        # Format the prompt for the multimodal LLM
        prompt_parts = [
            "You are an expert assistant. Use the following context to answer the user's question. The context may include text snippets and images. Provide a concise and direct answer based only on the provided context.\n",
            "--- CONTEXT START ---\n"
        ]

        for item in context_items:
            if item.get('type') == 'text':
                prompt_parts.append(f"Text: {item.get('content', '')}\n")
            elif item.get('type') == 'image':
                prompt_parts.append(item.get('content')) # Append PIL image directly

        prompt_parts.append("\n--- CONTEXT END ---\n")
        prompt_parts.append(f"User Question: {query}")

        response = self.model.generate_content(prompt_parts)
        return response.text

# Create a single, reusable instance of the service
generative_service = GenerativeService(settings)