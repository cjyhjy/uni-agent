"""Exercise #298's unchanged CLI through the adapter and expect safe rejection."""

import asyncio
import json
import sys
from dataclasses import asdict

from examples.opencode.smoke_task import run_smoke


async def main():
    result = await run_smoke(sys.argv[1])
    print(json.dumps(asdict(result), default=str))
    assert result.finished is False
    assert result.reward == 0.0
    assert result.extra_info["agent_error"] == "unsupported_version"
    assert result.extra_info["requests"] == 0
    assert result.extra_info["verifier_exit_code"] is None
    assert result.extra_info["workspace_removed"] is True


if __name__ == "__main__":
    asyncio.run(main())
