import base64
from PIL import Image, ImageDraw

def generate():
    img = Image.new('RGB', (400, 300), color = (255, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((10,10), 'EMAIL PROOF', fill=(255,255,255))
    img.save('email_proof.png')
    
    with open('email_proof.png', 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
        print(f"data:image/png;base64,{b64}")

if __name__ == "__main__":
    generate()
