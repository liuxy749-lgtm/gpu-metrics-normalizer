#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU model normalization helpers.

Vendor tools expose model names in different formats.  Keep the canonical
names here so every collector returns a stable `gpu_type` value.
"""

import os
import re


MODEL_ALIASES = {
    # NVIDIA
    "NVIDIA A100-SXM4-40GB": "英伟达-A100-40G",
    "NVIDIA A100-PCIE-40GB": "英伟达-A100-40G",
    "NVIDIA A100 80GB PCIe": "英伟达-A100-80G",
    "NVIDIA A800-SXM4-80GB": "英伟达-A800-80G",
    "NVIDIA A800 80GB PCIe": "英伟达-A800-80G",
    "NVIDIA H100 80GB HBM3": "英伟达-H100-80G",
    "NVIDIA H100 PCIe": "英伟达-H100-80G",
    "NVIDIA H100 NVL": "英伟达-H100-80G",
    "NVIDIA H800": "英伟达-H800-80G",
    "NVIDIA H20": "英伟达-H20-96G",
    "NVIDIA B200": "英伟达-B200-179G",
    "Tesla V100-SXM2-32GB": "英伟达-V100-32G",
    "NVIDIA GeForce RTX 4090": "英伟达-4090-24G",

    # Ascend
    "Ascend910-Ascend-V1": "昇腾-910C-64G",
    "Ascend910": "昇腾-910C-64G",
    "Ascend 910": "昇腾-910C-64G",
    "Ascend 910B": "昇腾-910B-64G",
    "Ascend 910C": "昇腾-910C-64G",

    # Iluvatar / Tianshu
    "Iluvatar BI-V100": "天数-BIV100-64G",
    "Iluvatar BI-V150": "天数-BIV150-64G",
    "BI-V100": "天数-BIV100-64G",
    "BI-V150": "天数-BIV150-64G",
    "Iluvatar TG-V200 OAM": "天数-TGV200-64G",
    "TGV200": "天数-TGV200-64G",

    # Moore Threads
    "MTT S5000": "摩尔-S5000-80G",
    "MUSA S5000": "摩尔-S5000-80G",
    "S5000": "摩尔-S5000-80G",

    # MetaX
    "MetaX C550": "沐曦-MC550-64G",
    "MXC550": "沐曦-MC550-64G",
    "MC550": "沐曦-MC550-64G",

    # Kunlunxin
    "P800 OAM": "昆仑芯-P800-96G",
    "P800": "昆仑芯-P800-96G",

    # Hygon
    "DCU K100_AI": "海光-BW1000-64G",
    "BW1000": "海光-BW1000-64G",

    # Tsingmicro
    "TX8110": "清微-TX8110-64G",
    "TX81": "清微-TX81-64G",

    # Enflame
    "ZIXIAOC200": "燧原-S60-48GB",
    "S60": "燧原-S60-48GB",

    # Pingtouge / Sunrise
    "PPU ZW810E": "平头哥-PPU-ZW810E",
    "ZW810E": "平头哥-PPU-ZW810E",
    "SR-SUN-S2-X1-PCIE": "曦望-S2",
    "Sunrise S2": "曦望-S2",
}


def normalize_gpu_type(raw_name):
    """Return a stable model name for raw vendor output."""
    name = str(raw_name or "").strip()
    if not name:
        return ""

    compact = re.sub(r"\s+", " ", name)
    if compact in MODEL_ALIASES:
        return MODEL_ALIASES[compact]

    lower = compact.lower()
    contains_rules = (
        ("a100", "英伟达-A100-40G"),
        ("a800", "英伟达-A800-80G"),
        ("h100", "英伟达-H100-80G"),
        ("h800", "英伟达-H800-80G"),
        ("h20", "英伟达-H20-96G"),
        ("b200", "英伟达-B200-179G"),
        ("v100", "英伟达-V100-32G"),
        ("4090", "英伟达-4090-24G"),
        ("910b", "昇腾-910B-64G"),
        ("910c", "昇腾-910C-64G"),
        ("ascend910", "昇腾-910C-64G"),
        ("bi-v100", "天数-BIV100-64G"),
        ("biv100", "天数-BIV100-64G"),
        ("bi-v150", "天数-BIV150-64G"),
        ("biv150", "天数-BIV150-64G"),
        ("tgv200", "天数-TGV200-64G"),
        ("s5000", "摩尔-S5000-80G"),
        ("mc550", "沐曦-MC550-64G"),
        ("mxc550", "沐曦-MC550-64G"),
        ("metax c550", "沐曦-MC550-64G"),
        ("p800", "昆仑芯-P800-96G"),
        ("bw1000", "海光-BW1000-64G"),
        ("k100_ai", "海光-BW1000-64G"),
        ("tx8110", "清微-TX8110-64G"),
        ("tx81", "清微-TX81-64G"),
        ("s60", "燧原-S60-48GB"),
        ("zixiaoc200", "燧原-S60-48GB"),
        ("zw810e", "平头哥-PPU-ZW810E"),
        ("sr-sun-s2", "曦望-S2"),
        ("sunrise s2", "曦望-S2"),
    )
    for needle, canonical in contains_rules:
        if needle in lower:
            return canonical
    return compact


def add_standard_metric_names(record):
    """Add canonical metric field names while keeping legacy fields."""
    if os.environ.get("ENABLE_DEVICE_ID", "0").lower() not in ("1", "true", "yes", "on"):
        record["gpu_sn"] = ""
        record["gpu_uuid"] = ""

    total = int(record.get("memory_total_bytes", 0) or 0)
    used = int(record.get("memory_used_bytes", 0) or 0)
    free = int(record.get("memory_free_bytes", max(0, total - used)) or 0)

    gpu_util_percent = float(record.get("gpu_utilization_percent", 0) or 0)
    memory_ratio = record.get("memory_usage_ratio")
    if memory_ratio is None:
        memory_ratio = round(used / total, 4) if total else 0.0

    record["gpu_utilization_ratio"] = round(gpu_util_percent / 100.0, 4)
    record["gpu_memory_usage_ratio"] = round(float(memory_ratio or 0), 4)
    record["gpu_memory_total_bytes"] = total
    record["gpu_memory_used_bytes"] = used
    record["gpu_memory_free_bytes"] = free
    record["gpu_power_usage_watts"] = float(record.get("power_watts", 0) or 0)
    record["gpu_temperature"] = float(record.get("temperature_c", 0) or 0)
    return record
