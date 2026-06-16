import os
import tempfile
import numpy as np
from PIL import Image
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import base64
import io
import math

from prnu_engine import ForensicLibrary, AdvancedPRNU
from cfa_engine import AdvancedCFA
from quality_gate import ForensicQualityGate
from jpeg_engine import AdvancedJPEG
from illuminant_engine import AdvancedLighting
from main import combine_evidence_dst

app = Flask(__name__)
CORS(app) 

# WebSocket Engine with 50MB buffer limit
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', max_http_buffer_size=50 * 1024 * 1024)

def safe_float(val):
    try:
        f_val = float(val)
        return 0.0 if math.isnan(f_val) or math.isinf(f_val) else f_val
    except:
        return 0.0

@socketio.on('connect')
def handle_connect():
    print("[*] Frontend UI connected via WebSocket.")

@socketio.on('analyze_image')
def handle_analysis(data):
    print("[*] Image received. Starting asynchronous analysis pipeline...")
    filepath = None
    try:
        # Decode the Base64 image
        file_data = data['file_data'].split(',')[1]
        image_bytes = base64.b64decode(file_data)
        img = Image.open(io.BytesIO(image_bytes))

        # ---------------------------------------------------------
        # THE FIX: Save to the isolated Windows Temp directory 
        # so VS Code Live Server does not detect the file change.
        # ---------------------------------------------------------
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, 'ws_temp_target.jpg')
        
        if img.mode != 'RGB': img = img.convert('RGB')
        img.save(filepath, format='JPEG', quality=100)

        image_matrix = np.array(img.convert('L')).astype(np.float32)

        # Initialize Engines
        prnu = AdvancedPRNU(ForensicLibrary(folder_path='signatures'))
        cfa = AdvancedCFA()
        jpeg = AdvancedJPEG()
        lighting = AdvancedLighting()
        gate = ForensicQualityGate()

        evidence_pool = []
        results = {}

        # 1. PRNU
        emit('progress', {'step': 'Extracting Sensor Pattern Noise (PRNU)...'})
        socketio.sleep(0.1) 
        p_verdict, p_score, _ = prnu.detect_forgery(image_matrix)
        results['prnu'] = {"verdict": p_verdict, "score": safe_float(p_score), "status": "Analyzed"}
        evidence_pool.append(safe_float(p_score))

        # 2. CFA
        emit('progress', {'step': 'Estimating CFA Interpolation Grids...'})
        socketio.sleep(0.1)
        if gate.should_run_cfa(filepath):
            c_verdict, c_score, _ = cfa.detect_cfa_anomalies(image_matrix)
            results['cfa'] = {"verdict": c_verdict, "score": safe_float(c_score), "status": "Analyzed"}
            evidence_pool.append(safe_float(c_score))
        else:
            results['cfa'] = {"verdict": "Bypassed", "score": 0.5, "status": "Bypassed (Heavy Compression)"}

        # 3. JPEG
        emit('progress', {'step': 'Analyzing JPEG Block Grids...'})
        socketio.sleep(0.1)
        j_verdict, j_score, _ = jpeg.detect_dimple_artifacts(filepath)
        results['jpeg'] = {"verdict": j_verdict, "score": safe_float(j_score), "status": "Analyzed"}
        evidence_pool.append(safe_float(j_score))

        # 4. Lighting
        emit('progress', {'step': 'Calculating Illuminant Color Vectors...'})
        socketio.sleep(0.1)
        l_verdict, l_score, dev = lighting.detect_lighting_anomalies(filepath)
        results['lighting'] = {"verdict": l_verdict, "score": safe_float(l_score), "deviation": safe_float(dev), "status": "Analyzed"}
        evidence_pool.append(safe_float(l_score))

        # 5. Fusion
        emit('progress', {'step': 'Executing Dempster-Shafer Fusion...'})
        socketio.sleep(0.1)
        final_score = combine_evidence_dst(evidence_pool)
        final_verdict = "Authentic Trace" if final_score > 0.5 else "Tampered Composite"

        # Cleanup the temp file safely
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

        # Broadcast Results
        emit('analysis_complete', {
            "final_verdict": final_verdict,
            "joint_confidence": safe_float(final_score * 100),
            "breakdown": results
        })
        print("[✔] Analysis complete. Results transmitted.")

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        emit('analysis_error', {'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*55)
    print("   DEEPTRACE M.TECH WEBSOCKET SERVER ONLINE")
    print("   Ready for real-time asynchronous streaming...")
    print("="*55 + "\n")
    socketio.run(app, port=5000, debug=True)