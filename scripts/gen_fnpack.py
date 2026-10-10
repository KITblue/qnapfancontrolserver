#!/usr/bin/env python3
"""
gen_fnpack.py — 基于本地构建产物生成 FnDepot V2 索引 fnpack.json

单应用模式：从 dist/ 下的 FPK 读取 manifest，计算 sha256/size，生成 fnpack.json。

用法
  CI（GitHub Actions）:
      python scripts/gen_fnpack.py
  本地:
      python scripts/gen_fnpack.py

输出
  <repo>/fnpack.json
"""

import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── 配置 ────────────────────────────────────────────────────────────────────

REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "KITblue/qnapfancontrolserver")
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_SLUG}/main"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "fnpack.json"
DIST = ROOT / "dist"

APP_VERSION = os.environ.get("APP_VERSION", "1.3.7.1")
APP_ASSET = os.environ.get("APP_ASSET", f"FanControlServer-v{APP_VERSION}-qnapfancontrol-iframe.fpk")

SOURCE_INFO = {
    "name": "QNAP Fan Control",
    "author": "KITblue",
    "homepage": f"https://github.com/{REPO_SLUG}",
    "description": "威联通（QNAP）NAS 定制风扇管理：集成 IT8528 驱动，一键安装自动携带驱动，支持温控曲线、多风扇管理与实时硬件监控。",
}

APP_OVERRIDES = {
    "display_name": "QNAP Fan Control",
    "desc": "<b>QNAP Fan Control</b> 是为威联通（QNAP）NAS 定制的智能风扇与温度管理软件，集成 <b>qnap8528 驱动</b>（QNAP IT8528 EC 内核驱动），开箱即用。<br><br>📁 <b>风扇控制：</b><br>- 独立设置每个风扇的智能温控曲线<br>- 手动/自动模式随时切换，支持 0‑255 精确 PWM 值<br>- 自动扫描硬件 PWM 通道，支持多风扇管理<br><br>🌡️ <b>硬件监控：</b><br>- 实时 CPU/GPU/内存/硬盘温度及使用率<br>- 支持 NVMe/SATA 硬盘温度读取<br>- 历史温度曲线图表（ECharts）<br><br>🔔 <b>安全机制：</b><br>- 可配置过热阈值，超限强制全速运转<br>- 停转温差防止频繁启停<br>- 系统登录态 + 管理员写保护<br><br>🔧 <b>IT8528 驱动（qnap8528-kmod）：</b><br>- QNAP IT8528 EC 内核驱动，支持风扇控制、温度传感器、LED、按键和 VPD 读取<br>- 随本应用自动安装，开箱即用<br>- 内核升级后自动通过 DKMS 为新内核重新编译<br><br>⚙️ <b>其他特点：</b><br>- 响应式 Web 界面，深色主题<br>- WebSocket 实时推送，无需手动刷新<br>- 通过系统统一网关访问：/app/FanControlServer（需 fnOS V1.1.31+）<br><br>🐛 <b>反馈与支持：</b><a href=\"https://github.com/KITblue/qnapfancontrolserver/issues\" target=\"_blank\">GitHub Issues</a>",
}


# ── 基础工具 ────────────────────────────────────────────────────────────────(
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(fp: Path) -> dict:
    with tarfile.open(fp, "r:gz") as t:
        raw = t.extractfile("manifest").read().decode("utf-8", errors="replace")
    out = {}
    for line in raw.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


# ── 主逻辑 ───────────────────────────────────────────────────────────

def main():
    if not DIST.is_dir():
        raise SystemExit(f"错误: 未找到构建产物目录 {DIST}，请先运行 scripts/build.sh 或 CI 构建步骤")

    fpk_path = DIST / APP_ASSET
    if not fpk_path.exists():
        raise SystemExit(f"错误: 未找到构建产物 {fpk_path}")

    manifest = read_manifest(fpk_path)
    version = manifest["version"]
    size = fpk_path.stat().st_size
    sha256 = sha256_of(fpk_path)
    download_url = f"https://github.com/{REPO_SLUG}/releases/download/v{version}/{APP_ASSET}"

    entry = {
        "display_name": manifest.get("display_name", "FanControlServer"),
        "desc": manifest.get("desc", ""),
        "platform": [manifest.get("platform", "x86")],
        "categories": ["系统工具"],
        "icon_url": f"{RAW_BASE}/icons/fancontrol.png",
        "run_as": "root",
        "install_type": "",
        "is_docker": False,
        "maintainer": manifest.get("maintainer", "KITblue"),
        "maintainer_url": manifest.get("maintainer_url", f"https://github.com/{REPO_SLUG}"),
        "distributor": manifest.get("distributor", "KITblue"),
        "distributor_url": manifest.get("distributor_url", f"https://github.com/{REPO_SLUG}"),
        "desktop_uidir": manifest.get("desktop_uidir", ""),
        "desktop_applaunchname": manifest.get("desktop_applaunchname", ""),
        "releases": {
            version: {
                "packages": {
                    "x86": {
                        "download_url": download_url,
                        "sha256": sha256,
                        "size": size,
                    }
                }
            }
        },
    }
    entry.update(APP_OVERRIDES)

    fnpack = {
        "schema_version": "2",
        "source_info": SOURCE_INFO,
        "apps": {
            "FanControlServer": entry,
        },
    }

    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(fnpack, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"生成: {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    print(f"[FanControlServer] {APP_ASSET} ({size} bytes, sha256 {sha256[:12]}…)")

if __name__ == "__main__":
    main()
