import numpy as np

class AlgebraicIlluminant:
    def estimate_illuminant_vector(self, block_rgb):
        """
        Implements Minkowski p=1 Norm parameters for the Grey-Edge Hypothesis,
        extracting radiometric light distributions purely through finite image derivatives.
        """
        img = block_rgb.astype(np.float32)
        grad_x = np.abs(img[:, 1:, :] - img[:, :-1, :])
        grad_y = np.abs(img[1:, :, :] - img[:-1, :, :])
        
        grad_x = np.pad(grad_x, ((0, 0), (0, 1), (0, 0)), mode='constant')
        grad_y = np.pad(grad_y, ((0, 1), (0, 0), (0, 0)), mode='constant')
        
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        illuminant_r = np.sum(gradient_magnitude[:, :, 0])
        illuminant_g = np.sum(gradient_magnitude[:, :, 1])
        illuminant_b = np.sum(gradient_magnitude[:, :, 2])
        
        illuminant_vector = np.array([illuminant_r, illuminant_g, illuminant_b])
        norm = np.linalg.norm(illuminant_vector)
        
        if norm == 0:
            return np.array([0.0, 0.0, 0.0])
        return illuminant_vector / norm

    def angular_error(self, vec1, vec2):
        if np.sum(vec1) == 0 or np.sum(vec2) == 0:
            return 0.0
        dot_product = np.clip(np.dot(vec1, vec2), -1.0, 1.0)
        return float(np.degrees(np.arccos(dot_product)))