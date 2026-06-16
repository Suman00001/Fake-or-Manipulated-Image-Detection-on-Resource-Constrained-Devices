import numpy as np
from scipy.signal import wiener
import warnings

class AlgebraicPRNU:
    def __init__(self):
        self.window_size = (3, 3)

    def apply_wiener_filter(self, Y):
        Y_double = Y.astype(np.float64)
        
        # Suppress SciPy's internal divide-by-zero warnings on flat images
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            D_Y = wiener(Y_double, self.window_size)
        
        # Fix the NaN crash: If a pixel block is perfectly flat, wiener outputs NaN.
        # We replace NaN with the original pixel so the noise residual (W = Y - D_Y) safely becomes 0.
        np.copyto(D_Y, Y_double, where=np.isnan(D_Y))
        
        return D_Y.astype(np.float32)

    def extract_residual(self, Y_matrix):
        Y = Y_matrix.astype(np.float32)
        D_Y = self.apply_wiener_filter(Y)
        W = Y - D_Y
        
        W_mean = np.mean(W)
        W = W - W_mean
        return W

    def calculate_correlation(self, W_test, K_reference):
        w_vec = W_test.flatten()
        k_vec = K_reference.flatten()
        
        w_mean = np.mean(w_vec)
        k_mean = np.mean(k_vec)
        
        w_dev = w_vec - w_mean
        k_dev = k_vec - k_mean
        
        covariance = np.sum(w_dev * k_dev)
        w_variance = np.sum(w_dev ** 2)
        k_variance = np.sum(k_dev ** 2)
        
        if w_variance == 0 or k_variance == 0:
            return 0.0
            
        denominator = np.sqrt(w_variance * k_variance)
        
        # Ensure we don't output NaN for perfectly flat blocks
        rho = covariance / denominator
        return 0.0 if np.isnan(rho) else float(rho)