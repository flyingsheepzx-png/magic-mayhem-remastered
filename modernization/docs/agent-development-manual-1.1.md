# Magic & Mayhem Remastered 1.1：Agent 开发手册

面向接手本版本的编程 agent。整理日期：2026-10-02（香港时间）。本文以该日实际的 `Magic&Mayham_Remastered_1.1` 玩家目录为基线，而不是早期 HD60、v38 或最初冻结的 1.1 构建。先读同目录的 `source-index.json`，它逐项列出开发所需的源码文件及哈希。

## 1. 首次接手：先确认你拥有什么

玩家包的结构如下。`RELEASE_ROOT` 是你收到的整个发行目录，可以移动；不要把作者机器的盘符当成产品要求。

```text
RELEASE_ROOT/
  MagicMayhem-Remastered.exe        玩家入口，也是内嵌模块的载体
  release-manifest.json             发行文件清单及各次修正元数据
  verify-files.ps1                  静态文件校验器
  AGENTS.md                         随包的 agent 工作规则
  Documentation/Agent-Development/
    README.md                       本手册的发布副本
    source-index.json                与当前二进制对应的源码材料索引
  runtime/
    Chaos-Wide169-engine.exe         已修改的原生 x86 引擎
    ddraw.dll                       定制 cnc-ddraw 包装器
    terrain_diagonal.dll            地形通行扩展
    png_assets.dll / png_pages.dll   PNG 兼容层
    jpeg.dll / jpeg_native.dll       JPEG 转发器及保留的原实现
    fmv_h264.dll                     现代过场视频桥接
    CFG/ Interface/ Realms/ ...      游戏资源
    Save/                           玩家存档
    remastered-settings.ini         独立显示参数，运行时可生成
    modernization/config/qol-hotkeys.json
```

**这是原生二进制加 C/C++ 扩展的开发项目，没有完整、可从零编译的原游戏源码。** 修改增强模块需要对应的扩展源码；仅有玩家包可以做资源/配置调查、二进制分析和新扩展，但不能据此宣称已恢复原引擎源码。

作者开发工程称为 `DEV_ROOT`，当前机器位置为 `D:/Games/Magic&Mayham`。其 `modernization/` 包含工具、测试、源码、构建快照和设计文档。玩家目录中的 `runtime/modernization/` 主要是兼容路径与用户状态，不是这个开发工程。其他玩家需要另行取得源码材料；详见第 11 节。

接手步骤：

1. 读用户本次需求、包内 `AGENTS.md`、本手册和源码索引。
2. 确认实际玩家入口、引擎、DLL、PE 内嵌模块哈希。不要仅按 EXE 文件名或“1.1”判断版本。
3. 创建独立开发副本；保存本次来源、哈希、需求和待验证事项。
4. 选择与当前二进制匹配的源码快照，只修改一个明确问题。
5. 构建、离线验证、备份、安装与回滚准备后，按用户授权进行运行验收。

## 2. 这份手册绑定的精确身份

所有值均为 SHA-256；以下核心文件及资源已从实际发行入口读取，并与发行清单核对。

| 对象 | SHA-256 |
| --- | --- |
| 玩家入口 | `bd9015dc7feaeb5d862130a20075e71f5cd09694daa238778db5d429abd4cc3f` |
| 原生引擎 | `42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da` |
| RCDATA 101：repath | `0f618f11afe86cba77b33a64938b07c25da2dad1afc365e414ae63ad43535dd2` |
| RCDATA 102：QoL / HD UI | `ea6325f770b9c1b57a74624973ae6fecdc74a45167e6c857953ada8359daa8b6` |
| RCDATA 103：AI diagnostics | `4e63e0d8452f2bfbcfef52e1838e17575d2bf7cddf37c4a1213dbe6f2ac95c17` |
| runtime/ddraw.dll | `f642c354e106dac903ee0899c3b5a09024c1bad2458f4232c85e37d8c98427cf` |
| runtime/terrain_diagonal.dll | `3a27cafa8a0f282b6bade57e3fee4e8d89511191f2d1b9aea1852399d3ca66d3` |
| runtime/fmv_h264.dll | `9b86df83d71198afe02474fbeae5380f55da99746cc051e6ac169d9263108789` |

当这些值变化时，本文不自动成为新版本的地址或源码依据。先找到新版本的可信来源和差分，更新对应开发记录。

在收到的发行目录中运行：

```powershell
Set-Location -LiteralPath 'D:\path\to\Magic&Mayham_Remastered_1.1'
Get-FileHash -LiteralPath '.\MagicMayhem-Remastered.exe' -Algorithm SHA256
Get-FileHash -LiteralPath '.\runtime\Chaos-Wide169-engine.exe' -Algorithm SHA256
& '.\verify-files.ps1'
```

地址式修改以核心引擎与模块身份为依据；本手册重点说明源码材料和开发流程，不承担整包资源审计。

## 3. 运行时架构与模块边界

玩家入口根据自身路径定位 `runtime/`，校验引擎及相关依赖，创建原生子进程、设置功能环境变量，提取/加载内嵌增强模块。FMV 启动阶段有独立的早期加载处理。请从玩家入口启动，勿用直接启动原生引擎代替正式功能验证。

| 组件 | 工作职责 | 本次匹配的开发来源（相对 DEV_ROOT） |
| --- | --- | --- |
| 正式 launcher | 身份校验、子进程、模块加载、FMV、临时文件清理 | `modernization/build/remastered-1.1-pick-projection/release_launcher.cpp` |
| 101 | 多单位寻路、编队/命令、遮挡与屋顶单位显示、逻辑/运动/渲染重放相关扩展 | `modernization/build/remastered-1.1-movement-timing/` |
| 102 | 混合 UI/字体、小地图、快捷键、头像施法、页面/表面生命周期、AI 限额、参数菜单、点击投影 | `modernization/build/remastered-1.1-pick-projection/` |
| 103 | 可选 AI 诊断，不默认启用 | `modernization/build/remastered-1.1-ai-diagnostics/` |
| ddraw | 表面包装、混合合成、输入逆变换、页面过渡、输出设置与 Present 限额 | `modernization/build/remastered-1.1-options-render-v1/wrapper/` |
| terrain | 地形边检查、对角通行与半阶修正 | `modernization/build/remastered-1.1-half-stair/` |

来源映射依据是对应构建产物与实际安装字节相同，**不是本次重新构建成功的声明**。101 和 102 的最新来源属于不同快照。不要找一个“最近的目录”，就把其中全部旧 DLL 覆盖到运行包。当前 pick-projection 快照中的 repath DLL 是保留的二进制，其 101 源码需从 movement-timing 快照取得。

保留 launcher 的现有早期 FMV 初始化、依赖哈希校验、模块顺序、功能标志和诊断隔离。正式 launcher 会清除部分 `MM_PROBE_*` 输入/采集标志，诊断脚本不能假定它们会传给子进程。

引擎磁盘代码、注入后代码、ddraw 包装器必须分开分析。源码中看不到某行为，可能是另一模块安装的 hook；反过来，磁盘反汇编也看不到所有运行时 detour。

## 4. 必须保留的行为

### 显示与时序

- 独立 UI 页面内容原生 **1920×1440**，默认位于 **2560×1440** 主表面中央，起点 `(320,0)`。
- 战斗场景及 HUD 保持 **1280×720**，在主表面中按既有 **2×** 合成。不要改成原生 2560×1440 战斗，也不要把战斗字体再翻倍。
- 参数菜单支持输出 **1920×1080 / 2560×1440**，窗口 / 无边框，逻辑速度 **40 / 30 / 20** 和包装器 **60 / 120 Present FPS**。这些组合有隔离运行证据。
- 输出缩放与内部几何不同。无边框按所选输出大小移除边框，不必然铺满桌面，也不是独占全屏。
- Render FPS 指成功呈现频率，可能呈现重复内容；它不证明 60/120 张不同游戏画面。原生 30 档采用整数 33ms 调度，可测得约 30.3 次逻辑更新/秒。
- 当前 movement-timing 保留既有 30Hz `31/50` 补偿（诊断 probe 为 `2/3`），其他速率及多人分支遵循已有策略。可见抖动因果和完整游戏时间等价仍未证实，勿顺手改写补偿。

显示参数在 `runtime/remastered-settings.ini` 的 `[display]` 下使用 `resolution`、`window_mode`、`render_fps`；逻辑速度仍走原生偏好保存机制。不要发明 `logic_fps` 键。显示默认回退为 `2560x1440`、`windowed`、`60`；玩家已经保存的选择应保留。

### AI、输入、资源与兼容性

- 单人 NOTIONAL 正常更新 AI budget 为 300（原 30）；两个正常预算读点仅在既有单人条件下覆盖。多人、REAL_TIME、启动分支保留原策略；原生 CFG 不因此全局改成 300。
- 单人 danger refresh 每次最多处理 16 单位 / 最终化 128 地图节点；多人保留 4/32。保留 8 次 owner 轮转耗尽后的 restart marker，防止空重复发布。不要只保留新常量而丢失 installer。
- 保留 `ai_budget.cpp`、`ai_danger_refresh.cpp` 及 102 中的安装链。后续优化一次一项，等用户反馈后继续。
- 保留快捷键绑定/转移/Delete、原生施法状态机、取消/框选行为、头像施法、小地图定位/标记、屋顶 Tab 和下层点击策略。
- 选取问题应先核对原生 hit region、投影、层级和地形。菜单点击准确不能证明单位命中正确；不要全局挪动鼠标来修复个别单位。
- 保留中文文本、存档格式、OGG、现有 FMV 与 PNG 兼容层。多人新行为需独立授权与验证。
- 沿用已批准的 SeedVR2 UI 资源和 Qwen/FullReadable RealmViewer 地图。2026-10-02 Medieval/Greek 更新记录仍标注用户验收待完成，不把美术替换自动当成已接受。

## 5. 构建：从精确快照开始

基本工具是 Windows、MSVC x86 C++/Windows SDK（`cl`、`link`、`rc`）、MSBuild 和 Python。现有快照使用 C++17；引擎与 DLL 是 **32 位 x86**，勿编译成 x64。作者脚本的 Visual Studio 18 和 `C:/Python314/python.exe` 路径是本机位置，换机须参数化。

`modernization/requirements-re.txt` 固定 `pefile==2024.8.26`、`capstone==5.0.9`；有些验证还需要 Pillow、Unicorn 等，按具体脚本 imports 安装到隔离环境。Ghidra/Java 用于进一步静态研究，不是编译 DLL 的前提。Python 工具可为 64 位，但 native harness 必须与 x86 ABI 匹配。

推荐开发布局：

```text
DEV_ROOT/
  modernization/docs/       决策、证据、待办
  modernization/tools/      构建/安装/诊断脚本
  modernization/tests/      回归与 native harness
  modernization/build/<new-iteration>/  新的不可覆盖快照
  modernization/playtests/<new-iteration>/  独立完整玩家包
  modernization/backups/<new-iteration>/   回滚材料
```

不要直接运行旧 `build_remastered_11.py build` 或 `release_remastered_11.py` 来“重新生成最新版”：它们用于历史初始组装，依赖旧目录/包，并有防覆盖门。历史 `current-baseline.json.latest_development` 仍记录 v38/wide169；本次用户指定的正式 1.1 优先，不能因此回退。

构建流程：

1. 将匹配源码、必要头文件/`.inc`、资源定义、图标和构建命令复制到全新的迭代目录；记录输入文件哈希。
2. 从当前入口提取 101/102/103。保持不修改模块的资源字节，关闭 `pefile.PE` 映射，避免 Windows 文件锁。
3. 只构建本次目标组件；审查现有 `build.cmd`/`terrain.cmd`，因为其中可能还会编译 launcher、运行测试或引用旧资源。
4. 编译入口时保留全部资源，包括 103，更新确实变化的依赖 pin；不要通过删除校验来绕过未知版本。
5. 验证 PE 架构、导入、资源集合、未修改模块字节和所有 hook 签名，再进入安装步骤。

示例：在新的 wrapper 源码副本中，保留项目设置，用已配置的 MSBuild 执行：

```powershell
& $msbuildPath '.\cnc-ddraw.vcxproj' /p:Configuration=Release /p:Platform=Win32 /m
```

`$msbuildPath` 必须先指向本机可信安装。源码位置与命令清单见 `source-index.json`。编译器升级可能改变输出字节；需要重新验证功能与 pin，不能要求新构建偶然复现旧哈希，也不能把旧哈希不符当成理由跳过验证。

## 6. 增加 hook 或二进制补丁

补丁至少绑定：可信完整引擎 SHA-256、PE machine/image base、准确 VA/RVA、预期原始字节、完整指令边界和回滚原字节。当前引擎常用首选 image base 为 `0x400000`；在每个具体输入中核实。不要把 VA、RVA、文件偏移混用。

未知哈希必须拒绝地址式安装；不要将刚算出的任意哈希直接加入白名单。新引擎版本需重新推导地址/ABI、检查冲突，同时评估 launcher、PNG loader、wrapper 等各自的身份 gate。

核对 `cdecl/stdcall/thiscall/fastcall`、ECX/EDX、堆栈清理、flags、保存寄存器和异常路径。trampoline 必须处理被覆盖指令中的相对地址。多个模块改同一入口时记录安装顺序和当前预期签名，避免重复 detour 或恢复别人的 hook。

native 对象的分配/释放、表面注册/销毁和 owner/生命周期要遵循已有实现。不要把 Ghidra 伪 C 当成可编译且 ABI 正确的源代码；为新结论记录输入身份、地址、反汇编/反编译证据、置信度和验证范围。分析数据库按版本隔离、放在源码仓库外。

## 7. 修改资源与中文配置

外部图像的活跃派生资源采用 PNG。原引擎仍可能请求 `.BMP`；兼容 DLL 会找同名 PNG，不要全局改配置名或删除 loader。`jpeg.dll` 转发给 `jpeg_native.dll`，并带入 PNG 兼容层；它不是随意可删的旧依赖。

PNG 无损不意味着任意 RGBA 都被引擎正确解释。现有 general loader 走 native BGR DIB；应保持精确颜色键、pitch、底向上布局、像素尺寸和裁切矩形。UI 的蓝/洋红颜色键和 sprite 的原生编码不能用 JPEG 或任意透明度替代。

修改资源需一起审查 atlas/Rect/Rect2、按钮状态族、文字窗口、点击矩形、缩放和混合页面切换；不要只换一张预览图。SPR 等原生资源与 PNG 是不同格式，先读对应工具，不能通过改扩展名转换。

中文配置可能是 GBK 或保留原生字节。做有限字段的字节替换，避免整份解码再编码。参数菜单的 `Game speed` / `Render FPS` 英文标签是已有受控修正，勿为“统一中文”顺手撤销。

生成素材复用已批准结果和原始来源；作者工作流使用 LocalModelManager，UI 使用 SeedVR2 7B Sharp，地图/其他约定素材使用 Qwen Image 2.1，禁止换用 GPT 图片生成。其他玩家没有这个本地服务时，先使用现成资产，不假设作者路径、模型或凭证存在。

FMV 通过现有 H.264 桥接和早期 launcher hook 播放 2560×1440 MP4。修改播放器时保留已有失败处理，并核对所用版本的回退逻辑。保留源 PTS、音轨、中文字幕、片段顺序和 campaign 触发语义。

## 8. 验证与游戏诊断

本手册整理过程中没有启动游戏。已有运行证据按具体修正、存档和构建解释，不扩展成整个 1.1 已全面验收。

先做与改动相关的离线测试：x86 detour 寄存器/flags/堆栈、native harness、边界/生命周期、像素颜色键、路径合法性和未修改模块字节。可参考工程内 `surface_registry_test.cpp`、`surface_lifecycle_native_test.cpp`、`options_*_test.py`、`movement_timing_test.cpp`、`ai_budget300_test.py` 和 `ai_danger_refresh_test.py`。这些脚本可能固定旧 build 路径；在新迭代中明确重定向目标后使用。

默认流程在构建安装并核对哈希后交给用户测试。只有用户明确要求 agent 运行验收时才启动隔离游戏。历史四项参数菜单任务曾单独要求逐项运行验收，不能把这个特例当成所有未来任务的常驻授权。

获准运行测试时：

- 使用独立完整包，独立 Save、CFG、AI 文件和显示/快捷键设置；可变文件不要 hardlink 回玩家目录。
- 从 launcher 启动，原生子进程 working directory 为 `runtime/`。仅操作、结束自己拥有的进程，不按名字批量终止用户进程。
- 优先 Python 后台输入与只读内存采样；确认 wrapper 私有输入协议的版本与 ACK。普通 `game_window.py` 会前台操作，不作为默认后台方案。
- 绑定 hash-verified 引擎和加载模块身份。读内存诊断不写玩家内存，不用未知地址值冒充遥测证据。
- 按 Windows client area 推导输入；分别处理窗口输出坐标、2560 主表面坐标、UI 起点和 1280 战斗坐标。确认实际选中单位后再测移动。
- 同一存档哈希、同一页面、相同行为做前后截图，保存完整输出尺寸。优先自动像素检查，只在具体疑点无法自动解决时人工看图。
- 分开统计逻辑更新、上传/重放、成功 Present、不同像素帧和世界位置随时间；一个 FPS 数字不能代表所有层次。
- 在 `finally` 清理自有进程、还原临时配置，核对玩家文件未变。

## 9. 安装、回滚与发行

制作新迭代，勿覆盖本次基线。安装前确认游戏已关闭，并确定实际目标根目录：历史工具可能同时写正式包、冻结 package 和 p1 候选三个位置，其他玩家不能直接运行这些硬编码 installer。

回滚表至少记录每个目标的相对路径、备份位置、before/after SHA-256、对应 manifest 变化与组件范围。安装前备份并验证备份哈希；写临时文件后原子替换，失败即恢复这次已经替换的项，并复核。

保护清单：`Save/`、`CFG/prefs.cfg`、`ddraw.ini`、`remastered-settings.ini`、快捷键 JSON、AI 学习文件、运行时生成/加密配置与玩家新增文件。`mutable_files` 是已知列表，不是所有用户状态的完整枚举。不要从旧发行清单重建玩家状态。

回滚前要求目标仍符合此次 after 哈希，避免覆盖后来的修正；通常按逆序撤销。仅恢复这次代码/资源和相关元数据，勿回滚新存档。早期危险度回滚和 budget 回滚存在先后依赖，不能随意跳回旧版。

新发行清单要从经过审查的静态文件计划生成，保留 source→build→install 来源链；排除玩家存档、诊断日志、转储、临时文件及凭证。不要按扩展名把所有 `.MAP` 当 linker 输出删掉：Realms 中的原生地图曾因此丢失 683 份。

对移到新路径（含中文/空格）的完整包做身份/路径检查；获准后验证启动、页面→战斗转换、输入映射、视频和退出。没有新目录运行证据时只报告静态可移植性，不报告运行通过。

## 10. 已知问题与证据边界

| 项目 | 本基线的记录状态 / 接手注意 |
| --- | --- |
| 间歇读档 AV / OGG 退出等待 | 未彻底解决；与已经修复的表面注册死循环分开诊断 |
| Alt+F4 表面生命周期 | 已有修正与 native harness；早期 known-issues 的笼统描述已过时，完整退出仍要按实测判断 |
| 参数菜单 | 四项已有隔离运行证据；输出分辨率切换已实现，原生 1K/2K/4K 内容方案不是同一功能 |
| 60 个不同画面 / 游戏时间完全等价 | 未完成证明；Present 60/120 不能关闭此项 |
| 最新移动时序 / 点击投影 | 已安装且有离线测试，清单仍标注用户运行验收待完成 |
| Medieval/Greek FullReadable 更新 | 2026-10-02 替换记录标注用户验收待完成 |
| Campaign FMV 触发 | 部分播放器/开场播放有证据，不等于所有战役触发验证 |
| 多人 | 兼容/同步门仍未完成，新优化默认保留原分支 |

`release-manifest.json` 的修正字段保存各次历史测试哈希，不都代表当前模块。例如 options 的早期 module hash 与现在 102 不同是后续叠加的正常情况。以顶层当前身份、实际内嵌资源和来源链判断继承；测试报告不能替代它们。

## 11. 发布给其他玩家时应提供的开发材料

本次随包提供的是手册和源码索引，**没有把整个开发工程打包进去**。让其他玩家能够继续修改已有功能，应另发一个开发资料包，至少包含：

1. `source-index.json` 指定的精确源码快照、其 `.h/.inc`、资源定义、图标和 build 命令；保留 wrapper 的完整 src/inc/config/项目/许可。
2. 对应的构建/验证/安装工具及传递导入依赖，相关测试和受控 fixture。不要只发 `runtime/hd11/`，因为部分最终源码由构建脚本生成/改写。
3. 设计文档及证据摘要：`native-ui-1920.md`、`ui-layout-adapter.md`、`qol-input.md`、`options-modernization.md`、`roof-visibility.md`、`unit-occlusion.md`、`png-assets.md`、`fmv-compat.md`、`launcher-architecture.md`、`ai-strategy-review.md`、`static-analysis.md`。
4. 原生引擎作为受控二进制依赖的身份记录，以及所需资产/fixture 的获取方式；不要声称扩展代码许可证自动授予原游戏、美术、音乐和视频再分发权。

### 需要交付的具体源码目录

所有路径相对 `DEV_ROOT`。复制目录中的源码材料即可，避免连同 `.obj/.pdb/.exp/.lib` 和历史临时输出一起打包。同名文件按模块目录分开放置，不要混成一套平铺源码。

| 用途 | 必需源码与材料 |
| --- | --- |
| launcher / 102 | `build/remastered-1.1-pick-projection/` 下全部 `.cpp/.h/.inc/.rc/.ico/.cmd`，以及 native 生命周期测试 fixture `native_destroy.bin`；目录前缀为 `modernization/` |
| 101 | `modernization/build/remastered-1.1-movement-timing/` 下五个主编译单元 `repath_multiunit_trial.cpp`、`render_replay_trial.cpp`、`clock_trial.cpp`、`logic_time_trial.cpp`、`game_time_trial.cpp`；全部配套 `.h/.inc` 与 `build.cmd` |
| 103 | `modernization/build/remastered-1.1-ai-diagnostics/ai_diagnostics.cpp` 与 `build.cmd`；集成时用当前 launcher/rc，勿换回该历史目录的入口 |
| wrapper | `modernization/build/remastered-1.1-options-render-v1/wrapper/` 的 `src/`、`inc/`、`config/`、项目文件、`exports.def`、`res.rc`、Makefile、README 与 LICENSE；排除 bin/obj/.vs |
| terrain | `modernization/build/remastered-1.1-half-stair/terrain_diagonal.cpp`、`terrain.cmd` |
| FMV | `modernization/build/remastered-1.1-fmv-h264/fmv_h264.cpp`；构建说明与验证入口位于 `modernization/assets/fmv-delivery-1440p-20261001/` 的构建命令、`fmv_h264_validation.cpp`、`REPORT.md`、`HANDOFF.md` |
| general PNG | `modernization/build/remastered-1.1-loader-fix/png_assets.cpp`、`build.cmd`、`build-policy.cmd`、`verify_policy.cpp`；它包含当前合并引擎的允许身份 |
| PNG 页 / JPEG 转发 | `modernization/runtime/png-pages/` 与 `modernization/runtime/png-assets/` 中源码、`.def` 和离线测试；当前实际 loader 的身份需以运行 DLL pin 为准 |
| 后续维护源码 | `modernization/runtime/hd11/` 全部源码/适配脚本以及 `modernization/runtime/terrain_diagonal/`；保留它们，但不把未同步的维护源替代上述最终快照 |
| 工具和测试 | `modernization/tools/` 中 Python/PowerShell/构建工具、`modernization/tests/` 中源码与小型必要 fixture、`requirements-re.txt`；包括传递依赖，之后再按用途裁剪 |
| 资源重建 | 与修改目标对应的 `modernization/assets/` 生成脚本、输入来源记录、几何/颜色键/状态族计划和模型任务参数；无需提供模型权重或全部中间图 |

101 必须带齐 `movement_timing.h`、`command_index.h`、`layout_context.h`、`ui_layout.h`、各 route `.inc`、`dynamic_wait.inc`、`command_response.inc` 和 `roof_ghost.inc`。102 必须带齐生命周期、混合 UI、参数菜单、AI、portrait/roof/canopy 的编译单元与 include；只交付 `qol_bindings.cpp` 不足以构建。

机器可读索引提供上述核心源码的实际文件名、大小、SHA-256 和产物匹配状态。外部 PNG 页/JPEG、FMV 的记录注明来源范围，不能把“找到了源码文件”当成已验证该工具链能从零重建全部运行包。

开发包应去掉作者玩家存档、私有地址/账号、日志转储、机器私有配置、模型权重和大体积历史缓存；保留第三方许可证，明确各组件授权来源。将作者绝对路径参数化，并检查 Python imports、C++ include 和 rc 引用闭包。现有 source-index 是来源/哈希索引，不是完整依赖锁或源码发行包通过证明。

作者本机全局 skills 可以提高工作效率，但其他 agent 不一定拥有它们。上述验证/后台输入/静态分析步骤应以工程中的实际代码与证据为准，不能要求读者访问 `C:/Users/DEVELOPER/.codex/skills` 或作者 NAS 才能理解手册。

## 12. 建议给接手 agent 的起始指令

```text
请基于我提供的 Magic & Mayhem Remastered 1.1 完整目录处理：<具体需求>。
先读根目录 AGENTS.md 和 Documentation/Agent-Development/README.md，
核对 source-index.json、release-manifest.json、核心文件和内嵌资源哈希。
保留当前所有功能和我的存档/配置，在独立副本中只实现这一个问题。
先报告所用源码快照、影响模块和验证范围，再完成构建、哈希核对、
备份、安装与可执行回滚。未知版本不要套固定地址。
默认由我进行游戏验收；若我另行授权你运行测试，使用隔离后台方案。
把确定的设计、证据和待办写入工程文档，明确哪些仍待运行验证。
```

交付说明应包含：问题和结果、基线/源码/产物身份、改动组件、测试证据及限制、安装位置、回滚方法和待用户验证项。每个自然检查点更新权威文档；勿把聊天记录当成唯一跨会话记忆。
