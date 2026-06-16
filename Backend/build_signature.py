import numpy as np
import os
from PIL import Image
from prnu_math import AlgebraicPRNU

def create_custom_signature(image_folder_path, device_name, save_folder='signatures'):
    """
    Generates a real PRNU sensor signature by averaging the noise residuals 
    from multiple images taken by the same camera.
    """
    engine = AlgebraicPRNU()
    accumulated_residual = None
    image_count = 0
    
    # Ensure output directory exists
    os.makedirs(save_folder, exist_ok=True)
    
    print(f"[*] Starting signature generation for: {device_name}")
    
    # Loop through all images in the provided folder
    for filename in os.listdir(image_folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(image_folder_path, filename)
            
            try:
                # Load image and convert to grayscale matrix
                img = Image.open(filepath).convert('L')
                Y = np.array(img).astype(np.float32)
                
                # Extract the noise residual (W) using your Wiener filter math
                W = engine.extract_residual(Y)
                
                # Add to the running total
                if accumulated_residual is None:
                    accumulated_residual = np.zeros_like(W)
                
                accumulated_residual += W
                image_count += 1
                print(f"    - Processed {filename}...")
                
            except Exception as e:
                print(f"[!] Failed to process {filename}: {e}")

    if image_count == 0:
        print("[!] No valid images found in the folder.")
        return

    # Calculate the average to isolate the permanent hardware fingerprint (K)
    final_signature_K = accumulated_residual / image_count
    
    # Save the binary signature to the library
    save_path = os.path.join(save_folder, f"{device_name}.npy")
    np.save(save_path, final_signature_K)
    
    print(f"\n[✔] Success! Signature saved to {save_path}")
    print(f"    - Total images averaged: {image_count}")
    print(f"    - Signature Matrix Shape: {final_signature_K.shape}")

# ==========================================
# Execution
# ==========================================
if __name__ == "__main__":
    # Example usage:
    # 1. Create a folder named "my_phone_photos" in your Backend directory.
    # 2. Put 10-20 photos taken by your personal phone in that folder.
    # 3. Run this script.
    
    target_folder = "my_phone_photos"
    custom_device_name = "My_Personal_Phone" 
    
    # Only run if the folder actually exists
    if os.path.exists(target_folder):
        create_custom_signature(target_folder, custom_device_name)
    else:
        print(f"Please create a folder named '{target_folder}' and add some images to it.")