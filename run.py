#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import signal

# Get absolute paths of directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "smart_bee_backend_starter")
FRONTEND_DIR = os.path.join(BASE_DIR, "Smart Bee Email Interface")

def run():
    print("=" * 70)
    print("🐝 Smart Bee - Cross-Platform Development Runner")
    print("=" * 70)
    
    # 1. Determine OS and paths
    import shutil
    is_windows = os.name == 'nt'
    has_pnpm = shutil.which("pnpm") is not None
    
    if is_windows:
        python_bin = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")
        npm_cmd = "pnpm.cmd" if has_pnpm else "npm.cmd"
    else:
        python_bin = "python3"
        npm_cmd = "pnpm" if has_pnpm else "npm"
        
    pkg_mgr_name = "pnpm" if has_pnpm else "npm"
        
    if not os.path.exists(python_bin):
        print(f"⚠️ Virtual environment python not found at {python_bin}")
        print("Falling back to system python (make sure dependencies are installed).")
        python_bin = sys.executable
        
    # 2. Check and Install Node Modules
    if not os.path.exists(os.path.join(FRONTEND_DIR, "node_modules")):
        print(f"⚠️ node_modules not found in frontend directory. Running '{pkg_mgr_name} install' first...")
        try:
            subprocess.run([npm_cmd, "install"], cwd=FRONTEND_DIR, check=True)
            print(f"✅ {pkg_mgr_name} install completed successfully.")
        except Exception as e:
            print(f"❌ Failed to run {pkg_mgr_name} install: {e}")
            print(f"Please run {pkg_mgr_name} install manually inside the 'Smart Bee Email Interface' directory.")
            
    # 3. Start Backend Process
    print("\n📡 Starting Backend (FastAPI)...")
    backend_cmd = [
        python_bin, "-m", "uvicorn", "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ]
    
    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR
        )
    except Exception as e:
        print(f"❌ Failed to start Backend: {e}")
        sys.exit(1)
        
    # 4. Start Frontend Process
    print("💻 Starting Frontend (React/Vite)...")
    frontend_cmd = [npm_cmd, "run", "dev"]
    try:
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR
        )
    except Exception as e:
        print(f"❌ Failed to start Frontend: {e}")
        backend_proc.terminate()
        sys.exit(1)
        
    print("\n🚀 Both servers starting! See logs below.")
    print("Press Ctrl+C to terminate both servers...\n")
    
    def signal_handler(sig, frame):
        print("\n👋 Terminating servers...")
        try:
            backend_proc.terminate()
            frontend_proc.terminate()
            backend_proc.wait(timeout=2)
            frontend_proc.wait(timeout=2)
        except:
            try:
                backend_proc.kill()
                frontend_proc.kill()
            except:
                pass
        print("✅ Done. Goodbye!")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep main thread alive
    backend_proc.wait()
    frontend_proc.wait()

if __name__ == "__main__":
    run()
