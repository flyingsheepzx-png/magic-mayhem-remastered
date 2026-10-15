# 源码地图与历史材料

`DEV_ROOT` 就是本仓库根目录。玩家包和开发仓库是两个不同的目录；不需要在玩家包中寻找完整 `modernization/`。

| 当前正式组件 | 对应源码目录 | 构建目标 |
| --- | --- | --- |
| 最终 launcher 与 102（QoL、HD UI、参数菜单、AI 限额、选取投影） | `modernization/build/remastered-1.1-pick-projection/` | `102`、`launcher` |
| 101（寻路、命令、运动时序与渲染重放） | `modernization/build/remastered-1.1-movement-timing/` | `101` |
| 103（可选 AI 诊断） | `modernization/build/remastered-1.1-ai-diagnostics/` | `103` |
| 定制 cnc-ddraw | `modernization/build/remastered-1.1-options-render-v1/wrapper/` | `wrapper` |
| 地形对角与半阶 | `modernization/build/remastered-1.1-half-stair/` | `terrain` |
| H.264 FMV 桥接 | `modernization/build/remastered-1.1-fmv-h264/` | `fmv` |
| 通用 PNG loader | `modernization/build/remastered-1.1-loader-fix/` | `png` |
| PNG pages / JPEG 转发器参考代码 | `modernization/runtime/png-pages/`、`modernization/runtime/png-assets/` | 参考源码；不宣称与安装字节已建立对应 |

`dev.py build` 从上表各自的精确快照编译。不能将某个最近目录里的全部模块视为最终版本。`runtime/hd11/` 是维护源与适配器；正式快照优先。历史 `build.cmd` 作为原始证据保留，可能含作者的 VS 路径或过期输入；推荐使用新的 `dev.py`。

`source-index.json` 是 2026-10-02 的来源记录，保持原始字节。其中 `source_code_included: false` 描述当时的**玩家包**，不是当前 GitHub 仓库。其 `matching_artifact.path` 指向作者当时的产物，不表示仓库会附上那些 EXE/DLL。本仓库实际公开文件以根目录 `source-distribution.json` 为准。

原索引中的 6 个二进制/素材文件未发布：四份 launcher 图标、一份 native Destroy 测试片段、一份诊断 fixture trace。图标与 Destroy 片段由 `dev.py prepare` 从哈希验证后的玩家文件提取；fixture trace 不是核心构建或三项原生离线测试的依赖。wrapper 自带图标属于其上游组件，保留上游声明。

历史工具、测试与素材生成脚本用于提供已有实现和研究线索，未逐个迁移到新目录。某些工具依赖已清理的历史包、特定存档、旧产物或本地模型服务，运行前须阅读源码并重定向目标。维护范围、未解决问题与贡献要求见根目录文档。无需重新反编译才能读取已有扩展实现；进一步研究引擎仍需自行准备对应游戏输入。
