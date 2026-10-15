# 第三方与授权范围

本仓库新增扩展代码、工具与原创文档按根目录 MIT LICENSE 发布。原游戏引擎、玩家文件、图像、字体、音乐、视频、存档与模型权重不在这项授权内，也不随本仓库提供。开发者自行准备合法取得、与文档哈希相符的玩家文件。

| 组件 | 来源与许可证 | 仓库内声明 |
| --- | --- | --- |
| 定制 cnc-ddraw | [FunkyFr3sh/cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw)，MIT；本仓库是游戏专用修改快照 | `modernization/build/remastered-1.1-options-render-v1/wrapper/LICENSE` |
| Microsoft Detours | [microsoft/Detours](https://github.com/microsoft/Detours)，MIT | 上述 wrapper 下 `src/detours/LICENSE.md` |
| LodePNG | Lode Vandevenne，zlib 风格许可证 | 上述 wrapper 下 `inc/lodepng.h` 和 `src/lodepng.c` 文件头 |
| Khronos OpenGL/KHR 头文件 | Khronos Group，保留文件内许可证 | 上述 wrapper 下 `inc/glcorearb.h`、`inc/wglext.h`、`inc/KHR/khrplatform.h` |
| Windows/DirectX 接口兼容声明 | 保留原文件头的来源与声明；不以根目录 MIT 替换 | wrapper 的 `inc/` 与相关接口源码 |

保留所有上游版权与许可证文本。修改过的 wrapper 不代表上游原版。Python 库由使用者通过包管理器安装，遵守各自许可证；本仓库不捆绑这些库。`modernization/recovered-source/` 是清理时按内容哈希保存的扩展工具源码，不是原游戏完整源码。

原游戏的少量 native 测试字节和 launcher 图标由 `dev.py prepare` 从本地经哈希验证的玩家文件提取，保存在被忽略的 `out/`，不会上传。静态研究文档记录地址、接口、推导与局部分析，不构成原游戏源码授权。
