import subprocess, os, time, math, logging, json, socket

log = logging.getLogger(__name__)

_hw_cache: dict = {}
_hw_cache_time: float = 0
HW_CACHE_TTL = 2.0
_sys_info_cache: dict = {}  # Never changes — cache forever

_gpu_cache: dict = {}
_gpu_cache_time: float = 0
GPU_CACHE_TTL = 3.0


def _mock_data() -> dict:
    t = time.time()
    return {
        "cpu_percent": round(35 + 20 * math.sin(t / 3), 1),
        "ram_used_gb": round(12.4 + 2 * math.sin(t / 10), 1),
        "ram_total_gb": 32.0,
        "gpu_3d_percent": round(45 + 30 * math.sin(t / 5), 1),
        "vram_used_gb": round(1.2 + 0.8 * math.sin(t / 7), 2),
        "npu_percent": round(40 + 20 * math.sin(t / 5), 1),
        "temp_c": round(55 + 10 * math.sin(t / 8), 1),
        "hostname": "DEMO-PC",
        "cpu_name": "AMD Ryzen AI MAX+ 395",
    }


def _ps(cmd: str, timeout: int = 5) -> str | None:
    """Run a PowerShell command, return stdout or None on error."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
    except Exception as e:
        log.debug("PS call failed: %s", e)
        return None


def _query_cpu_ram() -> dict:
    # Single PS call for CPU % + RAM together
    script = (
        "$cpu = (Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage); "
        "$mem = Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize; "
        "@{ cpu=$cpu; free=$mem.FreePhysicalMemory; total=$mem.TotalVisibleMemorySize } | ConvertTo-Json"
    )
    result = {"cpu_percent": None, "ram_used_gb": None, "ram_total_gb": None}
    out = _ps(script)
    if out:
        try:
            d = json.loads(out)
            result["cpu_percent"] = float(d["cpu"]) if d.get("cpu") is not None else None
            total_kb = d.get("total")
            free_kb = d.get("free")
            if total_kb and free_kb:
                result["ram_total_gb"] = round(total_kb / 1048576, 1)
                result["ram_used_gb"] = round((total_kb - free_kb) / 1048576, 1)
        except Exception as e:
            log.debug("CPU/RAM parse error: %s", e)
    return result


def _query_gpu_temp() -> dict:
    # GPU compute + VRAM + temp query (original, proven working)
    script = (
        "$r = @{}; "
        "try { $r.gpu = (Get-Counter '\\GPU Engine(*engtype_Compute 0*)\\Utilization Percentage').CounterSamples | Measure-Object CookedValue -Sum | Select-Object -ExpandProperty Sum } catch { $r.gpu = $null }; "
        "try { $r.vram = (Get-Counter '\\GPU Local Adapter Memory(*)\\Local Usage').CounterSamples | Measure-Object CookedValue -Maximum | Select-Object -ExpandProperty Maximum } catch { $r.vram = $null }; "
        "try { $r.temp = (Get-Counter '\\Thermal Zone Information(*)\\Temperature').CounterSamples | Measure-Object CookedValue -Maximum | Select-Object -ExpandProperty Maximum } catch { $r.temp = $null }; "
        "$r | ConvertTo-Json"
    )
    out = _ps(script, timeout=20)
    result = {"gpu_3d_percent": None, "vram_used_gb": None, "temp_c": None}
    if out:
        try:
            d = json.loads(out)
            if d.get("gpu") is not None:
                result["gpu_3d_percent"] = round(float(d["gpu"]), 1)
            if d.get("vram") is not None:
                result["vram_used_gb"] = round(float(d["vram"]) / (1024 ** 3), 2)
            if d.get("temp") is not None:
                k = float(d["temp"])
                result["temp_c"] = round(k - 273.15, 1) if k > 200 else round(k, 1)
        except Exception as e:
            log.debug("GPU/temp parse error: %s", e)
    return result


def _get_system_info() -> dict:
    global _sys_info_cache
    if _sys_info_cache:
        return _sys_info_cache
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "localhost"
    out = _ps("Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name")
    if out:
        cpu_name = out.split(" w/")[0].strip().title()
        cpu_name = cpu_name.replace("Amd", "AMD").replace("Ai", "AI")
    else:
        cpu_name = "AMD Ryzen AI MAX+"
    _sys_info_cache = {"hostname": hostname, "cpu_name": cpu_name}
    return _sys_info_cache


_npu_cache: dict = {}
_npu_cache_time: float = 0
NPU_CACHE_TTL = 3.0

# NPU LUID — the adapter with engtype_compute but no engtype_3d.
# Detected once, cached forever (doesn't change until reboot).
_npu_luid: str | None = None
_npu_luid_detected = False


def _detect_npu_luid() -> str | None:
    """Find the LUID of the NPU adapter (compute-only, no 3D engine)."""
    script = (
        "$eng = (Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction Stop).CounterSamples; "
        "$luids3d = @(); $eng | ForEach-Object { if ($_.InstanceName -match 'engtype_3d' -and $_.InstanceName -match 'luid_(0x[0-9a-fA-F]+_0x[0-9a-fA-F]+)') { $luids3d += $matches[1] } }; "
        "$luids3d = $luids3d | Sort-Object -Unique; "
        "$npuLuid = $null; $eng | ForEach-Object { if ($_.InstanceName -match 'engtype_compute' -and $_.InstanceName -match 'luid_(0x[0-9a-fA-F]+_0x[0-9a-fA-F]+)') { $l = $matches[1]; if ($luids3d -notcontains $l) { $npuLuid = $l } } }; "
        "$npuLuid"
    )
    out = _ps(script, timeout=15)
    if out and out.startswith('0x'):
        log.info("Detected NPU LUID: %s", out)
        return out
    log.info("No NPU LUID detected")
    return None


def _query_npu() -> dict:
    """Query NPU utilization via PDH counter for the NPU LUID."""
    global _npu_luid, _npu_luid_detected
    if not _npu_luid_detected:
        _npu_luid = _detect_npu_luid()
        _npu_luid_detected = True
    if not _npu_luid:
        return {"npu_percent": None}
    script = (
        f"(Get-Counter '\\GPU Engine(*luid_{_npu_luid}*engtype_compute*)\\Utilization Percentage' "
        f"-ErrorAction Stop).CounterSamples | Measure-Object CookedValue -Sum | "
        f"Select-Object -ExpandProperty Sum"
    )
    out = _ps(script, timeout=10)
    if out:
        try:
            return {"npu_percent": round(float(out), 1)}
        except ValueError:
            pass
    return {"npu_percent": 0.0}


def get_npu_telemetry() -> dict:
    """Return cached NPU data. Triggers background refresh if stale."""
    global _npu_cache, _npu_cache_time
    now = time.time()
    if (now - _npu_cache_time) < NPU_CACHE_TTL and _npu_cache:
        return dict(_npu_cache)
    if os.environ.get("MOCK_TELEMETRY") == "1":
        t = time.time()
        _npu_cache = {"npu_percent": round(40 + 20 * math.sin(t / 5), 1)}
    else:
        _npu_cache = _query_npu()
    _npu_cache_time = now
    return dict(_npu_cache)


def get_hardware_telemetry() -> dict:
    global _hw_cache, _hw_cache_time
    now = time.time()
    if now - _hw_cache_time < HW_CACHE_TTL and _hw_cache:
        return _hw_cache

    if os.environ.get("MOCK_TELEMETRY") == "1":
        _hw_cache = _mock_data()
        _hw_cache_time = now
        return _hw_cache

    result = _query_cpu_ram()
    result.update(_get_system_info())
    _hw_cache = result
    _hw_cache_time = now
    return result


_gpu_poll_running = False


def _refresh_gpu_cache():
    """Run GPU/temp queries and update cache. Called in a background thread."""
    global _gpu_cache, _gpu_cache_time, _gpu_poll_running
    if _gpu_poll_running:
        return
    _gpu_poll_running = True
    try:
        if os.environ.get("MOCK_TELEMETRY") == "1":
            t = time.time()
            data = {
                "gpu_3d_percent": round(45 + 30 * math.sin(t / 5), 1),
                "vram_used_gb": round(1.2 + 0.8 * math.sin(t / 7), 2),
                "temp_c": round(55 + 10 * math.sin(t / 8), 1),
            }
        else:
            data = _query_gpu_temp()
        _gpu_cache = data
        _gpu_cache_time = time.time()
    finally:
        _gpu_poll_running = False


def get_gpu_telemetry() -> dict:
    """Return cached GPU/temp data. Triggers a background refresh if stale."""
    global _gpu_cache, _gpu_cache_time
    now = time.time()
    stale = (now - _gpu_cache_time) >= GPU_CACHE_TTL
    if stale and not _gpu_poll_running:
        import threading
        threading.Thread(target=_refresh_gpu_cache, daemon=True).start()
    # Return whatever is cached (may be empty dict on first call)
    return dict(_gpu_cache)
