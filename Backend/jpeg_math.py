import numpy as np

class AlgebraicJPEG:
    def __init__(self):
        self.grid_size = 8

    def calculate_blockiness_signal(self, Y_matrix):
        """
        Extracts spatial Block Artifact Grid (BAG) profiles using matrix differences.
        Measures structural variations across 8x8 block boundaries vs internal pixels.
        """
        Y = Y_matrix.astype(np.float32)
        h, w = Y.shape
        
        # Calculate horizontal and vertical adjacent pixel differences
        diff_h = np.abs(Y[:, 1:] - Y[:, :-1])
        diff_v = np.abs(Y[1:, :] - Y[:-1, :])
        
        # Extract 1D profiles by taking structural column/row averages
        profile_h = np.mean(diff_h, axis=0)
        profile_v = np.mean(diff_v, axis=0)
        
        return profile_h, profile_v

    def measure_grid_regularity(self, profile):
        """
        Analyzes the 1D difference profile to evaluate if the 8-pixel JPEG 
        grid periodicity is uniform (authentic) or corrupted (double-compressed/tampered).
        """
        n = len(profile)
        if n < 16:
            return 1.0
            
        # Compute variances across sub-sampled phases to isolate grid peaks
        peaks = []
        for start in range(8):
            sub_sample = profile[start::8]
            if len(sub_sample) > 1:
                peaks.append(np.var(sub_sample))
                
        if not peaks:
            return 1.0
            
        max_peak = np.max(peaks)
        mean_peak = np.mean(peaks)
        
        if mean_peak == 0:
            return 1.0
            
        return float(max_peak / mean_peak)