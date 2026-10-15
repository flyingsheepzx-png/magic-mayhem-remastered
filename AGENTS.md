# 社区开发规则

- 本仓库根目录就是 DEV_ROOT。先读 README.md、docs/SOURCE_MAP.md、docs/BUILDING.md，再读 modernization/docs/agent-development-manual-1.1.md 与 source-index.json。
- 基线为 2026-10-02 实际正式 Remastered 1.1。当前精确模块映射优先于历史 v38/“latest development”记录；101 与 102 来自不同快照。
- 本仓库只公开扩展源码与研究工具，不是完整原游戏源码。禁止将原游戏、素材、玩家存档、私有配置、凭证、日志转储、模型权重或 out/ 加入 Git。
- 修改一个明确问题，保留既有功能。未知可执行文件哈希必须拒绝地址式安装；不能把任意新算出的哈希直接当可信版本。
- 单人 AI budget300 与 danger refresh16/128、多人原策略和 installer 链必须保留。一次只做一个优化，等待实际游戏反馈后继续。
- 保持原生 UI1920×1440 与战斗1280×720缩放2倍的混合策略、字体边界、中文、存档格式、OGG、PNG loader、FMV和现有输入状态机。
- 新构建和离线 harness 用 dev.py。原始构建快照与历史脚本供研究，可能引用旧路径。输出只写 out/；测试不得修改玩家包。
- 默认由用户进行游戏验收。仅在明确授权后启动独立游戏副本，优先后台输入和只读遥测；存档与设置隔离，不按名字批量结束进程。
- 安装之前准备备份、哈希核对与可执行回滚。编译通过、wrapper呈现帧率或分辨率检查不等于 gameplay/视觉验收。
- 持久规则写 AGENTS.md，设计/证据写 modernization/docs/，计划写 modernization/PLAN.md，行为要求写测试。优先现有权威文档，不记录秘密或临时调试状态。
- 历史全局 Skills、NAS、盘符或模型服务不是社区开发前提。素材生成默认复用合法现成输入；本次源码公开不授权自动继续作者已结束的1.2任务。
