#!/usr/bin/env bash
set -euo pipefail

PROM_URL="${PROM_URL:-http://127.0.0.1:9090}"

queries=(
  'count(gpu_utilization_ratio)'
  'count(gpu_memory_total_bytes)'
  'count(gpu_memory_used_bytes)'
  'count(gpu_power_usage_watts)'
  'count(gpu_temperature)'
  'count by(gpu_vendor,gpu_type)(gpu_utilization_ratio)'
)

for query in "${queries[@]}"; do
  echo ">>> ${query}"
  curl -fsS -G "${PROM_URL}/api/v1/query" --data-urlencode "query=${query}"
  echo
done

