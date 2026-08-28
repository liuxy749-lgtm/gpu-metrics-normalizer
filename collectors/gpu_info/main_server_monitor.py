#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主监控采集服务 - main_server_monitor.py
=======================================
功能:
  1. 检查机器型号类型 (物理机 / 虚拟机, 基于 DMI)
  2. 检测 GPU 厂商与型号, 自动选择对应的 vendor 采集脚本
  3. 每 INTERVAL_SECONDS 秒调用 vendor 脚本 --json 采集一次并上报

上报方式 (env.conf 配置):
  REPORT_MODE=http   -> HTTP POST JSON 到 REPORT_URL
  REPORT_MODE=local  -> 仅写本地日志

依赖: 仅标准库; vendor 脚本来自同目录 env.conf 的 GPU_INFO_DIR
用法:
  python3 main_server_monitor.py           # 前台运行
  nohup python3 main_server_monitor.py &   # 后台运行
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

from gpu_model_mapping import add_standard_metric_names

# ---------------- 路径与配置 ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_CONF = os.path.join(BASE_DIR, "env.conf")

CONFIG = {
    "GPU_INFO_DIR": BASE_DIR,
    "INTERVAL_SECONDS": 30,
    "REPORT_MODE": "http",
    "REPORT_URL": "",
    "REPORT_TOKEN": "",
    "LOG_DIR": "/var/log/gpu-monitor",
    "LOG_FILE": "gpu_monitor.log",
    "FORCE_RUN": 0,
    "SCRIPT_TIMEOUT": 30,
    "HOST_IP": "",
    "ENABLE_DEVICE_ID": "0",
}


def load_env_conf():
    """读取 env.conf (KEY=VALUE, # 注释)"""
    if not os.path.exists(ENV_CONF):
        print("[warn] env.conf 不存在, 使用默认配置", file=sys.stderr)
        return
    with open(ENV_CONF, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k in CONFIG:
                CONFIG[k] = v
    # 类型转换
    for key in ("INTERVAL_SECONDS", "FORCE_RUN", "SCRIPT_TIMEOUT"):
        try:
            CONFIG[key] = int(CONFIG[key])
        except (TypeError, ValueError):
            print("[warn] %s 配置非法, 使用默认值: %s" % (key, CONFIG[key]), file=sys.stderr)
            CONFIG[key] = 30 if key != "FORCE_RUN" else 0
    os.environ["ENABLE_DEVICE_ID"] = str(CONFIG.get("ENABLE_DEVICE_ID", "0"))


def log(msg):
    """写日志 (控制台 + 本地文件)"""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line, flush=True)
    try:
        logdir = CONFIG["LOG_DIR"]
        if not os.path.isdir(logdir):
            os.makedirs(logdir, exist_ok=True)
        with open(os.path.join(logdir, CONFIG["LOG_FILE"]), "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def run_cmd(cmd, timeout=30):
    """兼容 Python <3.7 的 subprocess 封装, 返回 stdout"""
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, _ = p.communicate(timeout=timeout)
        return out.decode("utf-8", "replace")
    except Exception as e:
        log("[err] 执行命令失败: %s -> %s" % (cmd[:80], e))
        return ""


def run_argv(argv, timeout=30):
    """执行 argv 形式命令, 避免 shell 解析路径或参数。"""
    try:
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=timeout)
        if p.returncode != 0 and err:
            log("[warn] 命令退出码 %s: %s" % (p.returncode, err.decode("utf-8", "replace")[:200]))
        return out.decode("utf-8", "replace")
    except Exception as e:
        log("[err] 执行命令失败: %s -> %s" % (" ".join(argv), e))
        return ""


# ---------------- 机器类型检测 ----------------
def read_dmi(name):
    try:
        with open("/sys/class/dmi/id/" + name, "r", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return ""


def detect_machine_type():
    """物理机/虚拟机: DMI product_name + sys_vendor 关键字"""
    product = (read_dmi("product_name") + " " + read_dmi("sys_vendor")).lower()
    vm_keywords = ("kvm", "qemu", "vmware", "virtual", "bochs", "openstack",
                   "nova", "virtualbox", "xen", "microsoft", "hyper-v", "bhyve")
    return "vm" if any(k in product for k in vm_keywords) else "physical"


def get_primary_ip():
    if CONFIG.get("HOST_IP"):
        return CONFIG["HOST_IP"]
    try:
        target_host = urllib.parse.urlparse(CONFIG.get("REPORT_URL", "")).hostname or "8.8.8.8"
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target_host, 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception:
        return ""


# ---------------- GPU 厂商检测 ----------------
# 厂商标识: (检测命令/文件, 匹配函数, vendor 脚本相对路径)
VENDOR_RULES = [
    # NVIDIA: nvidia-smi 在 PATH
    ("which nvidia-smi", lambda out: "nvidia-smi" in out,
     "nvidia/nvidia_gpu_info.py", "nvidia"),
    # 华为昇腾: npu-smi
    ("which npu-smi", lambda out: "npu-smi" in out,
     "huawei/ascend_910c_info.py", "ascend"),
    # 天数智芯: ixsmi (可能在 corex 目录, 用 find)
    ("find /usr/local -maxdepth 3 -name ixsmi 2>/dev/null | head -1",
     lambda out: "ixsmi" in out,
     "tianshu/tianshu_iluvatar_info.py", "tianshu"),
    # 摩尔线程: mthreads-gmi
    ("which mthreads-gmi", lambda out: "mthreads-gmi" in out,
     "moer/moer_s5000_info.py", "moore"),
    # 沐曦: mx-smi
    ("which mx-smi", lambda out: "mx-smi" in out,
     "muxi/muxi_mc550.py", "muxi"),
    # 平头哥: ppu-smi
    ("which ppu-smi", lambda out: "ppu-smi" in out,
     "pingtouge/ppu_zw810e_info.py", "pingtouge"),
    # 昆仑芯: xpu-smi
    ("which xpu-smi", lambda out: "xpu-smi" in out,
     "kunlunxin/kunlunxin_p800_info.py", "kunlun"),
    # 清微: tsm_smi
    ("which tsm_smi", lambda out: "tsm_smi" in out,
     "qingwei/qingwei_tx81_info.py", "qingwei"),
    # 曦望: pt_smi
    ("which pt_smi", lambda out: "pt_smi" in out,
     "xiwang/sunrise_s2_info.py", "xiwang"),
    # 燧原: efsmi
    ("which efsmi", lambda out: "efsmi" in out,
     "suiyuan/enflame_s60_info.py", "enflame"),
]


def detect_gpu_vendor():
    """返回 (vendor 名, 脚本相对路径) 或 (None, None)"""
    # 先走 SMI 工具检测
    for rule in VENDOR_RULES:
        cmd, match, script, vendor = rule[:4]
        out = run_cmd(cmd, timeout=10)
        if match(out):
            return vendor, script
    # 海光 sysfs 兜底: vendor 0x1d94
    try:
        for d in os.listdir("/sys/class/drm/"):
            if d.startswith("card") and d[4:].isdigit():
                dev = "/sys/class/drm/%s/device/vendor" % d
                with open(dev) as f:
                    if f.read().strip() == "0x1d94":
                        return "hygon", "haiguang/hygon_bw1000_info.py"
    except Exception:
        pass
    return None, None


# ---------------- 采集与上报 ----------------
def collect_gpu(vendor, script):
    """调用 vendor 脚本 --json 采集, 返回 (gpus 列表, 错误信息)"""
    script_path = os.path.join(CONFIG["GPU_INFO_DIR"], script)
    if not os.path.exists(script_path):
        return None, "vendor 脚本不存在: %s" % script_path
    out = run_argv([sys.executable, script_path, "--json"], timeout=CONFIG["SCRIPT_TIMEOUT"])
    if not out.strip():
        return None, "vendor 脚本无输出"
    try:
        # 解析第一个完整 JSON 值 (脚本 stdout 可能有 warning 前缀)
        raw = out.strip()
        starts = [idx for idx in (raw.find("["), raw.find("{")) if idx >= 0]
        if not starts:
            return None, "JSON 起始符不存在"
        raw = raw[min(starts):]
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(raw)
        if isinstance(obj, list):
            return obj, ""
        return None, "JSON 格式非列表"
    except Exception as e:
        return None, "JSON 解析失败: %s (输出前200: %s)" % (e, out[:200])


def build_payload(gpus, vendor):
    """组装上报数据"""
    gpus = [add_standard_metric_names(g) for g in gpus]
    total = 0
    used = 0
    free = 0
    util_sum = 0.0
    util_ratio_sum = 0.0
    memory_ratio_sum = 0.0
    power_sum = 0.0
    temperature_sum = 0.0
    n = len(gpus)
    for g in gpus:
        total += g.get("gpu_memory_total_bytes", g.get("memory_total_bytes", 0))
        used += g.get("gpu_memory_used_bytes", g.get("memory_used_bytes", 0))
        free += g.get("gpu_memory_free_bytes", g.get("memory_free_bytes", 0))
        util_sum += g.get("gpu_utilization_percent", 0)
        util_ratio_sum += g.get("gpu_utilization_ratio", 0)
        memory_ratio_sum += g.get("gpu_memory_usage_ratio", g.get("memory_usage_ratio", 0))
        power_sum += g.get("gpu_power_usage_watts", g.get("power_watts", 0))
        temperature_sum += g.get("gpu_temperature", g.get("temperature_c", 0))
    avg_util_ratio = round(util_ratio_sum / n, 4) if n else 0.0
    avg_memory_ratio = round(memory_ratio_sum / n, 4) if n else 0.0
    avg_power = round(power_sum / n, 2) if n else 0.0
    avg_temperature = round(temperature_sum / n, 2) if n else 0.0
    return {
        "hostname": socket.gethostname(),
        "ip": get_primary_ip(),
        "machine_type": detect_machine_type(),
        "gpu_vendor": vendor,
        "gpu_model": gpus[0].get("gpu_type", "") if n else "",
        "gpu_count": n,
        "gpu_memory_total_bytes": total,
        "gpu_memory_used_bytes": used,
        "gpu_memory_free_bytes": free,
        "gpu_memory_usage_ratio": round(used / total, 4) if total else avg_memory_ratio,
        "avg_gpu_utilization_ratio": avg_util_ratio,
        "avg_gpu_power_usage_watts": avg_power,
        "avg_gpu_temperature": avg_temperature,
        "memory_total_bytes": total,
        "memory_used_bytes": used,
        "memory_usage_ratio": round(used / total, 4) if total else 0.0,
        "avg_gpu_utilization_percent": round(util_sum / n, 2) if n else 0.0,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gpus": gpus,
    }


def report(payload):
    """上报: http POST / local 日志"""
    if CONFIG["REPORT_MODE"] == "http" and CONFIG["REPORT_URL"]:
        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(CONFIG["REPORT_URL"], data=body,
                                         headers={"Content-Type": "application/json"})
            if CONFIG["REPORT_TOKEN"]:
                req.add_header("Authorization", "Bearer " + CONFIG["REPORT_TOKEN"])
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.getcode()
                if code != 200:
                    log("[report] HTTP %s" % code)
        except Exception as e:
            log("[report] 上报失败: %s" % e)
    else:
        log("[report-local] %s" % json.dumps(payload, ensure_ascii=False)[:500])


# ---------------- 主循环 ----------------
def main():
    load_env_conf()
    log("===== main_server_monitor 启动 =====")
    log("配置文件: %s" % ENV_CONF)
    log("采集间隔: %ds  上报模式: %s" % (CONFIG["INTERVAL_SECONDS"], CONFIG["REPORT_MODE"]))

    machine_type = detect_machine_type()
    log("机器类型: %s" % machine_type)

    vendor, script = detect_gpu_vendor()
    log("GPU 厂商: %s  采集脚本: %s" % (vendor or "未检测到", script or "-"))

    if not CONFIG["FORCE_RUN"]:
        if machine_type != "physical":
            log("[exit] 非物理机(%s), 不采集, 退出。如需强制运行请设置 env.conf FORCE_RUN=1" % machine_type)
            sys.exit(0)
        if not vendor:
            log("[exit] 未检测到 GPU, 不采集, 退出。")
            sys.exit(0)
    elif not vendor:
        log("[warn] FORCE_RUN=1 但未检测到 GPU 厂商")

    log("开始每 %ds 采集上报一次 (Ctrl+C 退出)" % CONFIG["INTERVAL_SECONDS"])
    while True:
        t0 = time.time()
        gpus, err = collect_gpu(vendor, script)
        if err:
            log("[collect] 采集失败: %s" % err)
        elif gpus:
            payload = build_payload(gpus, vendor)
            log("[collect] %s: %d 卡, GPU利用率 %.1f%%, 显存 %.2f/%.2f GiB"
                % (payload["gpu_model"], payload["gpu_count"],
                   payload["avg_gpu_utilization_percent"],
                   payload["memory_used_bytes"] / 1073741824,
                   payload["memory_total_bytes"] / 1073741824))
            report(payload)
        # 精确间隔
        elapsed = time.time() - t0
        sleep = CONFIG["INTERVAL_SECONDS"] - elapsed
        if sleep > 0:
            time.sleep(sleep)


if __name__ == "__main__":
    main()
