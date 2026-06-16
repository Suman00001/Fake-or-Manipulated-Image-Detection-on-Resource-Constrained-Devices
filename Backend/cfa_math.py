import numpy as np

class AlgebraicCFA:
    def estimate_cfa_error(self, Y):
        """
        Implements a lightweight gradient edge-directed estimator 
        to track reconstruction errors within the Bayer interpolation plane.
        """
        Y = Y.astype(np.float32)
        h, w = Y.shape
        error_matrix = np.zeros_like(Y)
        
        # Fast 1D matrix finite spatial gradients
        grad_h = np.abs(Y[:, 2:] - Y[:, :-2])
        grad_v = np.abs(Y[2:, :] - Y[:-2, :])
        
        grad_h = np.pad(grad_h, ((0, 0), (1, 1)), mode='edge')
        grad_v = np.pad(grad_v, ((1, 1), (0, 0)), mode='edge')
        
        for i in range(1, h-1):
            for j in range(1, w-1):
                if grad_h[i, j] < grad_v[i, j]:
                    estimate = (Y[i, j-1] + Y[i, j+1]) / 2.0
                else:
                    estimate = (Y[i-1, j] + Y[i+1, j]) / 2.0
                error_matrix[i, j] = np.abs(Y[i, j] - estimate)
                
        return error_matrix