import subprocess, os, json, logging
from fastapi import APIRouter

log = logging.getLogger(__name__)
router = APIRouter(tags=["loops"])

LOOP_PATTERNS = {
    "orchestrator": "loop_orchestrator",
    "qa": "loop_qa",
    "coding_worker": "loop_coding_worker",
}


@router.get("/loops/{slug}")
async def loop_status(slug: str):
    if os.environ.get("MOCK_LOOPS") == "1":
        return {
            "loops": {
                k: {"alive": True, "pid": 1234 + i}
                for i, k in enumerate(LOOP_PATTERNS)
            }
        }
    loops = {}
    for name, pattern in LOOP_PATTERNS.items():
        try:
            ps = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Get-CimInstance Win32_Process | Where-Object {{ $_.CommandLine -match '{pattern}.*{slug}' }} | Select-Object ProcessId | ConvertTo-Json",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if ps.returncode == 0 and ps.stdout.strip():
                data = json.loads(ps.stdout)
                pid = (
                    data[0]["ProcessId"]
                    if isinstance(data, list)
                    else data.get("ProcessId")
                )
                loops[name] = {"alive": True, "pid": pid}
            else:
                loops[name] = {"alive": False, "pid": None}
        except Exception as e:
            log.warning("Loop check %s failed: %s", name, e)
            loops[name] = {"alive": False, "pid": None}
    return {"loops": loops}
