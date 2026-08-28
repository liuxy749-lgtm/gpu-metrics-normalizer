# GPU Info Collectors

`gpu_info` 是一组轻量级主机侧采集脚本，用于把不同厂商 GPU/NPU/加速卡的本地 SMI 输出转换为统一 JSON。它适合用于快速巡检、边缘节点自采集，或作为 OpenTelemetry 归一化链路之外的补充采集方式。

这组脚本不依赖厂商私有 SDK，只调用机器上已经安装的厂商命令行工具或公开的 Linux sysfs 文件。

## 支持范围

| 厂商 | 脚本 | 数据源 |
|---|---|---|
| NVIDIA | `nvidia/nvidia_gpu_info.py` | `nvidia-smi` |
| 华为昇腾 | `huawei/ascend_910c_info.py` | `npu-smi` |
| 天数智芯 | `tianshu/tianshu_iluvatar_info.py` | `ixsmi` |
| 摩尔线程 | `moer/moer_s5000_info.py` | `mthreads-gmi` |
| 沐曦 | `muxi/muxi_mc550.py` | `mx-smi` |
| 昆仑芯 | `kunlunxin/kunlunxin_p800_info.py` | `xpu-smi` |
| 海光 DCU | `haiguang/hygon_bw1000_info.py` | `/sys/class/drm` + `hwmon` |
| 清微 | `qingwei/qingwei_tx81_info.py` | `tsm_smi` |
| 燧原 | `suiyuan/enflame_s60_info.py` | `efsmi` |
| 平头哥 | `pingtouge/ppu_zw810e_info.py` | `ppu-smi` |
| 曦望 | `xiwang/sunrise_s2_info.py` | `pt_smi` |

## 统一 JSON 字段

每张卡会输出标准字段：

| 字段 | 说明 | 单位 |
|---|---|---|
| `gpu_type` | 归一化后的 GPU 型号 | string |
| `gpu_utilization_ratio` | GPU 利用率 | 0-1 |
| `gpu_memory_usage_ratio` | 显存使用率 | 0-1 |
| `gpu_memory_total_bytes` | 显存总量 | bytes |
| `gpu_memory_used_bytes` | 显存已用 | bytes |
| `gpu_memory_free_bytes` | 显存空闲 | bytes |
| `gpu_power_usage_watts` | 当前功耗 | watts |
| `gpu_temperature` | 当前温度 | celsius |

## 型号归一化

不同厂商工具返回的型号名并不稳定，例如同一类卡可能出现空格、大小写、后缀不同的写法。`gpu_model_mapping.py` 维护这些别名，并统一输出稳定的 `gpu_type`。

如果需要扩展新型号，只需要在 `MODEL_ALIASES` 或 `contains_rules` 中补充映射。

## 隐私与资产标识

设备 SN、UUID、unique_id、主板序列号都属于资产可识别信息。开源版本默认不输出这些字段的值。

如确实需要用于内部资产定位，可以显式开启：

```bash
ENABLE_DEVICE_ID=1 python3 nvidia/nvidia_gpu_info.py --json
```

主服务也支持在 `env.example` 中设置：

```text
ENABLE_DEVICE_ID=1
```

## 使用方式

单独运行某个厂商脚本：

```bash
python3 nvidia/nvidia_gpu_info.py --json
python3 suiyuan/enflame_s60_info.py --json
```

自动探测厂商并周期上报：

```bash
cp env.example env.conf
python3 main_server_monitor.py
```

主服务会自动检测 GPU 厂商，并调用对应的 vendor 脚本生成 JSON payload。

## 配置

`env.example` 是示例配置。不要把包含真实上报地址、token 或内部路径的 `env.conf` 提交到仓库。

常用配置项：

| 配置 | 说明 |
|---|---|
| `GPU_INFO_DIR` | `gpu_info` 脚本目录 |
| `INTERVAL_SECONDS` | 采集间隔 |
| `REPORT_MODE` | `http` 或 `local` |
| `REPORT_URL` | HTTP 上报地址 |
| `REPORT_TOKEN` | 可选鉴权 token |
| `HOST_IP` | 手动指定上报 IP |
| `ENABLE_DEVICE_ID` | 是否输出 SN/UUID 等设备唯一标识 |

## 依赖

GPU vendor 脚本只依赖 Python 标准库和对应厂商 SMI 工具。

`host_info_exporter.py` 是可选主机信息 exporter，额外依赖：

```text
psutil
prometheus_client
```

## 说明

- 燧原 S60 的显存 total/used/free 来自 `efsmi -q -d MEMORY --json-format` 的 `Device Mem Info`。
- 海光 DCU 脚本直接读取 sysfs，不依赖 `dcu-smi` 或 `dcu-exporter`。
- 天数脚本会自动发现 `/usr/local/corex-*/bin/ixsmi`，避免硬编码 corex 版本。
