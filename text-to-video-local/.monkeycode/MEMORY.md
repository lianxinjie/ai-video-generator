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

[项目结构概览]
- Date: 2026-05-29
- Context: Agent 在集成云端 AI 配置与多认证支持时梳理
- Category: 代码结构
- Instructions:
  - web/app.py (~4300 行)：Flask 主服务，包含所有 /api/* 路由（config、generate-image、generate-video、task 查询等）
  - web/templates/ai_config.html：/config 页面前端（卡片 UI，多认证表单，测试生成按钮）
  - personal_mode/cloud_platforms.py：云端平台接口层（MGTVImagePlatform 等），负责签名/提交/轮询
  - personal_mode/ai_scene_analyzer.py：AI 场景分析器，支持多通道故障转移
  - config.json：运行时配置文件，`ai_configs` 列表存储所有云端 AI 配置项
  - Python 命令用 `python3`（不是 `python`），运行入口 `python3 web/app.py`，监听 0.0.0.0:5000

[MGTV AIGC API 真实端点（逆向 SPA 发现）]
- Date: 2026-05-27
- Context: Agent 在集成芒果 TV AIGC 图片/视频生成时，通过逆向 index-CwzRxVZG.js 和 aivideo-Bv9GM2mB.js 发现
- Category: 依赖关系
- Instructions:
  - 基础域：https://aigc.mgtv.com，所有 API 以 `/api/v1/` 前缀（小写 v1）
  - 视频模型列表（公开，无需签名）：GET /api/v1/aitools/videoModelList
  - 图片风格列表（需签名）：GET /api/v1/aitools/image/styles
  - 图片生成（需签名）：POST /api/v1/storyboard/generateByPromptv2（小写 v2）
  - 视频生成（需签名）：POST /api/v1/aivideo/generateByPromptv2（小写 v2）
  - 图片轮询（路径参数）：GET /api/v1/storyboard/detail/{imgId}
  - 视频轮询（路径参数）：GET /api/v1/aivideo/detail/{taskId}
  - 批量图片详情：POST /api/v1/storyboard/detailByIds（body: {imgIds: []}）
  - 认证方式：AK/SK HMAC-SHA256，string-to-sign = METHOD\npath\nts\nnonce\nsorted_query
  - 签名头：X-Access-Key, X-Timestamp, X-Nonce, X-Signature
  - 业务错误码 -401 表示"未认证"（AK/SK 错误），公开端点不返回此错误码
  - 返回结构通常为 {code: 200, msg: "success", data: {items: [{code, displayName, description}]}}

[config.json ai_configs 结构]
- Date: 2026-05-29
- Context: Agent 在实现多配置管理时发现
- Category: 代码结构
- Instructions:
  - ai_configs 是一个列表，每项含使用场景 (usage)、认证信息、模型配置、生成参数
  - usage 枚举：scene_analysis / voiceover / image_generation（视频生成共用 image_generation 条目）
  - auth_type 枚举：api_key / cookie / access_key_secret
  - 每项有唯一 id 字段，前端通过 config_id 传给 /api/generate-image 和 /api/generate-video 定位具体卡片
  - get_ai_config(usage, config_id) 优先按 config_id 精确匹配，再按 usage 取首个 enabled 条目
