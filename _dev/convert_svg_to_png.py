import cairosvg
from PIL import Image
import os

# Create PNG directory
png_dir = 'c:/Users/erkay/Desktop/önemli/etsy_images_png'
os.makedirs(png_dir, exist_ok=True)

svg_dir = 'c:/Users/erkay/Desktop/önemli/etsy_images'

# Convert each SVG to PNG
for filename in os.listdir(svg_dir):
    if filename.endswith('.svg'):
        svg_path = os.path.join(svg_dir, filename)
        png_filename = filename.replace('.svg', '.png')
        png_path = os.path.join(png_dir, png_filename)
        
        # Convert SVG to PNG with high resolution
        cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=2000, output_height=2000)
        print(f"Converted: {filename} -> {png_filename}")

print("\nAll SVG files converted to PNG successfully!")
