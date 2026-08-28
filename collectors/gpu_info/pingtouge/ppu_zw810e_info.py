#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU 信息提取脚本 - pingtouge
数据来源: 厂商 SMI 工具
提取: GPU利用率/显存利用率/显存总量/显存余量/显存已用/功耗/温度/型号/SN(UUID)
依赖: 仅标准库
用法: python3 gpu_info_pingtouge.py [--json]
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gpu_model_mapping import normalize_gpu_type, add_standard_metric_names


def run_cmd(cmd, timeout=25):
    try:
        p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return p.stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def segs(line):
    return [s.strip() for s in line.split("|") if s.strip()]


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


def out(gpus):
    if "--json" in sys.argv:
        print(json.dumps(gpus, ensure_ascii=False, indent=2))
    else:
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

def collect():
    text = run_cmd("ppu-smi")
    gpus = []
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        s1 = segs(lines[i]); s2 = segs(lines[i+1])
        if s1 and s1[0][0].isdigit() and len(s1) >= 2 and len(s2) >= 3:
            p0 = s1[0].split()
            gid = p0[0]; name = p0[1] if len(p0) > 1 else ""
            mt = re.search(r"([-\d.]+)C", s2[0])
            mp = re.search(r"([-\d.]+)W\s*/\s*([-\d.]+)W", s2[0])
            mm = re.search(r"([-\d.]+)MiB\s*/\s*([-\d.]+)MiB", s2[1])
            mu = re.search(r"([-\d.]+)%", s2[2])
            if mt and mp and mm and mu:
                util = float(mu.group(1)); power = float(mp.group(1)); temp = float(mt.group(1))
                mem_used = float(mm.group(1)); mem_total = float(mm.group(2))
                uuid = ""
                lu = run_cmd("ppu-smi -L")
                mu2 = re.search(r"PPU %s:\s*\S+\s+\(UUID:\s*(\S+)\)" % gid, lu)
                if mu2: uuid = mu2.group(1)
                g = base(util, mem_used, mem_total, power, temp, name, uuid=uuid)
                g["index"] = gid
                gpus.append(g)
            i += 2
            continue
        i += 1
    return gpus


def main():
    out(collect())


if __name__ == "__main__":
    main()
