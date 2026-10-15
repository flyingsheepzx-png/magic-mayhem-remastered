# Windows 构建

## 环境

- Windows 10/11，Python 3.10+。
- Visual Studio 或 Build Tools，安装“使用 C++ 的桌面开发”、MSVC x86/x64 工具和 Windows SDK。DLL 和 harness 使用 **x86**；Python 可以为 x64。
- `python -m pip install -r requirements-dev.txt`，建议使用根目录 README 的虚拟环境。进一步执行历史分析脚本时，按其 imports 安装 Pillow、numpy、Unicorn 等可选库。
- 完整 Remastered 1.1 玩家文件只在准备测试输入和 launcher 资源时需要。原游戏、素材、视频、模型权重不由此仓库提供。

从仓库根目录运行命令。以下 `python` 可以替换为 `.\.venv\Scripts\python.exe`。

```powershell
python dev.py audit
python dev.py prepare --release-root 'D:\YourGames\MagicMayhem_Remastered_1.1'
python dev.py build
python dev.py test
```

`audit` 校验公开清单和正式快照的 quoted include 依赖。修改源码后清单哈希变化是预期行为；审查差异，不要为了通过检查删除身份验证。发布新源码版本时重新生成清单，并说明基线变化。

`prepare` 只读玩家入口、引擎与相关核心 DLL，验证已知 SHA-256 和内嵌 101/102/103，然后将这三个模块、launcher 图标和重定位后的 native 生命周期测试片段提取到 `out/inputs/`。未知版本不执行地址式提取。不会复制存档、设置或记录玩家绝对路径。

`build` 自动通过 `vswhere` 定位 MSVC，再初始化 x86 环境。非标准安装可设置环境变量 `MM_VCVARSALL` 指向可信 `vcvarsall.bat`。编译中间文件、wrapper 工程副本和输出都在 `out/`，正式源码快照保持原样。

## 目标与依赖

```powershell
python dev.py build --component 101
python dev.py build --component 102
python dev.py build --component 103
python dev.py build --component terrain
python dev.py build --component fmv
python dev.py build --component png
python dev.py build --component wrapper
python dev.py build --component launcher
```

默认 `all` 依次构建上述七个 DLL 和 launcher。只编译 DLL 不需要玩家文件；launcher 需要先 `prepare`。launcher 优先内嵌 `out/101`、`out/102`、`out/103` 中已构建的模块，缺少时保留已验证玩家入口中的原模块。请确认这些目录中的产物确实是本次需要的版本。

新 launcher 保留引擎与外部依赖身份 gate。对于本次 `out/terrain`、`out/fmv`、`out/png` 中存在的产物，会在 `out/launcher/release_launcher.cpp` 中更新对应 SHA pin；没有重建的外部组件仍保持原 pin。`jpeg.dll`、`jpeg_native.dll`、`png_pages.dll` 继续使用原玩家包，参考代码不自动替换它们。`out/build-report.json` 记录生成物的 x86 身份与哈希，不要求不同工具链逐字节复现原产物。

`test` 编译并运行三个离线原生 harness：表面注册表、运动时序、精确 native Destroy + 生命周期 hooks。最后一项需要 `prepare` 提取的片段。测试只在新进程里使用 mock COM 表面和固定测试映射，不启动游戏，不操作玩家进程。

## 把改动用于隔离测试

本仓库没有自动安装命令。为具体修正准备独立完整玩家副本，并独立保存可变文件。只替换本次改动的模块及匹配 launcher；如果 launcher 更新了外部依赖 pin，必须同步该依赖。保留原文件、SHA-256 和可执行回滚步骤，核对 PE x86、所有嵌入资源和 hook 签名后再运行。

不要直接覆盖唯一玩家目录。完整打包涉及原游戏资产、配置和历史安装链，`dev.py build` 不从零重建整套游戏。所有新构建的运行验收仍待用户测试；历史 AV/OGG 限制并未因编译而解决。
