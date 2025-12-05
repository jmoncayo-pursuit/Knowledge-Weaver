from PIL import Image, ImageDraw
import os
import math

def create_icon(size):
    # Create a new image with a transparent background
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw a black circle
    draw.ellipse((0, 0, size, size), fill="black")

    # Draw a white spiderweb
    # Center coordinates
    cx, cy = size // 2, size // 2
    
    # Draw radial lines
    for i in range(0, 360, 45):
        angle = math.radians(i)
        # Start slightly offset from center to look cleaner
        start_x = cx
        start_y = cy
        end_x = cx + (size // 2 * 0.9) * math.cos(angle)
        end_y = cy + (size // 2 * 0.9) * math.sin(angle)
        draw.line((start_x, start_y, end_x, end_y), fill="white", width=max(1, size // 40))

    # Draw concentric polygons (web)
    num_rings = 3
    max_radius = size // 2 * 0.9
    step = max_radius / (num_rings + 1)
    
    for i in range(1, num_rings + 1):
        r = step * i
        points = []
        for angle_deg in range(0, 360, 45):
            angle = math.radians(angle_deg)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        # Close the loop
        points.append(points[0]) 
        draw.line(points, fill="white", width=max(1, size // 60))

    return image

def main():
    icon_sizes = [16, 48, 128]
    output_dir = "app_extension/icons"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for size in icon_sizes:
        image = create_icon(size)
        filename = f"icon{size}.png"
        path = os.path.join(output_dir, filename)
        image.save(path)
        print(f"Saved {path}")

if __name__ == "__main__":
    main()
