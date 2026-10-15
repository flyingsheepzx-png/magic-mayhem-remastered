# Magic & Mayhem Remastered — 社区开发源码

这是 Remastered **1.1 正式版扩展层**的源码仓库，供修复问题、研究和共同开发。此前玩家包只有二进制和开发手册，没有作者的 `DEV_ROOT/modernization/`，按手册找不到源码的问题由本仓库补齐。

**克隆本仓库后的目录就是 `DEV_ROOT`**，里面实际提供 `modernization/`。无需作者的盘符、NAS、Codex 全局 Skills 或本地模型服务。

这里没有完整的原游戏引擎源码，也不提供原游戏或素材。项目在既有 32 位引擎上通过 launcher、DLL 与 DirectDraw wrapper 扩展功能。游戏文件请自行准备合法取得、符合下面哈希的 Remastered 1.1 玩家包。

## 从哪里开始

1. 克隆或通过 GitHub 的 **Code → Download ZIP** 取得本仓库。
2. 阅读 [快速构建](docs/BUILDING.md) 和 [源码地图](docs/SOURCE_MAP.md)。
3. 接手 agent 先读 [AGENTS.md](AGENTS.md)，再读 [正式版开发手册](modernization/docs/agent-development-manual-1.1.md)。
4. 先核对版本，只修改一个具体问题，在独立副本中验证，通过 Issue / Pull Request 共创。

```powershell
# 需要 Git、Windows、Python 3.10+；也可下载 ZIP 后进入解压目录。
git clone https://github.com/flyingsheepzx-png/magic-mayhem-remastered.git
Set-Location magic-mayhem-remastered

# 在仓库根目录执行。
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe dev.py audit

# 指向你自己的完整玩家目录；只读取，不改写该目录。
.\.venv\Scripts\python.exe dev.py prepare --release-root 'D:\YourGames\MagicMayhem_Remastered_1.1'

# 安装 MSVC C++ x86 构建工具和 Windows SDK 后：
.\.venv\Scripts\python.exe dev.py build
.\.venv\Scripts\python.exe dev.py test
```

所有输出位于被 Git 忽略的 `out/`。构建入口自动发现 Visual Studio，不依赖作者的 VS 安装路径。只构建某个模块可用 `dev.py build --component 102`；具体步骤和边界见构建文档。

## 提供了什么

| 内容 | 位置 |
| --- | --- |
| 对应正式 1.1 的 launcher、101/102/103、wrapper、地形、FMV、PNG loader 源码 | `modernization/build/` 中的精确快照 |
| 逐文件大小、SHA-256、产物来源映射 | `modernization/docs/source-index.json` |
| 维护代码、历史构建与诊断工具、离线测试 | `modernization/runtime/`、`tools/`、`tests/` |
| 寻路、UI、时序、AI、静态研究的现有结论 | `modernization/docs/` |
| 已审查的公开文件和排除项 | `source-distribution.json` |

正式玩家入口 SHA-256 为 `bd9015dc7feaeb5d862130a20075e71f5cd09694daa238778db5d429abd4cc3f`，原生引擎为 `42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`。`dev.py prepare` 会验证核心文件和内嵌模块，未知版本直接拒绝。

这是已结束的作者 1.1 项目的源码公开；社区可以在此基础上继续贡献。仓库不承诺作者继续开发或合并所有提案。历史文档中的 v38、旧“最新版本”、绝对路径与任务状态属于当时记录；正式 1.1 的精确来源映射及本仓库入口优先。

本次离线构建结果与限制见 [验证记录](docs/VALIDATION.md)。间歇性读档 AV、OGG 退出挂起和多人行为仍有历史限制，不能因源码公开而视为解决。编译成功也不等于游戏验收。

## 参与与许可

欢迎提交可复现的 Issue、补充研究证据和范围明确的 PR，先读 [贡献说明](CONTRIBUTING.md)。报告中请附版本哈希、复现步骤、预期/实际结果；不要上传个人存档、转储或整套游戏资源。

新增原创代码与文档采用 [MIT](LICENSE)。第三方组件保留各自许可证，见 [第三方声明](THIRD_PARTY_NOTICES.md)。原游戏及其素材不受本仓库 MIT 授权。
