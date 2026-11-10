# 让 Linux 通过这台 Windows 上网

## 桌面端（PyQt-Fluent-Widgets）

跨平台桌面程序在 `app/`，启动：

```powershell
& "C:\Users\user\miniconda3\python.exe" c:\Users\user\Desktop\y-proxy\run_app.py
```

Linux：

```bash
python3 run_app.py
```

依赖见 `requirements.txt`（本机已装 `PyQt6` + `PyQt6-Fluent-Widgets`）。演示登录：`admin` / `admin`。

登录后选择：

- **出站端**：本机已能上网时使用。检测本机代理端口、放行防火墙、启动局域网中转。
- **入网端**：本机需要借用局域网出口时使用。填写出站端 IP 和端口，测试连通/上网，复制终端代理命令。

程序会识别当前是 Windows 还是 Linux；两边界面都能打开，防火墙放行主要在 Windows 上有意义。

### 打包（无依赖交付）

- **Windows 单文件 exe**（官方 CPython 虚拟环境，勿用 conda）：

```powershell
.\scripts\pack-windows.ps1
```

产物在 `dist\Y-Proxy-时间戳.exe`。

- **Linux AppImage**（Docker Desktop + Ubuntu 20.04，glibc 2.31）：

```powershell
.\scripts\pack-linux-via-docker.ps1
```

产物在 `dist-release\linux-x64\`（`*.AppImage` 与备用 `*.tar.gz`）。目标机无需 Docker / Python / Qt。

---

## 命令行备忘（可选）

若不用桌面端，仍可用下面的手工步骤。Windows 上的「七七」目前只肯给自己用；`lan_relay.py` 在 Windows 上开一扇门，Linux 从这扇门进来，流量再交给七七。

做完以后，Linux 上的浏览器和 `curl` 可以上网，并走七七当前选中的节点。整台 Linux 的全部流量不会自动接进 VPN。`ping` 也不走这条路。

两台机器要同时开着：Windows 上「七七」不要退出，`lan_relay.py` 那个黑窗口不要关。

## 这台电脑上该填哪个地址

2026-11-03 查到的地址如下。Linux 要填的是「交换机」这一行，不要填手机那一行。

| 网卡 | 地址 | 能不能给 Linux 填 |
| --- | --- | --- |
| 交换机 | `192.168.1.33` | 可以。Linux 自己的地址也是 `192.168.1.x` 时用这个 |
| 交换机 | `192.168.0.2` | 可以。Linux 自己的地址是 `192.168.0.x` 时用这个 |
| 以太网 2（苹果手机） | `172.20.10.5` | 不要填。这是手机数据线的地址 |
| 以 `169.254` 开头的地址 | 例如 `169.254.2.130` | 不要填 |

下面的例子先用 `192.168.1.33`。如果你的 Linux 是 `192.168.0.x`，把例子里的 `192.168.1.33` 全部换成 `192.168.0.2`。

## 第一步：确认七七还开着

看「七七」窗口：

- 「虚拟网卡」是蓝色打开状态。保持这样，不用去开「系统代理」。
- 节点列表里有一个选中的节点，例如「A香港0」，右边是「正常」。

然后在 Windows 上打开 PowerShell，粘贴下面这一句：

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 9674,9675,9676 } | Select-Object LocalAddress, LocalPort
```

要看到三行，地址都是 `127.0.0.1`，端口是 `9674`、`9675`、`9676`。

没有这三行：先打开七七，确认已经登录，虚拟网卡是开的，再执行一次。还是没有，就先停在这里，不要继续。

## 第二步：给 17890 端口放行

用管理员身份打开 PowerShell：开始菜单里搜 `PowerShell`，右键，选「以管理员身份运行」。粘贴：

```powershell
netsh advfirewall firewall add rule name="y-proxy-17890" dir=in action=allow protocol=TCP localport=17890 remoteip=192.168.0.0/24,192.168.1.0/24
```

成功时最后一行是 `确定。`

这条命令只做一次。以后重启电脑不用再做。

## 第三步：启动中转程序

普通 PowerShell 就可以，不必是管理员。不要只写 `python`。这台电脑上直接写 `python` 会碰到微软商店留下的占位程序，窗口没有任何输出。`py` 也没有安装。

粘贴下面这一整行：

```powershell
& "C:\Users\user\miniconda3\python.exe" c:\Users\user\Desktop\y-proxy\lan_relay.py
```

窗口里应出现这一行，并且窗口停在那里：

```text
listening ('0.0.0.0', 17890) -> 127.0.0.1:9674
```

这个窗口一直开着。关掉它，Linux 就断网。

如果提示找不到这个路径，在资源管理器地址栏输入 `C:\Users\user\miniconda3`，看里面有没有 `python.exe`。没有的话，先停在这里。

## 第四步：在 Linux 上确认能碰到 Windows

在 Linux 终端执行：

```bash
ping -c 3 192.168.1.33
```

能看到 `ttl=` 和应答时间，说明两台机器在同一个网上。

一直是超时：先看 Linux 自己的地址。

```bash
ip -4 addr
```

- 地址是 `192.168.0.x`：改 ping `192.168.0.2`，后面的命令也改用这个地址。
- 地址既不是 `192.168.1.x` 也不是 `192.168.0.x`：Linux 没接在这台 Windows 的交换机上，先把网线接到同一台交换机，或接到这台 Windows 的网口上。

`ping` 超时但地址段是对的：Windows 经常不回应 ping。继续做第五步。

## 第五步：在 Linux 上测试上网

把下面两行粘贴到 Linux 终端。地址按第四步的结果，用 `192.168.1.33` 或 `192.168.0.2`。

```bash
curl -x http://192.168.1.33:17890 https://ifconfig.me
echo
```

成功时，屏幕上是一串公网 IP，例如一串不是 `192.168` 开头的数字，然后光标回到下一行。

Windows 上出现 `open ('192.168.1.22', ...)` 只说明 Linux 碰到了这扇门。网页开没打开，要看 Linux 这条命令自己打印出了什么。只看到 open 和 close，不能算成功。

失败时对照：

| Linux 上看到的 | 含义 | 处理 |
| --- | --- | --- |
| `Connection refused` | Windows 的 17890 没在听 | 回到第三步，确认那行 `listening` 还在 |
| `Connection timed out` 或一直卡住 | 网不通，或防火墙没放行 | 重做第二步，并确认第四步的地址 |
| `Failed to connect` 里提到 `127.0.0.1` | 地址填成了 Linux 自己 | 改成 Windows 的 `192.168.1.33` 或 `192.168.0.2` |
| 立刻返回一个 `192.168` 或 `172.20` 开头的地址 | 请求没走七七 | 看七七是否还开着，虚拟网卡是否还是蓝色 |

## 第六步：让这个终端里的程序都走代理

第五步的 `curl -x` 只影响这一条命令。要让同一个终端里后面的命令都走代理，执行：

```bash
export http_proxy=http://192.168.1.33:17890
export https_proxy=http://192.168.1.33:17890
```

然后再测一次，这次不用加 `-x`：

```bash
curl https://ifconfig.me
echo
```

结果应和第五步那串公网 IP 一样。

这个设置只在当前终端有效。关掉终端就要重新执行这两行 `export`。

终端里的 `export` 不会传给已经打开的浏览器。浏览器要单独填，而且 HTTP 和 HTTPS 两栏都要填。只填 HTTP 时，浏览器仍会自己去查网站名字，Linux 上没有外网 DNS，就会显示「找不到网站」。这时 Windows 日志里照样会有 open 和 close。

Firefox：

1. 右上角菜单 → 设置 → 拉到最下面「网络设置」→ 设置。
2. 选「手动代理配置」。
3. HTTP 代理填 `192.168.1.33`，端口填 `17890`。
4. 勾选「也将此代理用于 HTTPS」。SOCKS 主机留空。
5. 确定后，地址栏输入 `https://www.baidu.com`。不要把 `192.168.1.33` 填进地址栏。

系统设置里如果有「网络代理」，HTTP 和 HTTPS 都填 `192.168.1.33`，端口都填 `17890`。SOCKS 留空。

## 终端里的 agent

这里说的是 Linux 终端里运行的 `agent`，不是桌面版 Cursor。桌面版的 `settings.json` 不会作用到这个命令。第六步的两行 `export` 也不会作用到已经启动的 agent。

先确认 Windows 上的中转还开着，再在 Linux 上停掉正在跑的 agent。在要启动它的那个终端里执行：

```bash
export http_proxy=http://192.168.1.33:17890
export https_proxy=http://192.168.1.33:17890
export HTTP_PROXY=http://192.168.1.33:17890
export HTTPS_PROXY=http://192.168.1.33:17890
agent
```

这四行必须写在 `agent` 前面。agent 已经在跑时再 export，它看不到这些变量。

启动后另开一个终端，检查这个进程是否真的带了代理：

```bash
tr '\0' '\n' < /proc/$(pgrep -nx agent)/environ | grep -i proxy
```

应能看到 `https_proxy=http://192.168.1.33:17890`。什么都没有，说明 agent 不是从刚才那个终端启动的。回到有这四行 `export` 的终端，先停掉 agent，再按上面的顺序重开。

`curl` 能返回 `HTTP/2 200`，只说明这一条 curl 走了代理。agent 若仍打印 `getaddrinfo EAI_AGAIN api2.cursor.sh`，就是它还在 Linux 本机查这个域名。Linux 没有外网 DNS，本机查询会失败。把 agent 停掉，用带代理的终端重新启动后，再看新输出。屏幕上已经印出的旧报错不会自己消失。

## 用完怎么停

在 Windows 那个中转窗口里按 `Ctrl+C`。Linux 上正在走代理的程序会立刻断开。Windows 自己仍然用七七上网。

Linux 改回原来，只去掉指向 `192.168.1.33:17890` 的代理。网卡和 IP 不用动。

1. 停掉终端里的 agent。
2. 在还开着的终端里执行：

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
```

3. 关掉这个终端。这几行 `export` 只在当时那个窗口里有效，关掉就没了。
4. Firefox：右上角菜单 → 设置 → 拉到最下面「网络设置」→ 设置 → 选「不使用代理」→ 确定。
5. 系统设置里如果把网络代理改成过「手动」，改回「关闭」或「禁用」。

改完后新开一个终端，执行：

```bash
env | grep -i proxy
```

没有任何输出，说明终端已经回到原来的状态。

防火墙那条规则可以留着，它只是允许别人连接 `17890`。中转程序没启动时，这个端口没有程序在听，连进来也会被拒绝。

## 重启之后怎么再开

电脑重启后，第二步不用再做。按这个顺序：

1. 打开七七，等虚拟网卡变成蓝色。
2. 再执行一次第一步的查询。还是 `127.0.0.1` 的 `9674`、`9675`、`9676`，就继续。
3. 执行第三步，留下那个窗口。
4. Linux 上重新执行第六步的两行 `export`。要再开终端里的 agent 时，按上一节「终端里的 agent」的四行 `export` 启动，不要沿用停掉之前的那个进程。

如果第一步里 `9674` 换成了别的端口，启动命令改成下面这样，把 `新端口` 换成查到的那个 HTTP 端口。`9674` 能同时当 HTTP 和 SOCKS 用；如果只剩一个 HTTP 端口，就填那个。

```powershell
& "C:\Users\user\miniconda3\python.exe" c:\Users\user\Desktop\y-proxy\lan_relay.py --target 127.0.0.1:新端口
```
