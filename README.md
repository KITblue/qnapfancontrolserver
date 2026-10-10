# QNAP Fan Control — 威联通 NAS 定制风扇管理

![logo](logo.png)

为威联通（QNAP）NAS 定制的智能风扇与温度管理软件：温控曲线、多风扇管理、实时硬件监控，从源码合并 [FanControlServer](https://github.com/guan-ry/FanControlServerApp) 与 [qnap8528 驱动](https://github.com/iamiao/8528)，安装时自动携带 IT8528 驱动，开箱即用。

## 关于

**QNAP Fan Control** 面向威联通（QNAP）NAS 用户，在开源项目 FanControlServer 基础上做品牌定制，并将 qnap8528 驱动（QNAP IT8528 EC 内核驱动）作为依赖集成，实现"安装风扇面板即自动安装驱动"。

- 🌬️ 风扇控制：独立设置每个风扇的智能温控曲线，手动/自动随时切换，0‑255 精确 PWM
- 🌡️ 硬件监控：CPU/GPU/内存/硬盘温度与使用率、NVMe/SATA 温度、历史温度曲线
- 🔔 安全机制：过热强制全速、停转温差防频繁启停、登录态 + 管理员写保护
- 🔧 IT8528 驱动：qnap8528-kmod 内核驱动随应用自动安装（DKMS 编译加载），支持风扇控制、温度传感器、LED、按键和 VPD 读取
- ⚙️ 深色 Web 界面：响应式、WebSocket 实时推送，经 fnOS 网关 /app/FanControlServer 访问

## 仓库结构

```
qnapfancontrolserver/
├── backend/                  # FanControlServer Go 后端（交叉编译 linux/amd64）
├── frontend/                 # FanControlServer Web 前端（Vite，构建到 backend/web）
├── app/                      # fnOS 应用运行时布局（server/、target/）
├── cmd/                      # fnOS 生命周期钩子（安装/卸载/升级/启停）
├── config/                   # fnOS 应用配置与权限
├── wizard/                   # 安装向导
├── docs/                     # 上游文档与截图
├── drivers/
│   └── qnap8528-kmod/        # qnap8528 驱动源码（DKMS 内核模块 + 独立 FPK 打包）
├── manifest                  # FanControlServer manifest（install_dep_apps = qnap8528-kmod）
├── scripts/
│   ├── build.sh              # 从源码构建：前端 → 后端 → 驱动 FPK → 主应用 FPK
│   └── gen_fnpack.py         # 读取 dist/ 构建产物，生成 FnDepot V2 索引 fnpack.json
├── icons/                    # 商店图标
├── logo.png                  # 项目 logo
└── fnpack.json               # FnDepot V2 索引（CI 生成，勿手改）
```

## 源码构建

本仓库不再下载上游 FPK 重打包，而是从源码编译构建：

```bash
chmod +x scripts/build.sh
./scripts/build.sh
```

构建流程：

1. `frontend`：`npm install && npm run build` → 产物输出到 `backend/web`
2. `backend`：`GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build` → `app/server/fancontrolserver`
3. `drivers/qnap8528-kmod`：`python3 build-driver-fpk.py` → `qnap8528-kmod_1.24.3_x86.fpk`
4. 主应用：`fnpack build`（manifest 已声明 `install_dep_apps = qnap8528-kmod`）
5. 全部 FPK 汇总到 `dist/`，由 CI 上传 Release 并生成 `fnpack.json`

## 自动同步（CI）

`.github/workflows/sync.yml` 每日自动执行（cron `3 9 * * *`，即北京时间 17:03），也支持 `workflow_dispatch` 手动触发：

- Checkout 源码 → 编译前端 → 交叉编译后端 → 构建 qnap8528 驱动 FPK → `fnpack build` 构建主应用 FPK
- 自动上传两个 FPK 到本仓库 Release `v1.3.7.1`（`--clobber` 替换旧资产）
- 基于本地构建产物重新生成 `fnpack.json` 并提交到 `main`

跟踪上游更新：上游（guan-ry/FanControlServerApp、iamiao/8528）发新版本后，手动合并源码更新并触发 workflow 即可重新构建发布。

## 快速使用

1. 打开飞牛应用商店 → 第三方商店 → 添加源
2. 粘贴 JSON 直链（最稳）：
   ```
   https://raw.githubusercontent.com/KITblue/qnapfancontrolserver/main/fnpack.json
   ```
3. 搜到 **QNAP Fan Control** → 安装（会自动安装 qnap8528 驱动）

> 国内加速直链（备选）：`https://cdn.jsdelivr.net/gh/KITblue/qnapfancontrolserver@main/fnpack.json`

## 技术细节

- `fnpack.json` 为 V2 规范；FanControlServer 与 qnap8528-kmod 均指向本仓库 Release 中从源码构建的 FPK
- 展示名与介绍为品牌定制（QNAP Fan Control），由 manifest 与 `gen_fnpack.py` 统一维护；应用安装身份 `appname` 保持 `FanControlServer` 不变，已安装用户可持续收到更新
- 主应用 manifest 声明 `install_dep_apps = qnap8528-kmod`，fnOS 安装器会自动先装驱动
- 源仓库名 `qnapfancontrolserver`，FnDepot 客户端在 GitHub 仓库模式下可能要求仓库名为 FnDepot，因此**建议用 JSON 直链添加**

## 免责声明

- 非官方项目，与飞牛 fnOS 官方团队无任何关联
- 驱动涉及内核模块和系统权限，请确保已备份重要数据
- 仅供技术爱好者和威联通用户折腾使用
- 上游 FanControlServer 与 qnap8528 代码均遵循其原始 LICENSE，本仓库做源码整合与品牌封装

---

**维护者**：[KITblue](https://github.com/KITblue)  
**问题反馈**：[GitHub Issues](https://github.com/KITblue/qnapfancontrolserver/issues)
