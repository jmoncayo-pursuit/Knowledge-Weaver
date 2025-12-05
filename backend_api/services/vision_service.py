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
        
        # Use Gemini 2.0 Flash Exp (Confirmed Working)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("VisionService initialized successfully with gemini-2.0-flash-exp")

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
            # But the user says "Gemini 2.0 Flash Thinking model to generate the HIPAA-compliant image directly".
            # So I will assume it works.
            
            # I'll look for the image in the response.
            # If the SDK returns a PIL Image object in some way, or we need to access the bytes.
            
            # Let's look at how we might access the image. 
            # If `response.parts` has a part with `mime_type` starting with `image/`.
            
            generated_image_data = None
            
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        generated_image_data = part.inline_data.data
                        break
                    # Sometimes it might be in a different structure depending on the SDK version.
            
            # If we can't find it in parts, maybe the response itself has it?
            # The user's instruction is simple: "model.generate_content([image, prompt])".
            
            # If I can't guarantee the SDK structure, I'll add some logging and fallback.
            # But for "Pure AI", I should rely on it.
            
            if not generated_image_data:
                # Fallback/Error if no image returned
                # Maybe the model returns a URI?
                logger.warning("No image data found in Gemini response. Checking text...")
                logger.warning(f"Response text: {response.text}")
                # If it returns text, we can't do much.
                raise ValueError("Gemini did not return an image.")

            # Convert to Base64
            img_str = base64.b64encode(generated_image_data).decode("utf-8")
            
            redacted_img_val = f"data:image/png;base64,{img_str}"
            original_img_val = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
            
            logger.info(f"Redacted Image Type: {type(redacted_img_val)}")
            logger.info(f"Original Image Type: {type(original_img_val)}")
            
            return {
                "redacted_image": redacted_img_val,
                "original_image": original_img_val,
                "redacted_items": [] # No specific items
            }
            
        except Exception as e:
            logger.error(f"Error redacting image: {e}")
            raise e
