"""Compare normal startup and explicit-loader startup under inherited glibc paths."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

result = []
for loader in (False, True):
    for polluted in (False, True):
        for command in (["--version"], ["debug", "config"]):
            with tempfile.TemporaryDirectory(prefix="ua-loader-") as tmp:
                env = {
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "HOME": tmp,
                    "TMPDIR": tmp,
                    "OPENCODE_DISABLE_AUTOUPDATE": "1",
                    "OPENCODE_DISABLE_MODELS_FETCH": "1",
                    "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
                    "OPENCODE_CONFIG_CONTENT": '{"autoupdate":false,"plugin":[],"lsp":false,"formatter":false}',
                }
                for kind in ("CONFIG", "DATA", "STATE", "CACHE"):
                    env[f"XDG_{kind}_HOME"] = str(Path(tmp) / kind.lower())
                if polluted:
                    env["LD_LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu"
                argv = (["/opt/opencode/bin/opencode"] if loader else [sys.argv[2]]) + command
                completed = subprocess.run(argv, env=env, cwd=tmp, text=True, capture_output=True, timeout=30)
                row = {
                    "candidate": loader,
                    "inherited_glibc_path": polluted,
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-6000:],
                    "stderr": completed.stderr[-6000:],
                }
                result.append(row)
                print(json.dumps(row), flush=True)
Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + "\n")

for row in result:
    if not row["candidate"] and row["inherited_glibc_path"]:
        assert row["returncode"] == 127 and "Error relocating" in row["stderr"], row
    else:
        assert row["returncode"] == 0, row
        if row["command"] == ["--version"]:
            assert row["stdout"].strip() == Path("/opt/opencode/OPENCODE_VERSION").read_text().strip(), row
        else:
            assert isinstance(json.loads(row["stdout"]), dict), row
