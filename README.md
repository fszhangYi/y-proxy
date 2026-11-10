# Y-Proxy

局域网代理共享桌面端：把**已联网机器（出站端）**的出口，交给同网段的**入网端**使用。

典型场景：Windows 上已有 VPN / 代理客户端（如 mihomo /「七七」）只能本机用时，用 Y-Proxy 在局域网开中转，让另一台 Linux / Windows 通过 HTTP(S) 代理上网。

> 详细逐步操作（端口探测、防火墙、终端 `export`、agent 等）见 **[manual.md](./manual.md)**。

## 功能

- **出站端**：检测本机局域网 IP 与本地代理端口，可选放行防火墙，启动 TCP 中转到局域网监听端口
- **入网端**：填写出站端 IP/端口，Ping / TCP / 上网测试，复制 `export` 与带代理启动命令，配置本进程代理
- **跨平台**：自动识别 Windows / Linux；界面与打包均支持两端
- **独立交付**：Windows 单文件 exe；Linux AppImage（Ubuntu 20.04 / glibc 2.31）

## 截图与界面

登录固定窗口 → 选择「出站端 / 入网端」→ 对应操作页（科幻风 Fluent 深色主题）。

演示账户：`admin` / `admin`

## 快速开始（开发）

依赖：Python 3.11+（建议官方 CPython，打包勿用 conda）

```bash
pip install -r requirements.txt
python run_app.py
```

Windows 示例：

```powershell
& "C:\Users\user\miniconda3\python.exe" c:\Users\user\Desktop\y-proxy\run_app.py
```

## 使用流程（简版）

1. 在**已能上网**的机器上打开 Y-Proxy，登录后选 **出站端**
2. 确认本地代理端口（如 `127.0.0.1:9674`），必要时放行防火墙，点 **启动中转**
3. 把本机局域网 IP + 监听端口告诉另一台机器
4. 在**需要上网**的机器上选 **入网端**，填出站端 IP/端口，测试连通后配置终端或进程代理

注意：

- 入网端不要填 `127.0.0.1`，也不要填手机热点 / `169.254.x.x` 链路本地地址
- 进程代理只影响本应用及其子进程；已在跑的程序需重启后才能看到新环境变量
- `ping` 通常不走 HTTP 代理

## 打包

### Windows 单文件 exe

使用官方 CPython 创建的 `build\packvenv`（不要用 Miniconda 直接打）：

```powershell
.\scripts\pack-windows.ps1
```

产物：`dist\Y-Proxy-<时间戳>.exe`（目标机无需安装 Python / Qt）

### Linux AppImage（Docker + Ubuntu 20.04）

需本机 Docker Desktop 已启动：

```powershell
.\scripts\pack-linux-via-docker.ps1
```

产物：`dist-release\linux-x64\`

- `Y-Proxy-*-x86_64.AppImage`
- 备用 `Y-Proxy-*-linux-x64.tar.gz`

目标 Ubuntu 20.04+ x86_64：

```bash
chmod +x Y-Proxy-*-x86_64.AppImage
./Y-Proxy-*-x86_64.AppImage
```

## 目录结构

```text
app/                 # 桌面端（登录 / 角色 / 出站 / 入网）
  services/          # OS 检测、中转、客户端代理辅助
packaging/           # PyInstaller spec、运行时钩子、图标
scripts/             # pack-windows.ps1 / pack-linux-via-docker.ps1
docker/              # Ubuntu 20.04 打 AppImage 的 Dockerfile
lan_relay.py         # 命令行 TCP 中转（可不依赖 GUI）
manual.md            # 完整手工操作备忘
run_app.py           # 桌面端入口
```

## 技术栈

- Python 3 + **PyQt6** + **PyQt6-Fluent-Widgets**
- 本地 TCP 转发（`lan_relay` / `RelayServer`）
- 打包：PyInstaller；Linux 经 Docker 产出 AppImage

## 许可与说明

本仓库用于个人 / 内网代理共享场景。请遵守当地网络与软件许可规定；第三方 VPN / 代理客户端的使用以其自身协议为准。
