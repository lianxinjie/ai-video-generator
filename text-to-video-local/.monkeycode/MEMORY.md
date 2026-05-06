# 用户指令记忆

本文件记录了用户的指令、偏好和教导，用于在未来的交互中提供参考。

## 格式

### 用户指令条目
用户指令条目应遵循以下格式：

[用户指令摘要]
- Date: [YYYY-MM-DD]
- Context: [提及的场景或时间]
- Instructions:
  - [用户教导或指示的内容，逐行描述]

### 项目知识条目
Agent 在任务执行过程中发现的条目应遵循以下格式：

[项目知识摘要]
- Date: [YYYY-MM-DD]
- Context: Agent 在执行 [具体任务描述] 时发现
- Category: [代码结构 | 代码模式 | 代码生成 | 构建方法 | 测试方法 | 依赖关系 | 环境配置]
- Instructions:
  - [具体的知识点，逐行描述]

## 去重策略
- 添加新条目前，检查是否存在相似或相同的指令
- 若发现重复，跳过新条目或与已有条目合并
- 合并时，更新上下文或日期信息
- 这有助于避免冗余条目，保持记忆文件整洁

## 条目

[用户环境偏好 - 优先 Windows]
- Date: 2026-05-05
- Context: 用户明确要求所有问题优先 Windows 环境
- Instructions:
  - 所有问题和功能优先在 Windows 环境下测试和验证
  - 下载源、镜像、URL 优先确保 Windows 可用
  - 代码生成优先考虑 Windows 兼容性
  - 路径分隔符使用 `\\` 或 `Path()` 处理
  - 可执行文件考虑 `.exe` 后缀
  - 命令行命令考虑 Windows PowerShell/CMD 语法

[FFmpeg Windows 下载源优先级]
- Date: 2026-05-05
- Context: FFmpeg 自动下载功能优化
- Category: 环境配置
- Instructions:
  - 优先使用 GitHub GyanD 镜像 (0.67MB/s, 83MB, 2 分钟)
  - 备选 GitHub BtbN 镜像 (0.77MB/s, 209MB, 4.5 分钟)
  - 最后使用 gyan.dev 官方 (0.21MB/s, 104MB, 8.5 分钟)
  - 自动故障切换到可用镜像
