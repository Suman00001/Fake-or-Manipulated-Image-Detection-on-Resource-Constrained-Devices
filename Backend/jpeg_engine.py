from jpeg_math import AlgebraicJPEG
import numpy as np
from PIL import Image

class AdvancedJPEG(AlgebraicJPEG):
    def __init__(self):
        super().__init__()
        # A grid regularity index below 1.15 indicates that the standard 
        # 8x8 JPEG structure has been broken or double-saved out of alignment.
        self.grid_threshold = 1.15

    def detect_dimple_artifacts(self, image_path):
        """
        Automated spatial Block Artifact Grid consistency analyzer.
        Bypasses raw bitstream requirements using structural grid math.
        """
        print("[*] Running Spatial-Domain JPEG Grid Regularity Analysis...")
        try:
            img = Image.open(image_path).convert('L')
            Y_matrix = np.array(img).astype(np.float32)
            
            profile_h, profile_v = self.calculate_blockiness_signal(Y_matrix)
            
            reg_h = self.measure_grid_regularity(profile_h)
            reg_v = self.measure_grid_regularity(profile_v)
            
            # Combine horizontal and vertical grid metrics
            grid_regularity = (reg_h + reg_v) / 2.0
            
            is_fake = grid_regularity < self.grid_threshold
            
            if is_fake:
                confidence = 0.2  # Apply penalty score for broken structural grids
                verdict = "Fake (Disrupted JPEG Block Grid)"
            else:
                # Normalize regularity metrics into a clean confidence bound
                confidence = min(1.0, grid_regularity / 2.0)
                verdict = "Authentic (Consistent JPEG Block Grid)"
                
            return verdict, float(confidence), grid_regularity
            
        except Exception as e:
            print(f"[!] Spatial JPEG grid analysis failed: {e}")
            return "Inconclusive", 0.5, 1.0