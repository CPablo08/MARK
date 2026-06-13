import asyncio
import os
import tempfile
import uuid

from mark_core.config import get_settings

settings = get_settings()


async def run_sandbox_code(code: str, timeout: int = 10) -> str:
    os.makedirs(settings.sandbox_dir, exist_ok=True)
    path = os.path.join(settings.sandbox_dir, f"run_{uuid.uuid4().hex[:8]}.py")
    with open(path, "w") as f:
        f.write(code)

    proc = await asyncio.create_subprocess_exec(
        "python3",
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=settings.sandbox_dir,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode()[:1000]
        err = stderr.decode()[:500]
        return out or err or "(no output)"
    except asyncio.TimeoutError:
        proc.kill()
        return "Execution timed out (sandbox limit)"
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
