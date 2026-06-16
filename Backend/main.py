import os
import numpy as np
from PIL import Image
from prnu_engine import ForensicLibrary, AdvancedPRNU
from cfa_engine import AdvancedCFA
from quality_gate import ForensicQualityGate
from jpeg_engine import AdvancedJPEG
from illuminant_engine import AdvancedLighting

def load_image_as_matrix(path):
    try:
        img = Image.open(path).convert('L')
        return np.array(img).astype(np.float32)
    except Exception as e:
        print(f"[!] Image matrix read error: {e}")
        return None

def combine_evidence_dst(evidences):
    """
    Applies Dempster's Rule of Combination sequentially across N forensic dimensions 
    to yield a reliable, multi-source probability vector.
    """
    if not evidences:
        return 0.5
        
    m_A = evidences[0]
    m_F = 1.0 - evidences[0]
    
    for next_evidence in evidences[1:]:
        m2_A = next_evidence
        m2_F = 1.0 - next_evidence
        
        conflict = (m_A * m2_F) + (m_F * m2_A)
        normalization_scale = 1.0 - conflict
        
        if normalization_scale == 0:
            continue
            
        m_A = (m_A * m2_A) / normalization_scale
        m_F = (m_F * m2_F) / normalization_scale
        
    total_mass = m_A + m_F
    return float(m_A / total_mass) if total_mass > 0 else 0.5

def run_forensic_pipeline(image_path, device_label=None):
    print(f"\n{'='*60}\nLAUNCHING INTEGRATED AUTOMATED FORENSIC PIPELINE\nTarget File: {image_path}\n{'='*60}")
    
    if not os.path.exists(image_path):
        print("[!] Aborting. Please insert a valid target photo array.")
        return

    # Initialize Engine Pool
    prnu_engine = AdvancedPRNU(ForensicLibrary(folder_path='signatures'))
    cfa_engine = AdvancedCFA()
    jpeg_engine = AdvancedJPEG()
    lighting_engine = AdvancedLighting()
    quality_gate = ForensicQualityGate()
    
    image_matrix = load_image_as_matrix(image_path)
    if image_matrix is None:
        return

    evidence_pool = []

    # Channel 1: Sensor PRNU
    p_verdict, p_score, _ = prnu_engine.detect_forgery(image_matrix, metadata=device_label)
    print(f"    -> PRNU Channel Analysis  : {p_verdict} (Confidence: {p_score:.4f})")
    evidence_pool.append(p_score)

    # Channel 2: CFA Anomaly Gate Check
    if quality_gate.should_run_cfa(image_path):
        c_verdict, c_score, _ = cfa_engine.detect_cfa_anomalies(image_matrix)
        print(f"    -> CFA Grid Analysis      : {c_verdict} (Confidence: {c_score:.4f})")
        evidence_pool.append(c_score)

    # Channel 3: Frequency-Domain JPEG Dimples
    if image_path.lower().endswith(('.jpg', '.jpeg')):
        j_verdict, j_score, _ = jpeg_engine.detect_dimple_artifacts(image_path)
        print(f"    -> JPEG Format Analysis   : {j_verdict} (Confidence: {j_score:.4f})")
        evidence_pool.append(j_score)

    # Channel 4: Automated Scene Physics (Radiometric Light)
    l_verdict, l_score, dev = lighting_engine.detect_lighting_anomalies(image_path)
    print(f"    -> Radiometric Light Analysis: {l_verdict} (Confidence: {l_score:.4f}, Max Dev: {dev:.2f}°)")
    evidence_pool.append(l_score)

    # Multi-Evidence Statistics Fusion (DST)
    final_joint_probability = combine_evidence_dst(evidence_pool)
    final_verdict = "AUTHENTIC IMAGE TRACE" if final_joint_probability > 0.5 else "TAMPERED / FORGED COMPOSITE"

    print(f"\n{'='*60}\n >>> CONSOLIDATED REPORT VERDICT : {final_verdict}")
    print(f" >>> MULTI-SOURCE SYSTEM CONFIDENCE: {final_joint_probability:.4f}\n{'='*60}\n")

if __name__ == "__main__":
    target_file = "original.jpg"
    if os.path.exists(target_file):
        # Pass a metadata hint if matching signature exists in signatures/ folder, else set to None
        run_forensic_pipeline(target_file, device_label=None)
    else:
        print(f"[*] Pipeline ready. Place a sample file named '{target_file}' into the directory to test.")