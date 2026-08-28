#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主机信息采集 Exporter
=====================
采集主机信息并以 Prometheus 文本格式暴露在 HTTP 端口，供 OTEL Collector
(prometheus receiver) 抓取后上传到中心 Prometheus。

指标:
  node_host_info{hostname, ip, machine_type, board_manufacturer, board_serial}  恒为 1
  node_cpu_usage_percent       CPU 使用率 (%)
  node_memory_usage_percent    内存使用率 (%)
  node_load_avg_5m             5 分钟平均负载
  node_scrape_errors           采集错误计数(排查用)

machine_type: physical=物理机 / vm=虚拟机(含 KVM/VMware/QEMU/OpenStack 等)
物理机额外输出主板厂商(board_manufacturer)。主板 SN 默认脱敏，
设置 ENABLE_DEVICE_ID=1 后才输出。

用法:
  python3 host_info_exporter.py                 # 默认端口 9101
  HOST_INFO_PORT=9200 python3 host_info_exporter.py
  HOST_INFO_INTERVAL=15 python3 host_info_exporter.py   # 采集间隔秒数
"""
import os
import socket
import sys
import time

import psutil
from prometheus_client import Gauge, start_http_server, REGISTRY

PORT = int(os.environ.get("HOST_INFO_PORT", "9101"))
INTERVAL = int(os.environ.get("HOST_INFO_INTERVAL", "10"))
ENABLE_DEVICE_ID = os.environ.get("ENABLE_DEVICE_ID", "0").lower() in ("1", "true", "yes", "on")
HOST_IP = os.environ.get("HOST_IP", "").strip()

# DMI 路径
DMI = "/sys/class/dmi/id"


def read_dmi(name: str) -> str:
    """读 /sys/class/dmi/id/<name>，失败返回空串"""
    try:
        with open(os.path.join(DMI, name), "r", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return ""


def detect_machine_type() -> str:
    """判断虚拟机/物理机：靠 DMI product_name + sys_vendor 关键字"""
    product = (read_dmi("product_name") + " " + read_dmi("sys_vendor")).lower()
    vm_keywords = (
        "kvm", "qemu", "vmware", "virtual", "bochs", "openstack",
        "nova", "virtualbox", "xen", "microsoft", "hyper-v", "bhyve",
    )
    return "vm" if any(k in product for k in vm_keywords) else "physical"


def get_primary_ip() -> str:
    """取本机非回环主 IP。可通过 HOST_IP 显式指定。"""
    if HOST_IP:
        return HOST_IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""
    finally:
        s.close()


def main():
    hostname = socket.gethostname()
    ip = get_primary_ip()
    machine_type = detect_machine_type()
    board_vendor, board_serial = "", ""
    if machine_type == "physical":
        board_vendor = read_dmi("board_vendor")
        board_serial = read_dmi("board_serial") if ENABLE_DEVICE_ID else ""
        # fallback: dmidecode（部分机型 /sys/class/dmi 权限受限）
        if not board_vendor or (ENABLE_DEVICE_ID and not board_serial):
            try:
                import subprocess
                for key, opt in (("board_vendor", "baseboard-manufacturer"),
                                 ("board_serial", "baseboard-serial-number")):
                    if key == "board_vendor" and board_vendor:
                        continue
                    if key == "board_serial" and (board_serial or not ENABLE_DEVICE_ID):
                        continue
                    out = subprocess.run(["dmidecode", "-s", opt],
                                         capture_output=True, text=True, timeout=5)
                    val = out.stdout.strip() if out.returncode == 0 else ""
                    if key == "board_vendor":
                        board_vendor = val
                    else:
                        board_serial = val
            except Exception:
                pass

    print(f"[host-info-exporter] hostname={hostname} ip={ip} "
          f"machine_type={machine_type} board_vendor={board_vendor} "
          f"board_serial={board_serial} port={PORT} interval={INTERVAL}s",
          flush=True)

    # 主机信息：全部用 Gauge（不用 INFO 类型，避免 OTEL→VM 400 丢弃）
    host_info = Gauge(
        "node_host_info",
        "主机基本信息(恒为1)，标签含主机名/IP/类型/主板信息",
        ["hostname", "ip", "machine_type", "board_manufacturer", "board_serial"],
    )
    cpu_g = Gauge("node_cpu_usage_percent", "CPU 使用率(%)")
    mem_g = Gauge("node_memory_usage_percent", "内存使用率(%)")
    load5_g = Gauge("node_load_avg_5m", "5 分钟平均负载")
    err_g = Gauge("node_scrape_errors", "采集错误次数")

    start_http_server(PORT, addr="0.0.0.0")
    print(f"[host-info-exporter] listening on :{PORT}/metrics", flush=True)

    while True:
        try:
            cpu_g.set(psutil.cpu_percent(interval=1))
            mem_g.set(psutil.virtual_memory().percent)
            load5_g.set(os.getloadavg()[1])
            host_info.labels(hostname=hostname, ip=ip,
                             machine_type=machine_type,
                             board_manufacturer=board_vendor,
                             board_serial=board_serial).set(1)
        except Exception as e:
            err_g.inc()
            print(f"[host-info-exporter] scrape error: {e}", flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
