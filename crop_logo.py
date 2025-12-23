
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
        # 1. Be strictly transparent
        # 2. OR be very close to white (e.g. > 240)
        
        # Mask for non-transparent pixels
        non_transparent = a > 0
        
        # Mask for non-white pixels (where any channel is < 240)
        # This means if a pixel is (250, 250, 250), it is considered white/background.
        # We want to keep pixels that are darker than that.
        non_white = (r < 240) | (g < 240) | (b < 240)
        
        # Combined mask: We want pixels that are NOT transparent AND NOT white
        # Wait, if it's transparent, we don't care if it's white or not.
        # But commonly we just want the bounding box of the "content".
        # Content = (Visible) AND (Not White Background)
        
        # However, usually logos have transparency. If no transparency, we rely on white check.
        # If it has transparency, we rely on alpha.
        
        # Let's check if the image has meaningful alpha (not all 255)
        if np.min(a) == 255:
            # No transparency, assume white background
            mask = non_white
        else:
            # Has transparency. But sometimes there's a white matte AND transparency.
            # Let's assume we want to crop based on Visible Non-White pixels.
            # If a pixel is opaque white, do we want to keep it? 
            # Usually for logos on white bg, yes, crop the white.
            # If the logo HAS white parts inside it, this simple bbox might clip holes.
            # getbbox() finds the bounding box of NON-ZERO regions.
            # We want rows/cols that contain at least one "content" pixel.
            
            # Let's consider content = (Alpha > 10) AND (NOT (R>240 & G>240 & B>240))
            # This keeps colored pixels. What if the logo has white text?
            # If logo has white text, it must be surrounded by color or shadow, or we lose it against a white page background anyway.
            # But the user said "remove the large white area around it".
            mask = (a > 10) & ((r < 250) | (g < 250) | (b < 250))

        # Find indices where mask is True
        coords = np.argwhere(mask)
        
        if coords.size > 0:
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0) + 1 # Slice is exclusive at the end
            
            print(f"Cropping to: y={y0}:{y1}, x={x0}:{x1}")
            cropped_img = img.crop((x0, y0, x1, y1))
            cropped_img.save(output_path)
        else:
            print("No content found (image might be fully white/transparent). copying original.")
            img.save(output_path)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    crop_image("src_image/logo.png", "src_image/logo_cropped.png")
