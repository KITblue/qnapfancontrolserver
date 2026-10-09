#!/usr/bin/env bash
# 飞牛 fnOS 应用打包前构建（合并项目 qnapfancontrolserver）
# 从源码构建：前端 → Go 后端 → 打包主应用 FPK（qnap8528 驱动源码已内置在 app/qnap8528-src，随包安装）
# 用法（在仓库根目录）：chmod +x scripts/build.sh && ./scripts/build.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$ROOT"

step() {
  printf '\n==> %s\n' "$1"
}

step "构建前端"
( cd "${ROOT}/frontend" && npm install && npm run build )

if [[ ! -f "${ROOT}/backend/web/index.html" ]]; then
  echo "错误: 未找到 backend/web/index.html" >&2
  exit 1
fi

# 确保 target 目录存在（用于 Unix Socket）
mkdir -p "${ROOT}/app/target"

step "交叉编译后端 (linux/amd64) -> app/server/fancontrolserver"
mkdir -p "${ROOT}/app/server"
APP_VERSION="$(grep -E '^[[:space:]]*version[[:space:]]*=' "${ROOT}/manifest" | head -1 | sed 's/.*=[[:space:]]*//')"
LDFLAGS="-s -w -X fancontrolserver/internal/version.Version=${APP_VERSION}"
( cd "${ROOT}/backend" && go mod tidy && GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "${LDFLAGS}" -o "${ROOT}/app/server/fancontrolserver" . )

step "打包 fnOS 应用 (fnpack build)"
# 在项目根目录下打包（qnap8528 驱动源码随 app/qnap8528-src 内置，由 cmd/service-setup 安装）
( cd "${ROOT}" && fnpack build )

# 将生成的 .fpk 文件移动到 dist 目录
mkdir -p "${ROOT}/dist"
fpk_file=$(find "${ROOT}" -maxdepth 1 -name "*.fpk" -type f | head -1)
if [[ -n "$fpk_file" ]]; then
  mv "$fpk_file" "${ROOT}/dist/"
  echo "移动安装包到 ${ROOT}/dist/$(basename "$fpk_file")"
else
  echo "错误: 未找到生成的 .fpk 文件" >&2
  exit 1
fi

echo ""
echo "完成。产物:"
echo "  二进制: app/server/fancontrolserver"
echo "  安装包: dist/*.fpk（已内置 qnap8528 驱动源码，安装时自动编译安装，卸载时自动移除）"