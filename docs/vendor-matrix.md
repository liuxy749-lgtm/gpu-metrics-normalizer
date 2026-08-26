# Vendor Matrix

> 端口说明：表中的端口是部署时常见的采集端口示例，不代表厂商 exporter 的固定默认端口。实际端口应以你的 exporter 启动参数和 OTel `targets` 配置为准。

| 厂商 | 型号/系列 | exporter | 采集端口示例 | 当前配置文件 | 原始指标映射完整度 | 归一化输出 | 状态 |
|---|---|---|---|---|---|---|---|
| NVIDIA | H100/A800/H20/A100/V100/H800/B200/4090/3090 | dcgm-exporter | 可自定义，如 `9400`、`21001` | `configs/vendors/nvidia-dcgm.yaml` | 完整 | temperature, power, util, mem used/free/total/ratio, state | 已验证 |
| 华为昇腾 | 910B/910C | npu-exporter | 可自定义，如 `8100`、`21001` | `configs/vendors/huawei-ascend.yaml` | 待补充原始 exporter 样例；当前保留标准化模板 | temperature, power, util, mem used/total/ratio | 已验证输出，待补原始映射 |
| 天数智芯 | BIV100/BIV150/MRV100/TGV200 | ix-exporter | 可自定义，如 `21001` | `configs/vendors/iluvatar-tianshu.yaml` | 完整 | temperature, power, util, mem total/used/ratio | 已验证 |
| 摩尔线程 | S5000 | mtgpu-exporter | 可自定义，如 `21001` | `configs/vendors/mthreads-s5000.yaml` | 完整 | temperature, power, util, mem total/used/ratio | 已验证 |
| 沐曦 | MC550 | mx-exporter | 可自定义，如 `8100`、`21001` | `configs/vendors/muxi-mc550.yaml` | 完整 | temperature, power, util, mem total/used/ratio | 已验证 |
| 昆仑芯 | P800 | xpu-exporter | 可自定义，如 `9507`、`21001` | `configs/vendors/kunlunxin-p800.yaml` | 待补充原始 exporter 样例；当前保留标准化模板 | temperature, power, util, mem total/used/ratio | 已验证输出，待补原始映射 |
| 海光 | BW1000/BW200/DCU | dcu-exporter | 可自定义，如 `9507`、`21001` | `configs/vendors/hygon-dcu.yaml` | 完整 | temperature, power, util, mem total/used/free/ratio | 已验证 |
| 清微 | TX81/TX8110 | tx-exporter | 可自定义，如 `21001` | `configs/vendors/tsingmicro-tx.yaml` | 完整 | temperature, power, util, mem total/used/ratio, state | 已验证 |
| 燧原 | S60 | enflame/s60 exporter | 可自定义，如 `21001` | `configs/vendors/enflame-s60.yaml` | 待补充原始 exporter 样例；当前保留标准化模板 | temperature, power, util, mem total/used/ratio | 已验证输出，待补原始映射 |
| 寒武纪 | MLU590 | 待确认 | 待确认 | 暂无 | 待定 | 暂不提供 | 暂未配置 |

## 原始指标映射

### NVIDIA / DCGM

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `DCGM_FI_DEV_GPU_TEMP` | `gpu_temperature` | GPU 温度 |
| `DCGM_FI_DEV_POWER_USAGE` | `gpu_power_usage_watts` | 当前功耗 |
| `DCGM_FI_DEV_GPU_UTIL` | `gpu_utilization_ratio` | GPU 利用率，配置中统一到 0-1 |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | `gpu_memory_usage_ratio` | 显存/内存控制器利用率，配置中统一到 0-1 |
| `DCGM_FI_DEV_FB_USED` | `gpu_memory_used_bytes` | 显存已用 |
| `DCGM_FI_DEV_FB_FREE` | `gpu_memory_free_bytes` | 显存空闲 |
| `DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE` | `gpu_memory_total_bytes` | 通过 OTel 生成总显存 |
| `DCGM_FI_DEV_XID_ERRORS` | `gpu_state` | XID 错误状态 |

### 天数智芯 / Iluvatar

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `ix_gpu_temperature` | `gpu_temperature` | 卡温度 |
| `ix_power_usage` | `gpu_power_usage_watts` | 当前功耗 |
| `ix_gpu_utilization` | `gpu_utilization_ratio` | GPU 利用率，配置中统一到 0-1 |
| `ix_mem_total` | `gpu_memory_total_bytes` | 显存总量 |
| `ix_mem_used` | `gpu_memory_used_bytes` | 显存已用 |
| `ix_mem_used / ix_mem_total` | `gpu_memory_usage_ratio` | 通过 OTel 生成显存使用率 |

### 摩尔线程 / MThreads

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `mtgpu_gpu_temp` | `gpu_temperature` | GPU 温度 |
| `mtgpu_power_usage_milliwatts` | `gpu_power_usage_watts` | 功耗，配置中从 milliwatts 转 watts |
| `mtgpu_gpu_utilization` | `gpu_utilization_ratio` | GPU 利用率，配置中统一到 0-1 |
| `mtgpu_memory_total_bytes` | `gpu_memory_total_bytes` | 显存总量 |
| `mtgpu_memory_used_bytes` | `gpu_memory_used_bytes` | 显存已用 |
| `mtgpu_memory_used_bytes / mtgpu_memory_total_bytes` | `gpu_memory_usage_ratio` | 通过 OTel 生成显存使用率 |

### 沐曦 / Muxi

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `core_temp` | `gpu_temperature` | 核心温度 |
| `bway_power` | `gpu_power_usage_watts` | 当前功耗；配置中保留 `wayId="0"` |
| `gpu_usage` | `gpu_utilization_ratio` | GPU 利用率，配置中统一到 0-1 |
| `memory_total` | `gpu_memory_total_bytes` | 显存总量；配置中保留 `memType="vram"` |
| `memory_used` | `gpu_memory_used_bytes` | 显存已用；配置中保留 `memType="vram"` |
| `memory_used / memory_total` | `gpu_memory_usage_ratio` | 通过 OTel 生成显存使用率 |

### 海光 / Hygon DCU

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `dcu_temp` | `gpu_temperature` | DCU 温度 |
| `dcu_power_usage` | `gpu_power_usage_watts` | 当前功耗 |
| `dcu_utilizationrate` | `gpu_utilization_ratio` | DCU 利用率，配置中统一到 0-1 |
| `dcu_memorycap_bytes` | `gpu_memory_total_bytes` | 显存总量 |
| `dcu_usedmemory_bytes` | `gpu_memory_used_bytes` | 显存已用 |
| `dcu_memory_remaining` | `gpu_memory_free_bytes` | 显存空闲 |
| `dcu_usedmemory_bytes / dcu_memorycap_bytes` | `gpu_memory_usage_ratio` | 通过 OTel 生成显存使用率 |

### 清微 / Tsingmicro

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `TSINGMICRO_KUIPER_TEMP` | `gpu_temperature` | 卡温度 |
| `TSINGMICRO_KUIPER_POWER_USAGE` | `gpu_power_usage_watts` | 当前功耗 |
| `TSINGMICRO_KUIPER_UTILIZATION` | `gpu_utilization_ratio` | GPU 利用率，配置中统一到 0-1 |
| `TSINGMICRO_KUIPER_MEMORY_TOTAL` | `gpu_memory_total_bytes` | 显存总量 |
| `TSINGMICRO_KUIPER_MEMORY_USING` | `gpu_memory_used_bytes` | 显存已用 |
| `TSINGMICRO_KUIPER_MEMORY_USING / TSINGMICRO_KUIPER_MEMORY_TOTAL` | `gpu_memory_usage_ratio` | 通过 OTel 生成显存使用率 |
| `TSINGMICRO_KUIPER_HEALTH_STATUS` | `gpu_state` | 健康状态 |

### 华为昇腾、昆仑芯、燧原

这三类目前仓库中保留的是标准化模板，适用于已经输出或已经被预处理为 `gpu_*` 标准指标的 exporter 链路。严格的“原始 exporter 指标名 → `gpu_*`”映射需要补充对应 exporter 的 `/metrics` 样例后再固化。

### 寒武纪 / Cambricon

寒武纪 MLU590 暂不提供 OTel 配置。原因是当前没有可确认的原始 exporter 指标样例，不能把 `mlu_*` 这类泛化写法当成可用配置发布。

## 已验证过的归一化 gpu_type 示例

示例：

- `NVIDIA H100 80GB HBM3`
- `NVIDIA A800-SXM4-80GB`
- `NVIDIA A100-SXM4-40GB`
- `Tesla V100-PCIE-32GB`
- `Tesla V100-SXM2-32GB`
- `bm-nvidia-h20-96g`
- `bm-nvidia-h20-3e-141g`
- `bm-ascend-910b-64g`
- `Ascend910-Ascend-V1`
- `Iluvatar BI-V150 OAM`
- `Iluvatar TG-V200 OAM`
- `MTT S5000`
- `沐曦-MC550-64G`
- `P800 OAM`
- `海光-BW1000-64G`
- `BW200`
- `TX8110-256-00`
- `Enflame_S60-48GB`
