#!/usr/bin/env bash
set -euo pipefail

log_dir="${ORDERRUN_LOG_DIR:-/home/ubuntu/orderrun/logs}"
config_path="${ORDERRUN_LOGROTATE_CONFIG:-/etc/logrotate.d/orderrun}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo to write ${config_path}" >&2
  exit 1
fi

mkdir -p "${log_dir}/nginx"

cat >"${config_path}" <<EOF
${log_dir}/nginx/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

echo "Installed logrotate config: ${config_path}"
