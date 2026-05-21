from fastapi import APIRouter
from ..services.config_loader import get_config
from ..services.wmi_poller import get_hardware_telemetry, get_gpu_telemetry, get_npu_telemetry
from ..services.lemonade_client import get_inference_metrics

router = APIRouter(tags=["telemetry"])


@router.get("/telemetry/hardware")
async def hardware():
    return get_hardware_telemetry()


@router.get("/telemetry/speed")
async def speed():
    config = get_config()
    lemonade_url = config.get("lemonadeUrl", "http://[::1]:13305")
    return await get_inference_metrics(lemonade_url)


@router.get("/telemetry/hardware-full")
async def hardware_full():
    """Full hardware panel data: CPU, RAM, GPU, VRAM, NPU, temp, system name."""
    import asyncio
    config = get_config()
    lemonade_url = config.get("lemonadeUrl", "http://[::1]:13305")

    loop = asyncio.get_event_loop()
    hw, gpu = await asyncio.gather(
        loop.run_in_executor(None, get_hardware_telemetry),
        loop.run_in_executor(None, get_gpu_telemetry),
    )

    # Get NPU from PDH counter (separate query, won't break GPU if it fails)
    npu = await loop.run_in_executor(None, get_npu_telemetry)
    npu_percent = npu.get("npu_percent")

    return {
        "cpu_percent": hw.get("cpu_percent"),
        "ram_used_gb": hw.get("ram_used_gb"),
        "ram_total_gb": hw.get("ram_total_gb"),
        "gpu_3d_percent": gpu.get("gpu_3d_percent"),
        "vram_used_gb": gpu.get("vram_used_gb"),
        "npu_percent": npu_percent,
        "temp_c": gpu.get("temp_c"),
        "hostname": hw.get("hostname", "GOPO"),
        "cpu_name": hw.get("cpu_name", "AMD Ryzen AI MAX+"),
    }


@router.get("/telemetry/lemonade-full")
async def lemonade_full():
    """Full Local AI panel data: model, throughput, tokens, peaks."""
    config = get_config()
    lemonade_url = config.get("lemonadeUrl", "http://[::1]:13305")
    project_start = config.get("pixelProjectStart")

    lm = await get_inference_metrics(lemonade_url)

    return {
        "is_live": lm.get("is_live", False),
        "active_model": lm.get("active_model", "Qwen3.6 35B"),
        "active_model_raw": lm.get("active_model_raw", ""),
        "tokens_per_second": lm.get("tokens_per_second"),
        "time_to_first_token": lm.get("time_to_first_token"),
        "input_tokens": lm.get("input_tokens"),
        "output_tokens": lm.get("output_tokens"),
        "npu_utilization": lm.get("npu_utilization"),
        "peak_tokens_per_second": lm.get("peak_tokens_per_second"),
        "peak_npu_utilization": lm.get("peak_npu_utilization"),
        "project_start": project_start,
    }
