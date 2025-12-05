from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image(path):
    # Create a white image
    width = 1000
    height = 800
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to load a larger font, otherwise default
    try:
        font = ImageFont.truetype("Arial.ttf", 36)
        small_font = ImageFont.truetype("Arial.ttf", 24)
    except IOError:
        # Fallback to default if Arial not found (common on some linux, but Mac usually has it or similar)
        # On Mac, paths might differ. Let's try a safe path or just default.
        # Actually, let's just use default but scale it up if possible? No, PIL default is fixed.
        # We'll try to find a font.
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw a "chat" interface
    # Header
    draw.rectangle([0, 0, width, 80], fill='blue')
    draw.text((20, 20), "Teams Chat - CONFIDENTIAL", fill='white', font=font)
    
    # Message 1 - Alex Taylor
    draw.text((40, 120), "Questioner: Alex Taylor", fill='red', font=font)
    draw.rectangle([40, 160, 600, 220], outline='gray', width=2)
    draw.text((50, 170), "Hey, what is the patient's SSN?", fill='black', font=small_font)
    
    # Message 2 - Jordan Lee
    draw.text((40, 260), "Respondent: Jordan Lee", fill='green', font=font)
    draw.rectangle([40, 300, 600, 360], outline='gray', width=2)
    draw.text((50, 310), "It is 123-45-6789.", fill='black', font=small_font)
    
    # PII - Email
    draw.text((40, 450), "Contact: alex.taylor@example.com", fill='black', font=font)
    
    image.save(path)
    print(f"Created test image at {path}")

if __name__ == "__main__":
    create_test_image("test_screenshot.png")
