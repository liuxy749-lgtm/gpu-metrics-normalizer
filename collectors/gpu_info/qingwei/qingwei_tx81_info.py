#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU 信息提取脚本 - qingwei
数据来源: 厂商 SMI 工具
提取: GPU利用率/显存利用率/显存总量/显存余量/显存已用/功耗/温度/型号/SN(UUID)
依赖: 仅标准库
用法: python3 gpu_info_qingwei.py [--json]
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
    text = run_cmd("tsm_smi")
    cards = {}
    order = []
    cur = None
    for l in text.splitlines():
        s = [x.strip() for x in l.split("|")]  # 保留空段
        if len(s) < 3:
            continue
        head = s[1]   # card 行: 名称在第二段; chip 行: 第二段为空
        body = s[2]   # 数据都在第三段
        p0 = head.split()
        if len(p0) >= 2 and p0[0].isdigit():
            # card 行
            cid = p0[0]; name = " ".join(p0[1:])
            if cid not in cards:
                cards[cid] = {"name": name, "n": 0, "temp": 0.0, "power": 0.0,
                              "mem_used": 0.0, "mem_total": 0.0, "util": 0.0}
                order.append(cid)
            cur = cards[cid]
        elif cur is not None and not head:
            # 该 card 的 chip 行 (保持 cur 不变)
            pass
        mm = re.search(r"(\d+)\s+(\S+)\s+([-\d.]+)C\s+([-\d.]+)W\s*/\s*([-\d.]+)W\s+(\d+)M\s*/\s*(\d+)M\s+([-\d.]+)%", body)
        if mm and cur is not None:
            c = cur
            c["n"] += 1; c["temp"] += float(mm.group(3)); c["power"] += float(mm.group(4))
            c["mem_used"] += float(mm.group(6)); c["mem_total"] += float(mm.group(7))
            c["util"] += float(mm.group(8))
    gpus = []
    for cid in order:
        c = cards[cid]; n = c["n"]
        g = base(c["util"] / n, c["mem_used"], c["mem_total"], c["power"], c["temp"] / n,
                 c["name"] + " (x%dChip)" % n)
        g["index"] = cid
        gpus.append(g)
    return gpus


def main():
    out(collect())


if __name__ == "__main__":
    main()
