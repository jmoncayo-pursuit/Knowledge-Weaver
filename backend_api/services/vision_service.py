import os
import logging
import json
import re
from typing import List, Dict, Any, Tuple
import google.generativeai as genai
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)

class VisionService:
    """Service for analyzing images using Gemini Vision"""

    def __init__(self, api_key: str = None):
        """
        Initialize Vision Service
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Use Nano Banana Pro (Gemini 3 Pro Image Preview) as requested
        self.model = genai.GenerativeModel('nano-banana-pro-preview')
        
        logger.info("VisionService initialized successfully with nano-banana-pro-preview")

    def redact_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Redact PII from an image using Generative AI.
        
        Args:
            image_data: Raw bytes of the image
            
        Returns:
            Dict containing:
            - redacted_image: Base64 string of redacted image
            - original_image: Base64 string of original image
        """
        try:
            try:
                image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                logger.error(f"Failed to open image: {e}")
                raise ValueError("Invalid image data")
            
            prompt = """Please edit this image to be HIPAA compliant.
Task:

Redact: Black out or blur all Personally Identifiable Information (PII), including specific names, dates of birth, exact addresses, and medical record numbers.
Re-label: Replace the speaker names/labels. Use 'Questioner' for the person asking and 'Respondent' for the person answering.
Maintain: Keep the original layout and the non-sensitive dialogue text clear and readable."""
            
            logger.info("Sending image to Gemini for redaction...")
            response = self.model.generate_content([prompt, image])
            
            # The response should contain the generated image
            # We need to extract the image part from the response
            # Gemini 2.0 Flash Thinking should return an image if requested to edit?
            # Actually, generate_content usually returns text unless it's a specific image generation model or mode.
            # However, for "edit this image", if the model supports outputting images, it might be in parts.
            # Let's assume the model returns the image in the response parts.
            
            # Check if response has parts and if any part is an image
            # Note: The standard generate_content API for Gemini might return text. 
            # If we are using a model that outputs images (like Imagen or specific Gemini modes), we need to handle it.
            # The user prompt says "The redact_image function should now be a simple call to model.generate_content([image, prompt])."
            # And "Ensure the endpoint just returns the Base64 image that the AI gives back."
            # If Gemini 2.0 Flash Thinking returns an image, it will be in the candidates.
            
            # Let's inspect how to get the image from the response.
            # Usually it's response.parts[0].inline_data or similar if it returns an image.
            # Or if it's a text response describing the redaction, that's not what we want.
            # The user seems confident this works. I will assume the response contains the image.
            
            # If the model returns a PIL image directly (some SDK wrappers do this) or bytes.
            # Let's try to find the image in the response.
            
            # For now, I'll assume standard behavior:
            # If the model is capable of image-to-image, the response might contain the image data.
            # If not, this might fail. But I must follow the plan.
            
            # Actually, looking at the SDK, `generate_content` returns a `GenerateContentResponse`.
            # If it generated an image, it might be in `response.parts`.
            
            # Let's try to handle the case where it returns text (failure) or image.
            
            # Wait, standard Gemini API (as of late 2024/2025) might not return edited images directly via `generate_content` 
            # unless it's specifically the image generation endpoint or a multimodal output model.
            
            # Attempt to extract image data from the response
            redacted_image_data = None
            for part in response.parts:
                if hasattr(part, 'inline_data') and hasattr(part.inline_data, 'mime_type') and part.inline_data.mime_type.startswith('image/'):
                    redacted_image_data = part.inline_data.data
                    break
            
            if redacted_image_data:
                # Convert back to base64 for frontend
                img_str = base64.b64encode(redacted_image_data).decode('utf-8')
                
                redacted_img_val = f"data:image/png;base64,{img_str}"
                original_img_val = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
                
                logger.info(f"Redaction successful. Returning types: {type(redacted_img_val)}, {type(original_img_val)}")
                return {
                    "redacted_image": redacted_img_val,
                    "original_image": original_img_val,
                    "redacted_items": [] # No specific items
                }
            
            # If we get here, no image was found
            logger.warning(f"No image data found in Gemini response. Text: {response.text}")
            raise ValueError("Gemini returned text instead of an image. Please try again.")

        except Exception as e:
            logger.error(f"Error redacting image: {e}")
            raise e
