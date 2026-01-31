# dvrctl - DaVinci Resolve Control Package

[![PyPI](https://img.shields.io/pypi/v/dvrctl.svg)](https://pypi.org/project/dvrctl/)
[![Python](https://img.shields.io/pypi/pyversions/dvrctl.svg)](https://pypi.org/project/dvrctl/)
[![Downloads](https://img.shields.io/pypi/dm/dvrctl.svg)](https://pypi.org/project/dvrctl/)
[![GitHub stars](https://img.shields.io/github/stars/LoveinYuu/dvrctl.svg?style=social)](https://github.com/LoveinYuu/dvrctl)
[![License: All Rights Reserved](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg)](LICENSE)

> 一个用于控制和自动化 DaVinci Resolve 的 Python 库。

---

## 快速开始

```bash
pip install dvrctl
```

```python
import dvrctl

# 连接到本地运行的 DaVinci Resolve
dvr = dvrctl.GetResolve()

# 示例：切换到导出页面并退出
dvr.OpenPage('Deliver')  # 官方 API 方法
dvr.Quit()               # 官方 API 方法
```

---

## 初始化参数

`GetResolve` 类支持以下初始化参数：

```python
dvr = dvrctl.GetResolve(
    fuscript_path=None,  # 可选：指定 fusionscript 文件路径
    host=None,           # 可选：连接到远程主机
    loglevel='INFO'      # 可选：日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
)
```

### 参数说明

| 参数              | 类型  | 默认值    | 说明                                               |
|-----------------|-----|--------|----------------------------------------------------|
| `fuscript_path` | str | `None` | 手动指定 fusionscript 库路径，通常不需要设置                    |
| `host`          | str | `None` | 连接到远程 DaVinci Resolve 实例，例如 `'192.168.1.100'`    |
| `loglevel`      | str | `INFO` | 日志输出级别，可选值：`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

### 使用示例

```python
# 启用调试日志
dvr = dvrctl.GetResolve(loglevel='DEBUG')

# 连接到远程主机
dvr = dvrctl.GetResolve(host='192.168.1.100')

# 手动指定 fusionscript 路径
dvr = dvrctl.GetResolve(
    fuscript_path='/path/to/fusionscript.so',
    loglevel='WARNING'
)
```

---

## 功能概览

获取项目管理、项目操作、媒体存储、媒体池、时间线、通用工具、渲染输出等功能模块。

| 模块                  | 示例方法            | 说明       |
|---------------------|-----------------|----------|
| **Project Manager** | `dvr.pjm()`     | 获取项目管理器  |
| **Project**         | `dvr.pj()`      | 获取项目     |
| **Media Storage**   | `dvr.mds()`     | 获取媒体存储   |
| **Media Pool**      | `dvr.mdp()`     | 获取媒体池    |
| **Timeline**        | `dvr.tl()`      | 获取时间线    |
| **General**         | `dvr.general()` | 使用通用工具   |
| **Deliver**         | `dvr.deliver()` | 使用渲染输出功能 |

### 其他方法示例

| 模块                  | 示例方法                                       | 说明           |
|---------------------|--------------------------------------------|--------------|
| **Project Manager** | `pjm.CreateProject("MyProj")`              | 创建新项目        |
| **Project**         | `pj.save_project()`                        | 保存当前项目（自建方法） |
| **Media Storage**   | `mds.GetMountedVolumeList()`               | 获取挂载卷        |
| **Media Pool**      | `mdp.GetRootFolder()`                      | 获取根文件夹       |
| **Timeline**        | `tl.lock_track('video', 1, True)`          | 锁定轨道（自建方法）   |
| **General**         | `general.frames2tc(86400)`                 | 帧数转时间码（自建方法） |
| **Deliver**         | `deliver.add_to_render("Preset1", "/out")` | 添加渲染任务（自建方法） |

---

## 安装要求

* Python **3.5+**
* DaVinci Resolve **19+**（建议 19.1 及以上，需 Studio 版本）
* （可选）设置 DaVinci Resolve 的脚本环境变量

> **注意**：从 0.2.0 版本开始，`dvrctl` 支持**自动检测** fusionscript 路径，大多数情况下无需手动配置环境变量。

<details>
<summary>环境变量配置（可选，点击展开）</summary>

如果自动检测失败，可以手动设置以下环境变量：

**macOS**

```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

**Windows**

```powershell
setx RESOLVE_SCRIPT_API "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
setx RESOLVE_SCRIPT_LIB "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
setx PYTHONPATH "%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\"
```

**Linux**

```bash
export RESOLVE_SCRIPT_API="/opt/resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/opt/resolve/libs/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
# 部分发行版路径可能需要改为 /home/resolve
```

</details>

---

## 使用示例

### 基础操作

```python
import dvrctl

# 连接到 DaVinci Resolve（启用调试日志）
dvr = dvrctl.GetResolve(loglevel='DEBUG')

# 获取当前项目信息
pj = dvr.pj()
print(f"当前项目: {pj.GetName()}")

# 保存项目
pj.save_project()
```

### 项目管理

```python
pjm = dvr.pjm()
pjm.CreateProject("MyNewProject")  # 官方 API 方法
```

### 时间线操作

```python
tl = dvr.tl()
print(f"时间线名称: {tl.GetName()}")  # 官方 API 方法

# 锁定视频轨道 1
tl.lock_track('video', 1, True)  # 自建方法

# 锁定所有音频轨道
tl.lock_all_tracks('audio', True)    # 自建方法

# 删除视频轨道 1-5，最后参数可省略
tl.delete_track('video', 1, 5)  # 自建方法

# 删除所有视频轨道
tl.delete_tracks('video')  # 自建方法
```

### 添加媒体到时间线

```python
# 获取媒体池项目
mdp = dvr.mdp()
media_item = mdp.GetRootFolder().GetClips()[0]

# 添加到时间线
tl = dvr.tl()
tl.append_to_timeline(
    media_item,
    media_type=1,              # 可选：媒体类型
    track_index=1,             # 可选：轨道索引
    start_tc='00:01:00:00',    # 可选：起始时间码
    end_tc='00:02:00:00',      # 可选：结束时间码
    record_tc='01:00:00:00'    # 可选：记录时间码
)  # 自建方法
```

### 渲染输出

```python
# 添加渲染任务
dvr.deliver().add_to_render("Preset1", "/path/to/output")  # 自建方法
```

### 远程控制

```python
# 连接到远程 DaVinci Resolve
dvr = dvrctl.GetResolve(host='192.168.1.100')

# 执行操作
dvr.OpenPage('Edit')
```

---

## 功能特性

* ✅ **自动连接**：一行代码连接 Resolve，无需复杂配置
* ✅ **自动检测**：跨平台自动检测 fusionscript 路径（macOS/Windows/Linux）
* ✅ **日志控制**：灵活的日志级别控制，便于调试
* ✅ **面向对象接口**：简化 DaVinci Resolve API 调用
* ✅ **时间码工具**：帧数与时间码互转
* ✅ **轨道控制**：锁定/删除轨道更方便
* ✅ **媒体操作**：快速向时间线添加媒体
* ✅ **渲染管理**：简化渲染预设和任务添加
* ✅ **远程控制**：支持连接远程 DaVinci Resolve 实例

---

## 故障排除

### 连接失败

如果出现连接错误，请检查：

1. **DaVinci Resolve 是否正在运行**
2. **是否使用 Studio 版本**（免费版不支持脚本功能）
3. **启用调试日志查看详细信息**：

```python
dvr = dvrctl.GetResolve(loglevel='DEBUG')
```

### 自动检测失败

如果自动检测 fusionscript 失败，可以：

1. **手动指定路径**：

```python
dvr = dvrctl.GetResolve(
    fuscript_path='/path/to/fusionscript.so'  # 或 .dll
)
```

2. **设置环境变量** `RESOLVE_SCRIPT_LIB`（见上方配置说明）

---

## 注意事项

* 使用此库前需确保 **DaVinci Resolve 正在运行**
* 需要 **Studio 版本** 才能使用脚本功能
* 部分功能依赖特定 DaVinci Resolve 版本
* 远程连接功能需要在 DaVinci Resolve 中启用网络设置

---

## 更新日志

### 0.2.0
* 🚀 **新增自动检测 fusionscript 功能**（支持 macOS/Windows/Linux）
* 🚀 **新增日志级别控制**（DEBUG/INFO/WARNING/ERROR/CRITICAL）
* 🚀 **改进错误处理和异常信息**
* 🚀 **优化初始化流程**
* 📝 更新文档和使用示例

### 0.1.0

* ✨ 重构项目结构
* ✨ 新增说明文档
* ✨ 简化代码

### 0.0.1

* 🎉 从个人项目发布为开源软件

---

## 版权说明

因还是测试阶段，请勿在不了解的情况下使用。

版权所有 © 2025 LoveinYuu
保留所有权利（All Rights Reserved）

未经版权人明确书面许可，禁止复制、修改、分发、再授权或其他任何使用行为。

如需使用或获取许可，请联系：  
**Email:** purewhite820@gmail.com

---

## 致谢

感谢 Blackmagic Design 提供强大的 DaVinci Resolve 脚本 API。
