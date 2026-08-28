#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU 信息提取脚本 - NVIDIA 通用（A100 / A800 / H100 / H800 / B200 等）
=====================================================================
数据来源: nvidia-smi --query-gpu (标准 CSV, 所有 NVIDIA 数据中心卡通用)
提取: GPU利用率/显存利用率/显存总量/显存余量/显存已用/功耗/温度/型号/SN/UUID
依赖: 仅标准库 + nvidia-smi (系统自带)
用法: python3 nvidia_gpu_info.py [--json]
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gpu_model_mapping import normalize_gpu_type, add_standard_metric_names

FIELDS = (
    "index,name,serial,uuid,memory.total,memory.used,memory.free,"
    "utilization.gpu,utilization.memory,power.draw,temperature.gpu"
)


def run_cmd(cmd, timeout=30):
    """兼容 Python <3.7 的 subprocess 封装"""
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, _ = p.communicate(timeout=timeout)
        return out.decode("utf-8", "replace")
    except Exception:
        return ""


def to_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def base(util, mem_used, mem_total, power_w, temp_c, gpu_type, sn="", uuid=""):
    gpu_type = normalize_gpu_type(gpu_type)
    mem_total_b = int(mem_total * 1048576)
    mem_used_b = int(mem_used * 1048576)
    record = {
        "gpu_type": gpu_type, "gpu_sn": sn, "gpu_uuid": uuid,
        "memory_total_bytes": mem_total_b, "memory_free_bytes": mem_total_b - mem_used_b,
        "memory_used_bytes": mem_used_b,
        "memory_usage_ratio": round(mem_used / mem_total, 4) if mem_total else 0.0,
        "gpu_utilization_percent": util,
        "memory_utilization_percent": round(mem_used / mem_total * 100, 2) if mem_total else 0.0,
        "power_watts": power_w, "temperature_c": temp_c,
    }
    return add_standard_metric_names(record)


def collect():
    text = run_cmd("nvidia-smi --query-gpu=%s --format=csv,noheader,nounits" % FIELDS)
    if not text.strip():
        print("nvidia-smi 调用失败或无输出", file=sys.stderr)
        return []
    gpus = []
    for line in text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 11:
            continue
        (idx, name, serial, uuid, mem_total, mem_used, mem_free,
         util_gpu, util_mem, power, temp) = parts[:11]
        g = base(to_float(util_gpu), to_float(mem_used), to_float(mem_total),
                 to_float(power), to_float(temp), name, sn=serial, uuid=uuid)
        g["index"] = idx
        gpus.append(g)
    return gpus


def out(gpus):
    if "--json" in sys.argv:
        print(json.dumps(gpus, ensure_ascii=False, indent=2))
        return
    print("GPU 数量: %d\n" % len(gpus))
    for g in gpus:
        print("--- GPU %s ---" % g["index"])
        print("  型号        : %s" % g["gpu_type"])
        print("  SN/UUID     : %s" % (g["gpu_sn"] or g["gpu_uuid"] or "N/A"))
        print("  GPU 利用率  : %.1f %%" % g["gpu_utilization_percent"])
        print("  显存利用率  : %.1f %%" % g["memory_utilization_percent"])
        print("  显存总量    : %.2f GiB" % (g["memory_total_bytes"] / 1073741824))
        print("  显存余量    : %.2f GiB" % (g["memory_free_bytes"] / 1073741824))
        print("  显存已用    : %.2f GiB" % (g["memory_used_bytes"] / 1073741824))
        print("  功耗        : %.1f W" % g["power_watts"])
        print("  温度        : %.1f C" % g["temperature_c"])
    if gpus:
        n = len(gpus)
        print("\n===== 汇总 =====")
        print("平均GPU利用率: %.1f%%  平均显存利用率: %.1f%%"
              % (sum(g["gpu_utilization_percent"] for g in gpus) / n,
                 sum(g["memory_usage_ratio"] for g in gpus) / n * 100))
        print("显存总量/余量: %.2f GiB / %.2f GiB  整机功耗: %.1f W"
              % (sum(g["memory_total_bytes"] for g in gpus) / 1073741824,
                 sum(g["memory_free_bytes"] for g in gpus) / 1073741824,
                 sum(g["power_watts"] for g in gpus)))


def main():
    out(collect())


if __name__ == "__main__":
    main()
