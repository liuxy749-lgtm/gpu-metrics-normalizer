# GPU OTel Normalization Templates

这套配置用于把不同厂商 GPU/NPU/加速卡 exporter 的 Prometheus 指标，通过 OpenTelemetry Collector 归一化为一组统一指标，便于中心 Prometheus、Grafana、资源治理平台和告警系统统一消费。

本仓库只关注“厂商 exporter 原始指标 → OpenTelemetry Collector → 标准化 `gpu_*` 指标”的归一化方案，不包含资产系统、团队归属、资源分配或内部部署节点信息。

当前现场已验证归一化输出覆盖：

- NVIDIA：H100、A800、H20、A100、V100、H800、B200、4090、3090
- 华为昇腾：910B、910C
- 天数智芯：BIV100、BIV150、MRV100、TGV200
- 摩尔线程：S5000
- 沐曦：MC550
- 昆仑芯：P800
- 海光：BW1000、BW200/DCU
- 清微：TX81、TX8110
- 燧原：S60
- 寒武纪：MLU590（如需保留，可继续补配置）

> 开源前注意：本目录中的配置均已去掉现场 IP、内网域名、临时下载链接、账号密码，只保留通用映射逻辑和占位符。

## 统一输出指标

所有厂商最终统一为以下指标：

| 指标名 | 单位 | 说明 |
|---|---:|---|
| `gpu_temperature` | ℃ | 卡温度 |
| `gpu_utilization_ratio` | 1 | GPU/NPU/加速卡利用率，推荐范围 0-1 |
| `gpu_memory_usage_ratio` | 1 | 显存/HBM/VRAM 使用率，推荐范围 0-1 |
| `gpu_memory_total_bytes` | bytes | 显存总量 |
| `gpu_memory_used_bytes` | bytes | 显存已用 |
| `gpu_memory_free_bytes` | bytes | 显存空闲，可选 |
| `gpu_power_usage_watts` | watts | 当前功耗 |
| `gpu_state` | vendor-specific | 健康状态/错误状态，可选 |

统一标签：

| 标签 | 说明 |
|---|---|
| `ip` | 机器 IP，建议作为跨系统主键 |
| `hostname` | 主机名 |
| `dev_id` | 卡编号 |
| `gpu_vendor` | 厂商，如 `nvidia`、`huawei`、`kunlunxin` |
| `gpu_type` | 卡型号 |
| `region` | 地域/资源池 |
| `zone` | 可用区/机房 |
| `site` | 站点标识 |

## 目录结构

```text
gpu-otel-normalization/
├── README.md
├── configs/
│   ├── all-vendors-template.yaml
│   └── vendors/
│       ├── nvidia-dcgm.yaml
│       ├── huawei-ascend.yaml
│       ├── iluvatar-tianshu.yaml
│       ├── mthreads-s5000.yaml
│       ├── muxi-mc550.yaml
│       ├── kunlunxin-p800.yaml
│       ├── hygon-dcu.yaml
│       ├── tsingmicro-tx.yaml
│       └── enflame-s60.yaml
├── examples/
│   ├── docker-compose.yaml
│   └── otel.env.example
├── scripts/
│   └── validate-promql.sh
└── docs/
    └── vendor-matrix.md
```

## 快速启动

1. 准备 exporter。

   每台 GPU 机器上先启动对应厂商 exporter，例如：

   - NVIDIA：`dcgm-exporter`
   - 华为：`npu-exporter`
   - 天数：`ix-exporter`
   - 摩尔：`mtgpu-exporter`
   - 沐曦：`mx-exporter`
   - 昆仑芯：`xpu-exporter`
   - 海光：`dcu-exporter`
   - 清微：`tx-exporter`
   - 燧原：`s60/enflame exporter`

2. 修改 OTel 配置里的 targets。

   ```yaml
   static_configs:
     - targets:
         - 10.0.0.1:21001
         - 10.0.0.2:21001
       labels:
         region: example-region
         zone: example-zone
   ```

3. 设置中心 Prometheus OTLP 地址。

   ```bash
   cp examples/otel.env.example .env
   vim .env
   ```

4. 启动 OTel Collector。

   ```bash
   docker compose -f examples/docker-compose.yaml --env-file .env up -d
   ```

5. 检查标准指标。

   ```promql
   count by(gpu_vendor,gpu_type)(gpu_utilization_ratio)
   count by(gpu_vendor,gpu_type)(gpu_memory_total_bytes)
   count by(gpu_vendor,gpu_type)(gpu_power_usage_watts)
   count by(gpu_vendor,gpu_type)(gpu_temperature)
   ```

## 开源前 TODO

- [ ] 为华为昇腾、昆仑芯、燧原补充更多原始 exporter 样例输出。
- [ ] 为每个厂商增加 `sample-metrics/*.prom` 样例文件。
- [ ] 增加 OTel Collector 配置 CI 校验。
- [ ] 补充 Grafana dashboard 示例。

## 现场经验

1. 归一化层只负责输出稳定的 `gpu_*` 指标名和基础标签，不负责资产归属、团队归属或项目归属。
2. `ip`、`hostname`、`dev_id`、`gpu_vendor`、`gpu_type` 是建议保留的最小定位标签。
3. 如果 exporter 只提供 used/free，不提供 total，用 OTel `metricsgeneration` 生成：

   ```text
   gpu_memory_total_bytes = gpu_memory_used_bytes + gpu_memory_free_bytes
   ```

4. 如果 exporter 只提供 used/total，不提供 ratio，用 OTel `metricsgeneration` 生成：

   ```text
   gpu_memory_usage_ratio = gpu_memory_used_bytes / gpu_memory_total_bytes
   ```

5. 单位要在 OTel 层统一：

   ```text
   utilization / memory_usage_ratio: 0-1
   memory_total / memory_used / memory_free: bytes
   power: watts
   temperature: celsius
   ```
