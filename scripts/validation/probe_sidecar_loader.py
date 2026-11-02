"""Compare normal startup and explicit-loader startup under inherited glibc paths."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

result = []
for loader in (False, True):
    for polluted in (False, True):
        for command in (["--version"], ["debug", "config"]):
            with tempfile.TemporaryDirectory(prefix="ua-loader-") as tmp:
                env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": tmp, "TMPDIR": tmp,
                       "OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_DISABLE_MODELS_FETCH": "1",
                       "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
                       "OPENCODE_CONFIG_CONTENT": '{"autoupdate":false,"plugin":[],"lsp":false,"formatter":false}'}
                for kind in ("CONFIG", "DATA", "STATE", "CACHE"):
                    env[f"XDG_{kind}_HOME"] = str(Path(tmp) / kind.lower())
                if polluted:
                    env["LD_LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu"
                argv = (["/opt/opencode/lib/ld.so", "--library-path", "/opt/opencode/lib",
                         "/opt/opencode/libexec/opencode"] if loader else ["/opt/opencode/bin/opencode"]) + command
                completed = subprocess.run(argv, env=env, cwd=tmp, text=True, capture_output=True, timeout=30)
                row = {"explicit_loader": loader, "inherited_glibc_path": polluted, "command": command,
                       "returncode": completed.returncode, "stdout": completed.stdout[-6000:],
                       "stderr": completed.stderr[-6000:]}
                result.append(row)
                print(json.dumps(row), flush=True)
Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + "\n")
