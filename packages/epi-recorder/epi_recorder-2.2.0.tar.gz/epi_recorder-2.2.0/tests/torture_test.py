import os
import shutil
from pathlib import Path
import subprocess
import sys

# 1. Setup "Torture" Path
torture_dir = Path("Torture Test/With Spaces")
if torture_dir.exists():
    shutil.rmtree(torture_dir)
torture_dir.mkdir(parents=True)

# 2. Create a script with secrets at that path
script_path = torture_dir / "secret_script.py"
script_content = """
import os
print("Running inside torture path...")
print("My API Key is: sk-1234567890abcdef1234567890abcdef")
print("Done.")
"""
script_path.write_text(script_content, encoding="utf-8")

# 3. Run EPI on it
print(f"Running EPI on: {script_path}")
cmd = [sys.executable, "-m", "epi_cli.main", "run", str(script_path), "--no-open", "--no-verify"]
try:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print("[X] CRASHED!")
        sys.exit(1)
        
    # 4. Verify Redaction
    print("[OK] EPI ran successfully.")
    # Find the output file
    # (It should be in ./epi-recordings/ relative to CWD, not the script dir)
    recs = list(Path("epi-recordings").glob("secret_script_*.epi"))
    if not recs:
        print("[X] Could not find output file!")
        sys.exit(1)
        
    latest = sorted(recs)[-1]
    
    # Unpack and check
    import zipfile
    import json
    
    with zipfile.ZipFile(latest, 'r') as zf:
        # steps.jsonl is a line-delimited JSON file
        lines = zf.read("steps.jsonl").decode('utf-8').splitlines()
        
    found_secret = False
    for line in lines:
        if "sk-1234567890abcdef1234567890abcdef" in line:
            found_secret = True
            break
            
    if found_secret:
        print("[FAIL] Secret was NOT redacted!")
    else:
        print("[SUCCESS] Secret was redacted.")
        
except Exception as e:
    print(f"[ERROR] Exception: {e}")


