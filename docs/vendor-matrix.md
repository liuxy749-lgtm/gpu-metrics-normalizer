# Vendor Matrix

| 厂商 | 型号/系列 | exporter | 默认端口 | 已知原始指标 | 归一化输出 | 状态 |
|---|---|---|---:|---|---|---|
| NVIDIA | H100/A800/H20/A100/V100/H800/B200/4090/3090 | dcgm-exporter | 9400/21001 | `DCGM_FI_DEV_GPU_TEMP`, `DCGM_FI_DEV_POWER_USAGE`, `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_FB_USED`, `DCGM_FI_DEV_FB_FREE`, `DCGM_FI_DEV_MEM_COPY_UTIL` | temperature, power, util, mem used/free/total/ratio | 已验证 |
| 华为昇腾 | 910B/910C | npu-exporter | 8100/21001 | 现场已验证标准输出；原始 exporter 指标名需补样例 | temperature, power, util, mem used/total/ratio | 已验证输出，待补原始映射 |
| 天数智芯 | BIV100/BIV150/MRV100/TGV200 | ix-exporter | 21001 | `ix_gpu_temperature`, `ix_power_usage`, `ix_gpu_utilization`, `ix_mem_total`, `ix_mem_used` | temperature, power, util, mem total/used | 已验证 |
| 摩尔线程 | S5000 | mtgpu-exporter | 21001 | `mtgpu_gpu_temp`, `mtgpu_power_usage_milliwatts`, `mtgpu_gpu_utilization`, `mtgpu_memory_total_bytes`, `mtgpu_memory_used_bytes` | temperature, power, util, mem total/used | 已验证 |
| 沐曦 | MC550 | mx-exporter | 8100/21001 | `core_temp`, `bway_power`, `gpu_usage`, `memory_total`, `memory_used` | temperature, power, util, mem total/used | 已验证 |
| 昆仑芯 | P800 | xpu-exporter | 9507/21001 | 现场已验证标准输出；原始 exporter 指标名需补样例 | temperature, power, util, mem total/used | 已验证输出，待补原始映射 |
| 海光 | BW1000/BW200/DCU | dcu-exporter | 9507/21001 | `dcu_temp`, `dcu_power_usage`, `dcu_utilizationrate`, `dcu_memorycap_bytes`, `dcu_usedmemory_bytes`, `dcu_memory_remaining` | temperature, power, util, mem total/used/free/ratio | 已验证 |
| 清微 | TX81/TX8110 | tx-exporter | 21001 | `TSINGMICRO_KUIPER_TEMP`, `TSINGMICRO_KUIPER_POWER_USAGE`, `TSINGMICRO_KUIPER_MEMORY_TOTAL`, `TSINGMICRO_KUIPER_MEMORY_USING`, `TSINGMICRO_KUIPER_UTILIZATION`, `TSINGMICRO_KUIPER_HEALTH_STATUS` | temperature, power, util, mem total/used, state | 已验证 |
| 燧原 | S60 | enflame/s60 exporter | 21001 | 现场已验证标准输出；原始 exporter 指标名需补样例 | temperature, power, util, mem total/used | 已验证输出，待补原始映射 |
| 寒武纪 | MLU590 | mlu-exporter | 21001 | `mlu_*` | temperature, power, util, mem total/used | 可选保留 |

## 当前中心 Prometheus 已见归一化 gpu_type

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
