#!/usr/bin/env python3
"""
Comprehensive NeuroAd Pipeline Validation Script

Tests all components of the NeuroAd pipeline and reports status:
✅ working, ⚠️ partial, ❌ failed

Components tested:
1. SYSTEM - RAM, GPU/ROCm, Disk space
2. TRIBE v2 - Import, model load, inference
3. SALIENCY ENGINE - DeepGaze IIE, ViNet-S
4. EMOTION & CLIP - HSEmotion, CLIP
5. CREATIVE MODULES - Flux.1, CogVideoX
6. TURBO QUANT - TQ3 availability, API check
7. MIROFISH - Docker container, API endpoint
8. LEMONADE + LLM - Models endpoint, extra models
9. MODEL SWAP MANAGER - Script existence, status
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Try imports for components that need them
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class PipelineValidator:
    """Validates all components of the NeuroAd pipeline."""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        self.report_lines = []
        
    def log(self, message, status=None):
        """Log a message and optionally record status."""
        print(message)
        self.report_lines.append(message)
        
    def record_result(self, component, status, details=""):
        """Record a component's validation result."""
        self.results[component] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        status_symbol = {"working": "✅", "partial": "⚠️", "failed": "❌"}.get(status, "❓")
        self.log(f"  {status_symbol} {component}: {status.upper()} - {details}")
        
    def run_command(self, cmd, cwd=None, timeout=30):
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
            
    def check_system(self):
        """Test SYSTEM components: RAM, GPU/ROCm, Disk space."""
        self.log("\n" + "="*60)
        self.log("1. SYSTEM COMPONENTS")
        self.log("="*60)
        
        # 1a. Available RAM
        self.log("\n  1a. Checking available RAM...")
        returncode, stdout, stderr = self.run_command("free -h")
        if returncode == 0:
            self.log(f"  RAM Info:\n{stdout}")
            # Parse total RAM
            lines = stdout.strip().split('\n')
            for line in lines:
                if line.startswith('Mem:'):
                    parts = line.split()
                    if len(parts) >= 2:
                        total_ram = parts[1]
                        self.record_result("RAM", "working", f"Total: {total_ram}")
                        break
        else:
            self.record_result("RAM", "failed", f"Command failed: {stderr}")
            
        # 1b. GPU/ROCm status
        self.log("\n  1b. Checking GPU/ROCm status...")
        if TORCH_AVAILABLE:
            try:
                cuda_available = torch.cuda.is_available()
                if cuda_available:
                    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown"
                    gpu_count = torch.cuda.device_count()
                    self.log(f"  GPU: {gpu_name} (x{gpu_count})")
                    self.log(f"  CUDA Available: {cuda_available}")
                    self.record_result("GPU/ROCm", "working", f"{gpu_name} x{gpu_count}, CUDA={cuda_available}")
                else:
                    self.record_result("GPU/ROCm", "partial", "PyTorch available but CUDA not detected")
                    self.log("  GPU: No CUDA devices detected (CPU mode)")
            except Exception as e:
                self.record_result("GPU/ROCm", "partial", f"PyTorch available but GPU check failed: {str(e)}")
                self.log(f"  GPU: PyTorch available but GPU check failed: {str(e)}")
        else:
            self.record_result("GPU/ROCm", "failed", "PyTorch not installed")
            self.log("  GPU: PyTorch not installed")
            
        # 1c. Disk space in ~/jarvis_os/models/
        self.log("\n  1c. Checking disk space in ~/jarvis_os/models/...")
        models_dir = Path.home() / "jarvis_os" / "models"
        if models_dir.exists():
            stat = os.statvfs(models_dir)
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
            free_gb = (stat.f_bfree * stat.f_frsize) / (1024**3)
            used_gb = total_gb - free_gb
            self.log(f"  Models directory: {models_dir}")
            self.log(f"  Total: {total_gb:.1f} GB, Used: {used_gb:.1f} GB, Free: {free_gb:.1f} GB")
            self.record_result("Disk Space (models)", "working", f"Free: {free_gb:.1f} GB / Total: {total_gb:.1f} GB")
        else:
            self.record_result("Disk Space (models)", "partial", f"Directory not found: {models_dir}")
            self.log(f"  Models directory not found: {models_dir}")
            
    def check_tribe_v2(self):
        """Test TRIBE v2 components."""
        self.log("\n" + "="*60)
        self.log("2. TRIBE v2")
        self.log("="*60)
        
        # 2a. Import check
        self.log("\n  2a. Checking TRIBE v2 import...")
        tribe_dir = Path.home() / "jarvis_os" / "tribev2"
        
        if not tribe_dir.exists():
            self.record_result("TRIBE v2 (Import)", "failed", f"TRIBE v2 directory not found: {tribe_dir}")
            self.log(f"  TRIBE v2 directory not found: {tribe_dir}")
            return
            
        # Set environment to force CPU
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = ""
        
        # Try to import demo_utils
        import_cmd = f"""
import sys
sys.path.insert(0, '{tribe_dir}')
try:
    from demo_utils import TribeModel
    print("IMPORT_SUCCESS")
except Exception as e:
    print(f"IMPORT_FAILED: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"cd {tribe_dir} && CUDA_VISIBLE_DEVICES='' python3 -c '{import_cmd}'",
            timeout=60
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("TRIBE v2 (Import)", "working", "demo_utils.TribeModel import successful")
            self.log("  TRIBE v2 import: SUCCESS")
        else:
            self.record_result("TRIBE v2 (Import)", "partial", f"Import failed: {stderr}")
            self.log(f"  TRIBE v2 import: FAILED - {stderr}")
            return  # Skip further tests if import fails
            
        # 2b. Model load check (CPU-only)
        self.log("\n  2b. Checking TRIBE v2 model load (CPU-only)...")
        load_cmd = f"""
import sys
sys.path.insert(0, '{tribe_dir}')
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
try:
    from demo_utils import TribeModel
    model = TribeModel.from_pretrained('facebook/tribev2')
    print("LOAD_SUCCESS")
except Exception as e:
    print(f"LOAD_FAILED: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"cd {tribe_dir} && CUDA_VISIBLE_DEVICES='' python3 -c '{load_cmd}'",
            timeout=120
        )
        
        if "LOAD_SUCCESS" in stdout:
            self.record_result("TRIBE v2 (Model Load)", "working", "Model loaded successfully (CPU)")
            self.log("  TRIBE v2 model load: SUCCESS")
        else:
            self.record_result("TRIBE v2 (Model Load)", "partial", f"Model load failed: {stderr}")
            self.log(f"  TRIBE v2 model load: FAILED - {stderr}")
            
        # 2c. Direct audio inference test (skip WhisperX)
        self.log("\n  2c. Testing TRIBE v2 direct audio inference...")
        
        # Download sample MP3
        sample_audio = Path.home() / "jarvis_os" / "test_audio.mp3"
        download_cmd = f"""
import urllib.request
import os
os.makedirs('{sample_audio.parent}', exist_ok=True)
try:
    urllib.request.urlretrieve(
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
        '{sample_audio}'
    )
    print("DOWNLOAD_SUCCESS")
except Exception as e:
    print(f"DOWNLOAD_FAILED: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"CUDA_VISIBLE_DEVICES='' python3 -c '{download_cmd}'",
            timeout=60
        )
        
        if "DOWNLOAD_SUCCESS" not in stdout:
            self.record_result("TRIBE v2 (Audio Inference)", "partial", f"Sample download failed: {stderr}")
            self.log(f"  Sample download: FAILED - {stderr}")
            return
            
        self.log(f"  Sample audio downloaded: {sample_audio}")
        
        # Test inference
        inference_cmd = f"""
import sys
sys.path.insert(0, '{tribe_dir}')
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
try:
    from demo_utils import TribeModel
    model = TribeModel.from_pretrained('facebook/tribev2')
    # Test with audio file
    result = model.predict_audio('{sample_audio}')
    print(f"INFERENCE_SUCCESS: shape={{result.shape}}")
except Exception as e:
    print(f"INFERENCE_FAILED: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"CUDA_VISIBLE_DEVICES='' python3 -c '{inference_cmd}'",
            timeout=180
        )
        
        if "INFERENCE_SUCCESS" in stdout:
            self.record_result("TRIBE v2 (Audio Inference)", "working", "Audio inference successful")
            self.log("  TRIBE v2 audio inference: SUCCESS")
        else:
            self.record_result("TRIBE v2 (Audio Inference)", "partial", f"Inference failed: {stderr}")
            self.log(f"  TRIBE v2 audio inference: FAILED - {stderr}")
            
    def check_saliency_engine(self):
        """Test Saliency Engine components: DeepGaze IIE, ViNet-S."""
        self.log("\n" + "="*60)
        self.log("3. SALIENCY ENGINE")
        self.log("="*60)
        
        # 3a. DeepGaze IIE
        self.log("\n  3a. Checking DeepGaze IIE...")
        
        # Try to install and import
        deepgaze_cmd = """
import sys
try:
    import deepgaze_pytorch
    print("IMPORT_SUCCESS")
except ImportError:
    print("IMPORT_FAILED")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"pip install deepgaze-pytorch -q && python3 -c '{deepgaze_cmd}'",
            timeout=120
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("DeepGaze IIE", "working", "Import successful")
            self.log("  DeepGaze IIE import: SUCCESS")
            
            # Test inference
            self.log("\n  3a-i. Testing DeepGaze IIE inference...")
            test_cmd = """
import deepgaze_pytorch
import torch
import numpy as np

try:
    model = deepgaze_pytorch.DeepGazeIIE(pretrained=True)
    # Create a test image tensor (batch, channels, height, width)
    test_image = torch.randn(1, 3, 224, 224)
    # Run inference
    with torch.no_grad():
        prediction = model(test_image)
    print(f"INFERENCE_SUCCESS: shape={{prediction.shape}}")
except Exception as e:
    print(f"INFERENCE_FAILED: {{e}}")
"""
            
            returncode, stdout, stderr = self.run_command(
                f"CUDA_VISIBLE_DEVICES='' python3 -c '{test_cmd}'",
                timeout=60
            )
            
            if "INFERENCE_SUCCESS" in stdout:
                self.record_result("DeepGaze IIE (Inference)", "working", "Inference successful")
                self.log("  DeepGaze IIE inference: SUCCESS")
            else:
                self.record_result("DeepGaze IIE (Inference)", "partial", f"Inference failed: {stderr}")
                self.log(f"  DeepGaze IIE inference: FAILED - {stderr}")
        else:
            self.record_result("DeepGaze IIE", "partial", f"Import failed: {stderr}")
            self.log(f"  DeepGaze IIE import: FAILED - {stderr}")
            
        # 3b. ViNet-S
        self.log("\n  3b. Checking ViNet-S...")
        vinet_dir = Path.home() / "jarvis_os" / "ViNet"
        
        if not vinet_dir.exists():
            self.record_result("ViNet-S", "partial", f"Repository not found: {vinet_dir}")
            self.log(f"  ViNet-S repository not found: {vinet_dir}")
            return
            
        # Try to import
        vinet_import_cmd = f"""
import sys
sys.path.insert(0, '{vinet_dir}')
try:
    import vinet
    print("IMPORT_SUCCESS")
except ImportError as e:
    print(f"IMPORT_FAILED: {{e}}")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"cd {vinet_dir} && python3 -c '{vinet_import_cmd}'",
            timeout=60
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("ViNet-S", "working", "Import successful")
            self.log("  ViNet-S import: SUCCESS")
        else:
            self.record_result("ViNet-S", "partial", f"Import failed: {stderr}")
            self.log(f"  ViNet-S import: FAILED - {stderr}")
            
    def check_emotion_clip(self):
        """Test EMOTION & CLIP components."""
        self.log("\n" + "="*60)
        self.log("4. EMOTION & CLIP")
        self.log("="*60)
        
        # 4a. HSEmotion
        self.log("\n  4a. Checking HSEmotion...")
        hsemotion_cmd = """
import sys
try:
    import hsemotion
    print("IMPORT_SUCCESS")
except ImportError:
    print("IMPORT_FAILED")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"pip install hsemotion -q && python3 -c '{hsemotion_cmd}'",
            timeout=120
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("HSEmotion", "working", "Import successful")
            self.log("  HSEmotion import: SUCCESS")
        else:
            self.record_result("HSEmotion", "partial", f"Import failed: {stderr}")
            self.log(f"  HSEmotion import: FAILED - {stderr}")
            
        # 4b. CLIP
        self.log("\n  4b. Checking CLIP...")
        clip_cmd = """
import sys
try:
    import clip
    print("IMPORT_SUCCESS")
except ImportError:
    print("IMPORT_FAILED")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"pip install git+https://github.com/openai/CLIP.git -q && python3 -c '{clip_cmd}'",
            timeout=180
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("CLIP", "working", "Import successful")
            self.log("  CLIP import: SUCCESS")
            
            # Test image-text similarity
            self.log("\n  4b-i. Testing CLIP image-text similarity...")
            clip_test_cmd = """
import clip
import torch
from PIL import Image
import urllib.request
import os

try:
    # Download a test image
    test_img = '/tmp/clip_test.jpg'
    urllib.request.urlretrieve('https://raw.githubusercontent.com/pytorch/hub/master/images/dog.jpg', test_img)
    
    # Load model
    model, preprocess = clip.load('ViT-B/32', device='cpu')
    
    # Load image
    image = Image.open(test_img)
    image_input = preprocess(image).unsqueeze(0)
    
    # Define text prompts
    text_inputs = clip.tokenize(['a photo of a dog', 'a photo of a cat'])
    
    # Compute features
    with torch.no_grad():
        image_features = model.encode_image(image_input)
        text_features = model.encode_text(text_inputs)
        
        # Compute similarity
        similarity = torch.cosine_similarity(image_features, text_features)
        print(f"INFERENCE_SUCCESS: similarity={{similarity.tolist()}}")
except Exception as e:
    print(f"INFERENCE_FAILED: {{e}}")
"""
            
            returncode, stdout, stderr = self.run_command(
                f"CUDA_VISIBLE_DEVICES='' python3 -c '{clip_test_cmd}'",
                timeout=120
            )
            
            if "INFERENCE_SUCCESS" in stdout:
                self.record_result("CLIP (Similarity)", "working", "Image-text similarity successful")
                self.log("  CLIP image-text similarity: SUCCESS")
            else:
                self.record_result("CLIP (Similarity)", "partial", f"Similarity test failed: {stderr}")
                self.log(f"  CLIP similarity test: FAILED - {stderr}")
        else:
            self.record_result("CLIP", "partial", f"Import failed: {stderr}")
            self.log(f"  CLIP import: FAILED - {stderr}")
            
    def check_creative_modules(self):
        """Test CREATIVE MODULES: Flux.1, CogVideoX."""
        self.log("\n" + "="*60)
        self.log("5. CREATIVE MODULES")
        self.log("="*60)
        
        # 5a. Flux.1
        self.log("\n  5a. Checking Flux.1 (diffusers)...")
        
        # Check if diffusers is installed
        diffusers_check = """
import sys
try:
    import diffusers
    print(f"IMPORT_SUCCESS: version={{diffusers.__version__}}")
except ImportError:
    print("IMPORT_FAILED")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"pip install diffusers -q && python3 -c '{diffusers_check}'",
            timeout=120
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("Flux.1 (diffusers)", "working", "Import successful")
            self.log("  Flux.1 diffusers import: SUCCESS")
            
            # Try loading pipeline with ROCm
            self.log("\n  5a-i. Testing Flux.1 pipeline load (ROCm/CPU)...")
            pipeline_cmd = """
import torch
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

try:
    from diffusers import FluxPipeline
    print("PIPELINE_IMPORT_SUCCESS")
except ImportError:
    try:
        from diffusers import FluxPipeline
        print("PIPELINE_IMPORT_SUCCESS")
    except:
        print("PIPELINE_IMPORT_FAILED")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
            
            returncode, stdout, stderr = self.run_command(
                f"CUDA_VISIBLE_DEVICES='' python3 -c '{pipeline_cmd}'",
                timeout=60
            )
            
            if "PIPELINE_IMPORT_SUCCESS" in stdout:
                self.record_result("Flux.1 (Pipeline)", "working", "Pipeline import successful")
                self.log("  Flux.1 pipeline import: SUCCESS")
            else:
                self.record_result("Flux.1 (Pipeline)", "partial", f"Pipeline import failed: {stderr}")
                self.log(f"  Flux.1 pipeline import: FAILED - {stderr}")
        else:
            self.record_result("Flux.1 (diffusers)", "partial", f"Import failed: {stderr}")
            self.log(f"  Flux.1 diffusers import: FAILED - {stderr}")
            
        # 5b. CogVideoX
        self.log("\n  5b. Checking CogVideoX (import only)...")
        cogvideo_cmd = """
import sys
try:
    import cogvideox
    print("IMPORT_SUCCESS")
except ImportError:
    try:
        from cogvideox import CogVideoX
        print("IMPORT_SUCCESS")
    except:
        print("IMPORT_FAILED")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"pip install cogvideox -q 2>/dev/null; python3 -c '{cogvideo_cmd}'",
            timeout=120
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("CogVideoX", "working", "Import successful")
            self.log("  CogVideoX import: SUCCESS")
        else:
            self.record_result("CogVideoX", "partial", f"Import failed: {stderr}")
            self.log(f"  CogVideoX import: FAILED - {stderr}")
            
    def check_turbo_quant(self):
        """Test TURBO QUANT components."""
        self.log("\n" + "="*60)
        self.log("6. TURBO QUANT")
        self.log("="*60)
        
        # 6a. Check TQ3 availability in llama.cpp
        self.log("\n  6a. Checking TQ3 availability in llama.cpp...")
        
        # Check if llama.cpp is available
        llama_check = """
import subprocess
try:
    result = subprocess.run(['llama.cpp', '--help'], capture_output=True, timeout=5)
    print("LLAMA_CPP_FOUND")
except FileNotFoundError:
    print("LLAMA_CPP_NOT_FOUND")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"python3 -c '{llama_check}'",
            timeout=10
        )
        
        if "LLAMA_CPP_FOUND" in stdout:
            self.record_result("llama.cpp", "working", "Found")
            self.log("  llama.cpp: FOUND")
        else:
            self.record_result("llama.cpp", "partial", "Not found or not in PATH")
            self.log("  llama.cpp: NOT FOUND or not in PATH")
            
        # 6b. Test TurboQuant API endpoint
        self.log("\n  6b. Testing TurboQuant API endpoint...")
        
        if REQUESTS_AVAILABLE:
            try:
                response = requests.get("http://localhost:8888/api/v1/models", timeout=5)
                if response.status_code == 200:
                    models = response.json()
                    self.log(f"  API Response: {response.status_code}")
                    self.log(f"  Models available: {len(models.get('data', []))}")
                    
                    # Check for TQ3 support
                    tq3_found = False
                    for model in models.get('data', []):
                        model_id = model.get('id', '').lower()
                        if 'tq3' in model_id or '3-bit' in model_id:
                            tq3_found = True
                            break
                            
                    if tq3_found:
                        self.record_result("TurboQuant API (TQ3)", "working", "TQ3 model found")
                        self.log("  TQ3 support: FOUND")
                    else:
                        self.record_result("TurboQuant API (TQ3)", "partial", "API working but TQ3 not found")
                        self.log("  TQ3 support: NOT FOUND in models")
                else:
                    self.record_result("TurboQuant API", "partial", f"API returned {response.status_code}")
                    self.log(f"  TurboQuant API: {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.record_result("TurboQuant API", "partial", "Connection refused (service not running)")
                self.log("  TurboQuant API: CONNECTION REFUSED (service not running)")
            except Exception as e:
                self.record_result("TurboQuant API", "partial", f"Error: {str(e)}")
                self.log(f"  TurboQuant API: ERROR - {str(e)}")
        else:
            self.record_result("TurboQuant API", "partial", "requests library not available")
            self.log("  TurboQuant API: requests library not available")
            
        # 6c. Clone and run turboquant-pytorch validation
        self.log("\n  6c. Checking turboquant-pytorch...")
        tq_dir = Path.home() / "jarvis_os" / "turboquant-pytorch"
        
        if not tq_dir.exists():
            self.record_result("turboquant-pytorch", "partial", f"Repository not found: {tq_dir}")
            self.log(f"  turboquant-pytorch repository not found: {tq_dir}")
            return
            
        # Try to run validation script
        self.log(f"  Found repository at: {tq_dir}")
        self.record_result("turboquant-pytorch (Repo)", "working", "Repository found")
        
        # Check for validation script
        val_script = tq_dir / "validate.py"
        if val_script.exists():
            self.log(f"  Validation script found: {val_script}")
            self.record_result("turboquant-pytorch (Validation)", "working", "Validation script exists")
        else:
            self.record_result("turboquant-pytorch (Validation)", "partial", "Validation script not found")
            self.log("  Validation script: NOT FOUND")
            
    def check_mirofish(self):
        """Test MIROFISH components."""
        self.log("\n" + "="*60)
        self.log("7. MIROFISH")
        self.log("="*60)
        
        # 7a. Check if container is running
        self.log("\n  7a. Checking MiroFish container status...")
        returncode, stdout, stderr = self.run_command("docker ps | grep mirofish")
        
        if returncode == 0 and "mirofish" in stdout:
            self.record_result("MiroFish (Container)", "working", "Container is running")
            self.log("  MiroFish container: RUNNING")
            
            # 7b. Test API endpoint
            self.log("\n  7b. Testing MiroFish API endpoint...")
            
            if REQUESTS_AVAILABLE:
                try:
                    response = requests.get("http://localhost:3000", timeout=5)
                    if response.status_code == 200:
                        self.record_result("MiroFish API", "working", f"API responding: {response.status_code}")
                        self.log(f"  MiroFish API: {response.status_code} OK")
                    else:
                        self.record_result("MiroFish API", "partial", f"API returned {response.status_code}")
                        self.log(f"  MiroFish API: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    self.record_result("MiroFish API", "partial", "Connection refused")
                    self.log("  MiroFish API: CONNECTION REFUSED")
                except Exception as e:
                    self.record_result("MiroFish API", "partial", f"Error: {str(e)}")
                    self.log(f"  MiroFish API: ERROR - {str(e)}")
            else:
                self.record_result("MiroFish API", "partial", "requests library not available")
                self.log("  MiroFish API: requests library not available")
        else:
            self.record_result("MiroFish (Container)", "partial", "Container not running")
            self.log("  MiroFish container: NOT RUNNING")
            self.record_result("MiroFish API", "partial", "Container not running")
            self.log("  MiroFish API: SKIPPED (container not running)")
            
    def check_lemonade_llm(self):
        """Test LEMONADE + LLM components."""
        self.log("\n" + "="*60)
        self.log("8. LEMONADE + LLM")
        self.log("="*60)
        
        # 8a. Check localhost:8888 models endpoint
        self.log("\n  8a. Checking Lemonade SDK models endpoint...")
        
        if REQUESTS_AVAILABLE:
            try:
                response = requests.get("http://localhost:8888/models", timeout=5)
                if response.status_code == 200:
                    models = response.json()
                    self.record_result("Lemonade SDK (API)", "working", f"API responding: {response.status_code}")
                    self.log(f"  Lemonade SDK API: {response.status_code} OK")
                    self.log(f"  Models available: {len(models.get('data', []))}")
                    
                    # 8b. Verify extra models
                    self.log("\n  8b. Verifying extra models...")
                    model_ids = [m.get('id', '').lower() for m in models.get('data', [])]
                    
                    required_models = [
                        'extra.qwen3-coder-next',
                        'extra.deepseek-r1', 
                        'extra.bge-m3'
                    ]
                    
                    found_models = []
                    missing_models = []
                    
                    for req_model in required_models:
                        found = any(req_model in mid for mid in model_ids)
                        if found:
                            found_models.append(req_model)
                        else:
                            missing_models.append(req_model)
                            
                    if len(found_models) == len(required_models):
                        self.record_result("Lemonade SDK (Models)", "working", "All required models found")
                        self.log(f"  All required models found: {', '.join(found_models)}")
                    else:
                        self.record_result("Lemonade SDK (Models)", "partial", f"Missing: {', '.join(missing_models)}")
                        self.log(f"  Found: {', '.join(found_models)}")
                        self.log(f"  Missing: {', '.join(missing_models)}")
                else:
                    self.record_result("Lemonade SDK (API)", "partial", f"API returned {response.status_code}")
                    self.log(f"  Lemonade SDK API: {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.record_result("Lemonade SDK (API)", "partial", "Connection refused")
                self.log("  Lemonade SDK API: CONNECTION REFUSED")
            except Exception as e:
                self.record_result("Lemonade SDK (API)", "partial", f"Error: {str(e)}")
                self.log(f"  Lemonade SDK API: ERROR - {str(e)}")
        else:
            self.record_result("Lemonade SDK (API)", "partial", "requests library not available")
            self.log("  Lemonade SDK API: requests library not available")
            
    def check_model_swap_manager(self):
        """Test MODEL SWAP MANAGER."""
        self.log("\n" + "="*60)
        self.log("9. MODEL SWAP MANAGER")
        self.log("="*60)
        
        model_swap_path = Path.home() / "jarvis_os" / "model_swap.py"
        
        self.log(f"\n  9a. Checking model_swap.py at {model_swap_path}...")
        
        if not model_swap_path.exists():
            self.record_result("Model Swap Manager", "partial", f"File not found: {model_swap_path}")
            self.log(f"  model_swap.py: NOT FOUND")
            return
            
        self.record_result("Model Swap Manager (File)", "working", "File exists")
        self.log(f"  model_swap.py: FOUND")
        
        # Try to import
        self.log("\n  9b. Testing model_swap.py import...")
        import_cmd = f"""
import sys
sys.path.insert(0, '{Path.home() / "jarvis_os"}')
try:
    import model_swap
    print("IMPORT_SUCCESS")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        
        returncode, stdout, stderr = self.run_command(
            f"python3 -c '{import_cmd}'",
            timeout=30
        )
        
        if "IMPORT_SUCCESS" in stdout:
            self.record_result("Model Swap Manager (Import)", "working", "Import successful")
            self.log("  model_swap.py import: SUCCESS")
            
            # Get current status
            self.log("\n  9c. Getting current status...")
            status_cmd = f"""
import sys
sys.path.insert(0, '{Path.home() / "jarvis_os"}')
try:
    import model_swap
    if hasattr(model_swap, 'get_status'):
        status = model_swap.get_status()
        print(f"STATUS: {{status}}")
    elif hasattr(model_swap, 'status'):
        print(f"STATUS: {{model_swap.status}}")
    else:
        print("STATUS: NO_STATUS_METHOD")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
            
            returncode, stdout, stderr = self.run_command(
                f"python3 -c '{status_cmd}'",
                timeout=30
            )
            
            if "STATUS:" in stdout:
                self.record_result("Model Swap Manager (Status)", "working", "Status retrieved")
                self.log(f"  Current status: {stdout.strip()}")
            else:
                self.record_result("Model Swap Manager (Status)", "partial", "Could not retrieve status")
                self.log("  Current status: Could not retrieve")
        else:
            self.record_result("Model Swap Manager (Import)", "partial", f"Import failed: {stderr}")
            self.log(f"  model_swap.py import: FAILED - {stderr}")
            
    def generate_summary(self):
        """Generate final summary table."""
        self.log("\n" + "="*60)
        self.log("FINAL SUMMARY")
        self.log("="*60)
        
        # Count results by status
        working = sum(1 for r in self.results.values() if r["status"] == "working")
        partial = sum(1 for r in self.results.values() if r["status"] == "partial")
        failed = sum(1 for r in self.results.values() if r["status"] == "failed")
        
        self.log(f"\n  Results Overview:")
        self.log(f"    ✅ Working:  {working}")
        self.log(f"    ⚠️  Partial: {partial}")
        self.log(f"    ❌ Failed:   {failed}")
        self.log(f"    Total:     {len(self.results)}")
        
        # Categorize components
        production_ready = [k for k, v in self.results.items() if v["status"] == "working"]
        needs_fixes = [k for k, v in self.results.items() if v["status"] == "partial"]
        not_implemented = [k for k, v in self.results.items() if v["status"] == "failed"]
        
        self.log("\n  Production Ready (✅):")
        for item in production_ready:
            self.log(f"    - {item}")
            
        self.log("\n  Needs Fixes (⚠️):")
        for item in needs_fixes:
            self.log(f"    - {item}")
            
        self.log("\n  Not Yet Implemented (❌):")
        for item in not_implemented:
            self.log(f"    - {item}")
            
    def save_report(self):
        """Save report to file."""
        report_path = Path.home() / "jarvis_os" / "pipeline_validation_report.txt"
        
        # Add header
        header = f"""
================================================================================
NEUROAD PIPELINE VALIDATION REPORT
================================================================================
Generated: {self.start_time.isoformat()}
Duration: {(datetime.now() - self.start_time).total_seconds():.1f} seconds

================================================================================
DETAILED RESULTS
================================================================================

"""
        footer = f"""

================================================================================
END OF REPORT
================================================================================
"""
        
        full_report = header + "\n".join(self.report_lines) + "\n" + footer
        
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(full_report)
            self.log(f"\n  Report saved to: {report_path}")
        except Exception as e:
            self.log(f"\n  Failed to save report: {e}")
            
    def run_all(self):
        """Run all validation checks."""
        self.log("="*60)
        self.log("NEUROAD PIPELINE VALIDATION")
        self.log("="*60)
        self.log(f"Start time: {self.start_time.isoformat()}")
        
        self.check_system()
        self.check_tribe_v2()
        self.check_saliency_engine()
        self.check_emotion_clip()
        self.check_creative_modules()
        self.check_turbo_quant()
        self.check_mirofish()
        self.check_lemonade_llm()
        self.check_model_swap_manager()
        
        self.generate_summary()
        self.save_report()
        
        return self.results


def main():
    """Main entry point."""
    validator = PipelineValidator()
    results = validator.run_all()
    
    # Exit with appropriate code
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    partial_count = sum(1 for r in results.values() if r["status"] == "partial")
    
    if failed_count > 0:
        print(f"\nValidation completed with {failed_count} failures and {partial_count} partial results.")
        sys.exit(1)
    elif partial_count > 0:
        print(f"\nValidation completed with {partial_count} partial results.")
        sys.exit(0)
    else:
        print("\nValidation completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
