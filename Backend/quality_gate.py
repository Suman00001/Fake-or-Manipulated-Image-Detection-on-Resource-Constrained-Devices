import os
from PIL import Image

class ForensicQualityGate:
    def __init__(self):
        self.min_bpp = 1.2

    def should_run_cfa(self, image_path):
        """
        Calculates compressed Information Density to determine if high-frequency 
        interpolation grids remain intact.
        """
        try:
            img = Image.open(image_path)
            file_size_bytes = os.path.getsize(image_path)
            total_pixels = img.width * img.height
            
            bpp = (file_size_bytes * 8) / total_pixels
            print(f"[*] Information Density Evaluated: {bpp:.2f} bits/pixel")
            
            if bpp < self.min_bpp:
                print("[!] Structural destruction detected. CFA module bypassed.")
                return False

            print("[✔] Trace stability bounds passed. Activating CFA Analysis.")
            return True
        except Exception as e:
            print(f"[!] Quality Gate error: {e}")
            return True