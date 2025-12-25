
from PIL import Image
import numpy as np

def crop_image(input_path, output_path):
    try:
        img = Image.open(input_path)
        img = img.convert("RGBA")
        
        # Convert to numpy array
        data = np.array(img)
        
        # Split channels
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
        
        # Define what is "background"
        # We want to crop out the white background.
        
        # Mask for non-white pixels (where any channel is < 250, assuming close to pure white is bg)
        # Also consider pixels that are not fully transparent
        non_white_or_transparent = (a > 0) & ((r < 250) | (g < 250) | (b < 250))
        
        # Find indices where mask is True
        coords = np.argwhere(non_white_or_transparent)
        
        if coords.size > 0:
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0) + 1 # Slice is exclusive at the end
            
            print(f"Original size: {img.size}")
            print(f"Cropping to: y={y0}:{y1}, x={x0}:{x1}")
            
            # Crop using the bounding box
            cropped_img = img.crop((x0, y0, x1, y1))
            
            # Save
            cropped_img.save(output_path)
            print(f"Image saved to {output_path}")
        else:
            print("No content found (image might be fully white/transparent). Copying original.")
            img.save(output_path)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Input: top_logo.png (assumed name based on request, please verify if user provided exact name or file)
    # Output: logo_cropped.png
    input_file = "src_image/top_logo.png" 
    output_file = "src_image/logo_cropped.png"
    
    crop_image(input_file, output_file)
