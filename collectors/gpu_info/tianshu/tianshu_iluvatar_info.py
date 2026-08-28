#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU 信息提取脚本 - 天数智芯 Iluvatar 通用（BI-V150 / BI-V100 / MR-V100 / TG-V200）
================================================================================
数据来源: ixsmi --query-gpu (CSV, 各 corex 版本通用)
覆盖型号:
  - Iluvatar BI-V150  (corex-4.x, 64GB)
  - Iluvatar BI-V100  (corex-3.x, 32GB)
  - Iluvatar MR-V100  (corex-4.x, 32GB)
  - Iluvatar TG-V200  (corex-1.x, 64GB)
自动探测 ixsmi 路径与 LD_LIBRARY_PATH；power 字段名随版本自适应
(gpu.power.draw 4.x / power.draw 3.x)。
提取: GPU利用率/显存利用率/显存总量/显存余量/显存已用/功耗/温度/型号/SN/UUID
依赖: 仅标准库 + corex 运行时
用法: python3 tianshu_iluvatar_info.py [--json]
"""
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gpu_model_mapping import normalize_gpu_type, add_standard_metric_names


def find_ixsmi():
    """自动发现 ixsmi 二进制路径（选版本号最高的 corex）"""
    cands = []
    for p in glob.glob("/usr/local/corex-*/bin/ixsmi"):
        m = re.search(r"corex-([\d.]+(?:\.\d+)?)", p)
        ver = m.group(1) if m else "0"
        cands.append((ver, p))
    if not cands:
        # 兜底: PATH 里找
        for p in ("/usr/bin/ixsmi", "/usr/local/bin/ixsmi"):
            if os.path.exists(p):
                return p, os.path.dirname(os.path.dirname(p))
        return None, None
    cands.sort(key=lambda x: [int(n) for n in re.findall(r"\d+", x[0])])
    bin_path = cands[-1][1]
    lib_dir = os.path.join(os.path.dirname(os.path.dirname(bin_path)), "lib")
    return bin_path, lib_dir


def run_ix(cmd, timeout=30):
    bin_path, lib_dir = find_ixsmi()
    if not bin_path:
        return ""
    env = dict(os.environ)
    if lib_dir and os.path.isdir(lib_dir):
        env["LD_LIBRARY_PATH"] = lib_dir + ":" + env.get("LD_LIBRARY_PATH", "")
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env)
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
    bin_path, _ = find_ixsmi()
    if not bin_path:
        print("未找到 ixsmi，请确认已安装 corex 运行时", file=sys.stderr)
        return []

    fields = ("index,name,serial,uuid,memory.total,memory.used,memory.free,"
              "utilization.gpu,utilization.memory,temperature.gpu")
    # power 字段名版本差异: 先试 gpu.power.draw (4.x)，失败退 power.draw (3.x)
    power_field = "gpu.power.draw"
    text = run_ix('%s --query-gpu=%s,%s --format=csv,noheader,nounits' % (bin_path, fields, power_field))
    if not text.strip() or "not a valid field" in text:
        power_field = "power.draw"
        text = run_ix('%s --query-gpu=%s,%s --format=csv,noheader,nounits' % (bin_path, fields, power_field))

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
