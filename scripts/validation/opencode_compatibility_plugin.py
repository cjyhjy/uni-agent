"""Explicit test-only version-gate override; never imported by production code.

UA_COMPAT_VERSION selects exactly one investigated release. This permits
measuring behavior beyond the current guard; it does not change supported versions.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from uni_agent.agents.opencode import agent
from uni_agent.sandbox.local import LocalSandbox


@pytest.fixture(autouse=True)
def compatibility_experiment(monkeypatch, request):
    version = os.environ.get("UA_COMPAT_VERSION")
    if version not in {"1.18.18", "1.19.3"}:
        pytest.fail("compatibility plugin requires explicit UA_COMPAT_VERSION=1.18.18 or 1.19.3")
    output = Path(os.environ["UA_COMPAT_RECORDS"])
    original = LocalSandbox._exec
    monkeypatch.setattr(agent, "OPENCODE_VERSION", version)

    async def observed_exec(self, argv, **kwargs):
        result = await original(self, argv, **kwargs)
        if len(argv) > 1 and argv[1] in {"run", "--version"}:
            # Only synthetic test CLI output, no arbitrary environment or credentials.
            env = kwargs.get("env") or {}
            config = json.loads(env["OPENCODE_CONFIG_CONTENT"]) if env.get("OPENCODE_CONFIG_CONTENT") else {}
            record = {
                "test": request.node.nodeid,
                "experimental_version": version,
                "command": argv,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "config_keys": sorted(config),
                "guard_override": True,
            }
            with output.open("a") as stream:
                stream.write(json.dumps(record) + "\n")
        return result

    monkeypatch.setattr(LocalSandbox, "_exec", observed_exec)
