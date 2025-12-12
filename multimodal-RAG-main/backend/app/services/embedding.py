import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

class EmbeddingService:
    """
    A service to handle the creation of text and image embeddings using a CLIP model.
    The model is loaded once during initialization.
    """
    def __init__(self):
        """
        Initializes the EmbeddingService by loading the CLIP model and processor.
        This is a heavy operation and should only be done once.
        """
        model_name = "openai/clip-vit-base-patch32"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"EmbeddingService: Loading model '{model_name}' onto device '{self.device}'")

        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        print("EmbeddingService: CLIP model and processor loaded successfully.")

    def create_text_embedding(self, text: str) -> list[float]:
        """
        Creates a vector embedding for a given text string.
        """
        inputs = self.processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
        
        # Normalize the features and convert to a standard Python list
        text_features /= text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy().flatten().tolist()

    def create_image_embedding(self, image: Image.Image) -> list[float]:
        """
        Creates a vector embedding for a given PIL Image.
        """
        # Ensure image is in RGB format
        image = image.convert("RGB")
        inputs = self.processor(images=[image], return_tensors="pt").to(self.device)
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
        
        # Normalize the features and convert to a standard Python list
        image_features /= image_features.norm(dim=-1, keepdim=True)
        return image_features.cpu().numpy().flatten().tolist()

# Create a single, reusable instance of the service
embedding_service = EmbeddingService()