# Vendor Matrix

> 端口说明：表中的端口是部署时常见的采集端口示例，不代表厂商 exporter 的固定默认端口。实际端口应以你的 exporter 启动参数和 OTel `targets` 配置为准。

| 厂商 | 型号/系列 | exporter | 采集端口示例 | 当前配置文件 | 原始指标映射完整度 | 归一化输出 | 状态 |
|---|---|---|---|---|---|---|---|
| NVIDIA | H100/A800/H20/A100/V100/H800/B200/4090/3090 | dcgm-exporter | 可自定义，如 `9400`、`21001` | `configs/vendors/nvidia-dcgm.yaml` | 完整 | temperature, power, util, mem used/free/total/ratio, state | 已验证 |
| 华为昇腾 | 910B/910C | npu-exporter | 可自定义，如 `8100`、`21001` | `configs/vendors/huawei-ascend.yaml` | 完整 | temperature, power, util, mem used/total/ratio, hbm temp/bandwidth, state, clocks | 已验证 |
| 天数智芯 | BIV100/BIV150/MRV100/TGV200 | ix-exporter | 可自定义，如 `21001` | `configs/vendors/iluvatar-tianshu.yaml` | 完整 | temperature, power, util, mem total/used/ratio | 已验证 |
| 摩尔线程 | S5000 | mtgpu-exporter | 可自定义，如 `21001` | `configs/vendors/mthreads-s5000.yaml` | 完整 | temperature, power, util, mem total/used/ratio | 已验证 |
| 沐曦 | MC550 | mx-exporter | 可自定义，如 `8100`、`21001` | `configs/vendors/muxi-mc550.yaml` | 完整 | temperature, power, util, mem total/used/ratio | 已验证 |
| 昆仑芯 | P800 | xpu-exporter | 可自定义，如 `9507`、`21001` | `configs/vendors/kunlunxin-p800.yaml` | 完整 | temperature, power, util, mem total/used/free/ratio, state, xid/ecc/link | 已验证 |
| 海光 | BW1000/BW200/DCU | dcu-exporter | 可自定义，如 `9507`、`21001` | `configs/vendors/hygon-dcu.yaml` | 完整 | temperature, power, util, mem total/used/free/ratio | 已验证 |
| 清微 | TX81/TX8110 | tx-exporter | 可自定义，如 `21001` | `configs/vendors/tsingmicro-tx.yaml` | 完整 | temperature, power, util, mem total/used/ratio, state | 已验证 |
| 燧原 | S60 | gcu-exporter | 可自定义，如 `21001` | `configs/vendors/enflame-s60.yaml` | 完整 | temperature, power, util, mem total/used/ratio, state, clocks, ecc | 已验证 |
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

### 昆仑芯 / Kunlunxin P800

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `node_xpu_temp` | `gpu_temperature` | XPU 温度 |
| `node_xpu_powerUsage` | `gpu_power_usage_watts` | 当前功耗 |
| `node_xpu_utilization` | `gpu_utilization_ratio` | XPU 利用率，配置中统一到 0-1 |
| `node_xpu_memtotal` | `gpu_memory_total_bytes` | 显存总量 |
| `node_xpu_memused` | `gpu_memory_used_bytes` | 显存已用 |
| `node_xpu_memfree` | `gpu_memory_free_bytes` | 显存空闲 |
| `node_xpu_memutil` | `gpu_memory_usage_ratio` | 显存使用率，配置中统一到 0-1 |
| `node_xpu_state` | `gpu_state` | 设备状态 |
| `node_xpu_xidCount` | `gpu_xid_errors_total` | XID 错误计数 |
| `node_xpu_totalEccCorrectedErrors` | `gpu_ecc_corrected_errors_total` | ECC 可纠正错误计数 |
| `node_xpu_totalEccUncorrectedErrors` | `gpu_ecc_uncorrected_errors_total` | ECC 不可纠正错误计数 |
| `node_xpu_xpuLinkState` | `gpu_link_state` | XPU Link 状态 |

当前 Prometheus 中还可见以下昆仑芯原始指标，暂不进入核心五项归一化输出，可按需扩展：

```text
node_xpu_clock
node_xpu_computeRunningProcesses
node_xpu_currentEccMode
node_xpu_cxpuInstanceCount
node_xpu_cxpuMaxInstanceCount
node_xpu_cxpuMemoryFree
node_xpu_cxpuMemoryTotal
node_xpu_cxpuMemoryUsed
node_xpu_l3free
node_xpu_l3total
node_xpu_l3used
node_xpu_l3util
node_xpu_pendingEccMode
node_xpu_xpuDevicesNum
```

### 燧原 / Enflame S60

已验证的 S60 原始 exporter 为 `local/gcu-exporter:1.5.21`，监听端口可通过启动参数自定义。样例中 exporter 使用 `--web.listen-address=:21001`，原始指标前缀为 `enflame_gcu_*`。

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `enflame_gcu_temperatures` | `gpu_temperature` | GCU 温度 |
| `enflame_gcu_power_consumption` | `gpu_power_usage_watts` | 当前功耗，单位 watts |
| `enflame_gcu_usage` | `gpu_utilization_ratio` | GCU 利用率，配置中统一到 0-1 |
| `enflame_gcu_memory_total_bytes` | `gpu_memory_total_bytes` | 显存总量 |
| `enflame_gcu_memory_used_bytes` | `gpu_memory_used_bytes` | 显存已用 |
| `enflame_gcu_memory_usage` | `gpu_memory_usage_ratio` | 显存使用率，配置中统一到 0-1 |
| `enflame_gcu_health` | `gpu_state` | 健康状态；样例中 `healthmsg="Healthy"` 时值为 `2` |
| `enflame_gcu_clock` | `gpu_clock_mhz` | GCU 核心频率 |
| `enflame_gcu_cluster_usage` | `gpu_cluster_usage_ratio` | Cluster 利用率，配置中统一到 0-1 |
| `enflame_gcu_sip_usage` | `gpu_sip_usage_ratio` | SIP 利用率，配置中统一到 0-1 |
| `enflame_gcu_power_capability` | `gpu_power_capability_watts` | 功耗能力/功耗上限 |
| `enflame_gcu_power_usage` | `gpu_power_usage_ratio` | 功耗占比，配置中统一到 0-1；不要当作 watts 使用 |
| `enflame_gcu_ecc_single_bit_error_total_count` | `gpu_ecc_corrected_errors_total` | ECC 单比特错误累计计数 |
| `enflame_gcu_ecc_double_bit_error_total_count` | `gpu_ecc_uncorrected_errors_total` | ECC 双比特错误累计计数 |
| `enflame_gcu_exporter_up` | `gpu_exporter_up` | exporter 采集状态 |
| `enflame_gcu_count` | `machine_gpu_count` | 机器 GCU 数量 |

样例中确认的关键标签：

```text
minor_number -> dev_id
name         -> gpu_type
host         -> hostname
uuid         -> device UUID
busid        -> PCI bus path
```

当前样例中还可见以下燧原原始指标，可按需扩展：

```text
enflame_gcu_info
enflame_gcu_pcie_link_width
enflame_gcu_pcie_max_link_width
enflame_gcu_scrape_collector_duration_seconds
enflame_gcu_scrape_collector_success
enflame_gcu_virt_mode
gcu_exporter_build_info
```

### 华为昇腾 / Huawei Ascend 910B/910C

| 原始指标 | 归一化指标 | 说明 |
|---|---|---|
| `npu_chip_info_temperature` | `gpu_temperature` | NPU 芯片温度 |
| `npu_chip_info_power` | `gpu_power_usage_watts` | 当前功耗 |
| `npu_chip_info_ai_core_utilization` | `gpu_utilization_ratio` | AI Core 利用率，配置中统一到 0-1 |
| `npu_chip_info_hbm_total_memory` | `gpu_memory_total_bytes` | HBM 总量 |
| `npu_chip_info_hbm_used_memory` | `gpu_memory_used_bytes` | HBM 已用 |
| `npu_chip_info_hbm_utilization` | `gpu_memory_usage_ratio` | HBM 使用率，配置中统一到 0-1 |
| `npu_chip_info_hbm_temperature` | `gpu_hbm_temperature` | HBM 温度 |
| `npu_chip_info_health_status` | `gpu_state` | 健康状态 |
| `npu_chip_info_aicore_current_freq` | `gpu_clock_mhz` | AI Core 当前频率 |
| `npu_chip_info_bandwidth_rx` | `gpu_pcie_rx_bytes` | 接收带宽/流量指标，具体单位以 exporter 为准 |
| `npu_chip_info_bandwidth_tx` | `gpu_pcie_tx_bytes` | 发送带宽/流量指标，具体单位以 exporter 为准 |
| `npu_chip_info_hbm_bandwidth_utilization` | `gpu_hbm_bandwidth_ratio` | HBM 带宽利用率，配置中统一到 0-1 |
| `machine_npu_nums` | `machine_npu_nums` | 机器 NPU 数量，透传辅助指标 |

当前样例中还可见以下华为原始指标，可按需扩展到网络、HCCS、RoCE、光模块、ECC 等告警：

```text
npu_chip_info_hbm_ecc_double_bit_error_cnt
npu_chip_info_hbm_ecc_single_bit_error_cnt
npu_chip_info_hbm_ecc_total_double_bit_error_cnt
npu_chip_info_hbm_ecc_total_single_bit_error_cnt
npu_chip_info_hccs_bandwidth_info_total_rx
npu_chip_info_hccs_bandwidth_info_total_tx
npu_chip_info_link_status
npu_chip_info_network_status
npu_chip_info_overall_utilization
npu_chip_info_process_info
npu_chip_info_process_info_num
npu_chip_info_serial_number
npu_chip_info_utilization
npu_chip_info_vector_utilization
npu_chip_info_voltage
npu_chip_link_speed
npu_chip_link_up_num
npu_chip_optical_state
npu_chip_roce_rx_err_pkt_num
npu_chip_roce_tx_err_pkt_num
npu_exporter_version_info
```

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
