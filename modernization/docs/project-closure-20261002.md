# 项目结束与清理报告 — 2026-10-02

用户决定以实际安装的 Remastered 1.1 作为最终版本并结束开发。1.2 已取消，相关安装包、源码、构建、测试副本、专用 Ghidra 数据库和可确认的模型输出已删除。

## 清理结果

- 总计回收约 228.65 GiB（根据清理前清单与最终文件大小计算，非卷可用空间差值）。
- 开发工程：约 1.07 GiB；正式 1.1：约 1.25 GiB。
- 正式 1.1 全部 4,957 个文件 SHA-256 与清理前一致，含存档和配置。
- 219 份正式源码材料、55 份不同内容存档、34 份从旧备份回收的独有源码均通过哈希验证。
- 已清除旧整包测试副本、历史备份、重复发行包、截图/转储/帧缓存、模型任务输出与重复工具安装归档。
- 保留正式 runtime、精确模块源码、维护源码、工具/测试及必要 fixture、不可变资源源文件、已批准地图母版、开发手册、设计/逆向记录、现有 Ghidra/Java/验证环境与全局 Skills。

## 后续定位

正式入口：`D:/Games/Magic&Mayham_Remastered_1.1/MagicMayhem-Remastered.exe`。

精确源码映射：`modernization/docs/source-index.json`。

从已退役副本救回的存档按内容去重存放在 `modernization/preserved-player-data/saves/`，原位置和保留位置见 `index.json`。现有正式玩家数据未被覆盖。

旧备份中的独有源码保存在 `modernization/recovered-source/`；文件原名和来源见 `releases/cleanup-20261002-recovered-source.json`。

开发环境按源码保留，不保留全部旧构建缓存。历史 installer/rollback、文档中旧运行目录和旧日志链接可能已失效；不可直接以它们覆盖最终版。新开发必须由用户重新授权，从实际最终 1.1 创建新的独立实验副本。

此次未启动游戏，也未改变正式版本；结束项目并不宣称解决既有未完成的渲染/时序/稳定性问题。

清理计划、删除记录与完整验证：同目录 `cleanup-20261002-*.json` / `*-deleted.txt`。重新静态核验可运行 `python -B modernization/tools/verify_final_cleanup.py`。
