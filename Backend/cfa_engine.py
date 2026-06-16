import numpy as np
from cfa_math import AlgebraicCFA

class AdvancedCFA(AlgebraicCFA):
    def __init__(self):
        super().__init__()
        self.block_size = 64

    def detect_cfa_anomalies(self, image_matrix):
        print("[*] Running CFA Pattern Inconsistency Analysis...")
        error_matrix = self.estimate_cfa_error(image_matrix)
        h, w = error_matrix.shape
        
        blocks_h = h // self.block_size
        blocks_w = w // self.block_size
        heatmap = np.zeros((blocks_h, blocks_w))
        
        for i in range(blocks_h):
            for j in range(blocks_w):
                row_start = i * self.block_size
                col_start = j * self.block_size
                block = error_matrix[row_start:row_start+self.block_size, col_start:col_start+self.block_size]
                heatmap[i, j] = np.var(block)
                
        global_variance = np.mean(heatmap)
        max_variance = np.max(heatmap) if heatmap.size > 0 else 0.0
        
        if global_variance == 0:
            return "Fake", 0.0, heatmap
            
        is_fake = max_variance > (global_variance * 1.5)
        confidence = global_variance / max_variance if max_variance > 0 else 1.0
        verdict = "Fake" if is_fake else "Authentic"
        return verdict, float(confidence), heatmap