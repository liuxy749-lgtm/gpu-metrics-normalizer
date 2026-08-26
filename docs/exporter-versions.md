# Exporter Versions

本文记录本仓库归一化配置验证过的 exporter 版本或镜像标签。这里的版本号表示“已验证过该版本的指标输出格式”，不表示配置只能用于该版本。实际部署时，如果 exporter 的指标名、标签名或单位发生变化，需要同步调整对应的 OTel processor。

## 已验证版本

| 厂商 | 型号/系列 | exporter | 已验证版本 / 镜像标签 | 备注 |
|---|---|---|---|---|
| NVIDIA | H100、A800、H20、A100、V100、H800、B200、4090、3090 | dcgm-exporter | `4.6.0` | 基于 DCGM exporter 指标族 `DCGM_FI_DEV_*`。部分环境使用自定义构建补充 `gpu_memory_total_bytes`，OTel 配置也支持通过 used/free 生成 total。 |
| 华为昇腾 | 910B、910C | npu-exporter | `ascendai/npu-exporter:v7.3.1-arm64` | 基于 `npu_chip_info_*` 指标族验证。 |
| 天数智芯 | BIV100、BIV150、MRV100、TGV200 | ix-exporter | 待补充 | 已验证 `ix_*` 指标族。当前没有可公开确认的镜像 tag，建议部署方在使用时补充实际版本。 |
| 摩尔线程 | S5000 | mtgpu-exporter | 待补充 | 已验证 `mtgpu_*` 指标族。当前没有可公开确认的镜像 tag，建议部署方在使用时补充实际版本。 |
| 沐曦 | MC550 | mx-exporter | `cr.metax-tech.com/cloud/mx-exporter:0.14.2-amd64` | 基于 `core_temp`、`gpu_usage`、`memory_*` 等指标验证。 |
| 昆仑芯 | P800 | xpu-exporter | 待补充 | 已验证 `node_xpu_*` 指标族。当前没有可公开确认的镜像 tag，建议部署方在使用时补充实际版本。 |
| 海光 | BW1000、BW200/DCU | dcu-exporter | `dcu-exporter:v2.4.1` | 基于 `dcu_*` 指标族验证。实际镜像仓库名称可能随交付环境不同而变化。 |
| 清微 | TX81、TX8110 | tx-exporter | `v2.5.0` | 基于 TX8100/TX8110 系列 `TSINGMICRO_KUIPER_*` 指标验证。 |
| 燧原 | S60 | gcu-exporter | `local/gcu-exporter:1.5.21` | 基于 `enflame_gcu_*` 指标族验证。 |
| 寒武纪 | MLU590 | 待确认 | 待确认 | 当前没有可确认的 exporter 指标样例，本仓库暂不提供寒武纪配置。 |

## OpenTelemetry Collector

仓库中的示例配置按 OpenTelemetry Collector Contrib `0.112.0` 编写和验证。若使用更高版本，建议重点检查以下组件的兼容性：

- `prometheus` receiver
- `filter` processor
- `metricstransform` processor
- `transform` processor
- `metricsgeneration` processor
- `otlphttp` exporter

这些组件的语法整体较稳定，但不同版本的 OTTL 函数、错误处理行为和 processor 执行顺序仍建议在预发环境先验证。
