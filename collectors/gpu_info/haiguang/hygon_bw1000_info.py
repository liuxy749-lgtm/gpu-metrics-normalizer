#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海光 BW1000 DCU 信息提取脚本（纯 sysfs 实现）
==============================================
不依赖 dcu-smi，不依赖 dcu-exporter，不依赖任何第三方库。
直接读取内核 sysfs（ROCm/amdgpu 兼容接口）:
  /sys/class/drm/cardN/device/  (gpu_busy_percent, mem_info_vram_*, unique_id)
  /sys/class/drm/cardN/device/hwmon/hwmonX/  (temp1_input, power1_average)

提取每张卡的:
  - GPU 利用率 (%)
  - 显存利用率 (%)
  - 显存总量 / 余量 / 已用 (bytes -> GiB)
  - 功耗 (W)
  - 温度 (°C)
  - GPU 型号 (PCI vendor/device 映射)
  - GPU SN (unique_id)

用法:
  python3 gpu_info.py             # 可读文本输出
  python3 gpu_info.py --json      # JSON 输出
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gpu_model_mapping import normalize_gpu_type, add_standard_metric_names

DRM = "/sys/class/drm"

# 海光 (Hygon) PCI ID -> 型号映射; 可按实际机型扩展
PCI_MODEL = {
    ("0x1d94", "0x6320"): "Hygon BW1000-64G",
}
HYGON_VENDOR = "0x1d94"


def _read(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return ""


def _read_float(path):
    try:
        return float(_read(path))
    except (ValueError, TypeError):
        return 0.0


def collect():
    cards = sorted(
        (d for d in os.listdir(DRM) if d.startswith("card") and d[4:].isdigit()),
        key=lambda x: int(x[4:]),
    )
    gpus = []
    for card in cards:
        dev = os.path.join(DRM, card, "device")
        if not os.path.isdir(dev):
            continue
        vendor = _read(os.path.join(dev, "vendor"))
        if vendor != HYGON_VENDOR:      # 过滤 ASPEED 等板载显卡
            continue

        mem_total = _read_float(os.path.join(dev, "mem_info_vram_total"))
        mem_used = _read_float(os.path.join(dev, "mem_info_vram_used"))
        mem_free = max(0.0, mem_total - mem_used)
        mem_ratio = (mem_used / mem_total) if mem_total > 0 else 0.0

        hwmon = ""
        hwd = os.path.join(dev, "hwmon")
        if os.path.isdir(hwd):
            hmons = sorted(d for d in os.listdir(hwd) if d.startswith("hwmon"))
            if hmons:
                hwmon = os.path.join(hwd, hmons[0])

        temp_c = _read_float(os.path.join(hwmon, "temp1_input")) / 1000.0 if hwmon else 0.0
        power_w = _read_float(os.path.join(hwmon, "power1_average")) / 1e6 if hwmon else 0.0
        uevent = _read(os.path.join(dev, "uevent"))
        pci = ""
        for line in uevent.splitlines():
            if line.startswith("PCI_SLOT_NAME="):
                pci = line.split("=", 1)[1]
                break

        device_id = _read(os.path.join(dev, "device"))
        raw_model = PCI_MODEL.get((vendor, device_id), "%s:%s" % (vendor, device_id))
        record = {
            "index": str(len(gpus)),
            "card": card,
            "gpu_type": normalize_gpu_type(raw_model),
            "gpu_sn": _read(os.path.join(dev, "unique_id")),
            "gpu_uuid": _read(os.path.join(dev, "unique_id")),
            "memory_total_bytes": int(mem_total),
            "memory_free_bytes": int(mem_free),
            "memory_used_bytes": int(mem_used),
            "memory_usage_ratio": round(mem_ratio, 4),
            "gpu_utilization_percent": _read_float(os.path.join(dev, "gpu_busy_percent")),
            "memory_utilization_percent": round(mem_ratio * 100, 2),
            "power_watts": power_w,
            "temperature_c": temp_c,
            "pci_bus_id": pci,
        }
        gpus.append(add_standard_metric_names(record))
    return gpus


def print_text(gpus):
    print("DCU 数量: %d\n" % len(gpus))
    for g in gpus:
        print("--- GPU %s (%s) ---" % (g["index"], g["card"]))
        print("  型号        : %s" % g["gpu_type"])
        print("  SN          : %s" % g["gpu_sn"])
        print("  PCI Bus     : %s" % g["pci_bus_id"])
        print("  GPU 利用率  : %.1f %%" % g["gpu_utilization_percent"])
        print("  显存利用率  : %.1f %%" % g["memory_utilization_percent"])
        print("  显存总量    : %.2f GiB" % (g["memory_total_bytes"] / 1024 ** 3))
        print("  显存余量    : %.2f GiB" % (g["memory_free_bytes"] / 1024 ** 3))
        print("  显存已用    : %.2f GiB" % (g["memory_used_bytes"] / 1024 ** 3))
        print("  功耗        : %.1f W" % g["power_watts"])
        print("  温度        : %.1f °C" % g["temperature_c"])
    if gpus:
        avg_util = sum(g["gpu_utilization_percent"] for g in gpus) / len(gpus)
        avg_mem = sum(g["memory_usage_ratio"] for g in gpus) / len(gpus)
        total_mem = sum(g["memory_total_bytes"] for g in gpus)
        total_free = sum(g["memory_free_bytes"] for g in gpus)
        total_power = sum(g["power_watts"] for g in gpus)
        print("\n===== 汇总 =====")
        print("平均 GPU 利用率 : %.1f %%" % avg_util)
        print("平均显存利用率 : %.1f %%" % (avg_mem * 100))
        print("显存总量/余量  : %.2f GiB / %.2f GiB"
              % (total_mem / 1024 ** 3, total_free / 1024 ** 3))
        print("整机功耗       : %.1f W" % total_power)


def main():
    gpus = collect()
    if "--json" in sys.argv:
        print(json.dumps(gpus, ensure_ascii=False, indent=2))
    else:
        print_text(gpus)


if __name__ == "__main__":
    main()
