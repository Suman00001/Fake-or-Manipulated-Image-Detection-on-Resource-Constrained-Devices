import numpy as np
from PIL import Image
from illuminant_math import AlgebraicIlluminant

class AdvancedLighting(AlgebraicIlluminant):
    def __init__(self):
        super().__init__()
        self.grid_size = 256
        self.anomaly_threshold_degrees = 15.0

    def detect_lighting_anomalies(self, image_path):
        print("[*] Running Automated Illuminant Consistency Analysis...")
        try:
            img = Image.open(image_path).convert('RGB')
            Y = np.array(img)
            h, w, _ = Y.shape
            
            vectors = []
            for i in range(0, h - self.grid_size, self.grid_size):
                for j in range(0, w - self.grid_size, self.grid_size):
                    block = Y[i:i+self.grid_size, j:j+self.grid_size]
                    vec = self.estimate_illuminant_vector(block)
                    if np.sum(vec) > 0:
                        vectors.append(vec)
                        
            if len(vectors) < 2:
                return "Authentic (Consistent Light)", 1.0, 0.0
                
            global_illuminant = np.mean(vectors, axis=0)
            global_illuminant /= np.linalg.norm(global_illuminant)
            
            max_deviation = 0.0
            for vec in vectors:
                angle = self.angular_error(global_illuminant, vec)
                if angle > max_deviation:
                    max_deviation = angle
                    
            is_fake = max_deviation > self.anomaly_threshold_degrees
            confidence = max(1.0 - (max_deviation / (self.anomaly_threshold_degrees * 2)), 0.0)
            verdict = "Fake (Lighting Mismatch)" if is_fake else "Authentic (Consistent Light)"
            
            return verdict, float(confidence), max_deviation
        except Exception as e:
            print(f"[!] Lighting analysis layer failed: {e}")
            return "Inconclusive", 0.5, 0.0