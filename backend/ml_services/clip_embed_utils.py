import torch
import numpy as np
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

device = "cpu"   # Safer for your system, change to cuda if needed

model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")


def embed_image(path):
    """Generate embedding for an image using CLIP model"""
    try:
        img = Image.open(path).convert("RGB")
        inputs = processor(images=img, return_tensors="pt").to(device)
        with torch.no_grad():
            feats = model.get_image_features(**inputs)
        v = feats.cpu().numpy()[0].astype("float32")
        v /= (np.linalg.norm(v) + 1e-10)
        return v
    except Exception as e:
        print(f"Error embedding image {path}: {e}")
        return None


def embed_text(text):
    """Generate embedding for text using CLIP model"""
    try:
        inputs = processor(text=[text], return_tensors="pt").to(device)
        with torch.no_grad():
            feats = model.get_text_features(**inputs)
        v = feats.cpu().numpy()[0].astype("float32")
        v /= (np.linalg.norm(v) + 1e-10)
        return v
    except Exception as e:
        print(f"Error embedding text '{text}': {e}")
        return None
