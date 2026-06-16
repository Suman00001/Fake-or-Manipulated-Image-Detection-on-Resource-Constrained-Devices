import numpy as np
import os
from prnu_math import AlgebraicPRNU

class ForensicLibrary:
    def __init__(self, folder_path='signatures'):
        self.folder_path = folder_path
        self.fingerprints = {}
        self.load_library()

    def load_library(self):
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)
            return

        for filename in os.listdir(self.folder_path):
            if filename.endswith('.npy'):
                device_name = filename.replace('.npy', '')
                path = os.path.join(self.folder_path, filename)
                self.fingerprints[device_name] = np.load(path)
        print(f"[*] Forensic Library Loaded: {len(self.fingerprints)} devices ready.")

    def get_template(self, device_model):
        return self.fingerprints.get(device_model, None)

class AdvancedPRNU(AlgebraicPRNU):
    def __init__(self, library):
        super().__init__()
        self.library = library
        self.block_size = 64

    def detect_forgery(self, image_matrix, metadata=None):
        W = self.extract_residual(image_matrix)
        template = self.library.get_template(metadata) if metadata else None

        if template is not None:
            print(f"[*] Signature Match Found for: {metadata}. Running Correlation...")
            return self.library_check(W, template)
        else:
            print("[!] No matching metadata. Initializing Blind Forgery Check...")
            return self.blind_check(W)

    def library_check(self, W, K_ref):
        """
        Dynamically crops overlapping dimensions between arbitrary image sizes 
        and stored fingerprints to guarantee error-free matrix operations.
        """
        h_w, w_w = W.shape
        h_k, w_k = K_ref.shape
        
        min_h = min(h_w, h_k)
        min_w = min(w_w, w_k)
        
        W_cropped = W[:min_h, :min_w]
        K_cropped = K_ref[:min_h, :min_w]
        
        global_rho = self.calculate_correlation(W_cropped, K_cropped)
        verdict = "Authentic" if global_rho > 0.05 else "Fake"
        return verdict, max(0.0, min(global_rho * 10, 1.0)), None

    def blind_check(self, W):
        h, w = W.shape
        heatmap = np.zeros((h // self.block_size, w // self.block_size))
        K_pseudo = W.copy()

        for i in range(0, h - self.block_size, self.block_size):
            for j in range(0, w - self.block_size, self.block_size):
                block = W[i:i+self.block_size, j:j+self.block_size]
                ref = K_pseudo[i:i+self.block_size, j:j+self.block_size]
                rho = self.calculate_correlation(block, ref)
                heatmap[i//self.block_size, j//self.block_size] = rho
        
        mean_rho = np.mean(heatmap) if heatmap.size > 0 else 0.0
        is_fake = np.any(heatmap < 0.95)
        verdict = "Fake" if is_fake else "Authentic"
        return verdict, float(mean_rho), heatmap