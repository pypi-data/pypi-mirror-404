# yee88 架构审查计划

## TL;DR

**审查目标**：系统性评估 yee88 架构在扩展性、设计质量、技术债务三个维度的健康度

**核心交付物**：
- 扩展性瓶颈识别报告（含改进方案）
- 架构设计问题清单（含风险评级）
- 技术债务评估（一次性任务功能架构影响分析）
- 重构建议优先级矩阵

**审查范围**：
- IN: plugins.py, cron/, runners/, router.py, scheduler.py, config.py, settings.py, transport_runtime.py
- OUT: telegram/ 详细实现（仅审查接口层）、utils/ 工具函数、tests/ 测试代码

**预计工作量**：8-12 小时审查 + 4 小时报告撰写

---

## 审查维度与发现摘要

基于初步代码分析，已识别以下关键问题：

### 1. 扩展性问题
| 组件 | 现状 | 潜在瓶颈 |
|------|------|----------|
| 插件系统 | entrypoints 设计良好 | 缺少插件生命周期管理（加载/卸载/热更新） |
| Runner 抽象 | JsonlSubprocessRunner 基类完善 | 新引擎添加仍需修改多处代码（backend, runner, entrypoint） |
| 配置系统 | Pydantic + TOML 双层设计 | 配置热重载边界情况未明确 |
| 命令系统 | 基于 entrypoints 简单直接 | 缺少命令发现机制 |

### 2. 架构设计问题
| 问题 | 位置 | 风险级别 |
|------|------|----------|
| 上帝对象 | transport_runtime.py (345行, 18方法) | 中 - 职责过重，难以测试 |
| 循环依赖风险 | config.py 被几乎所有模块导入 | 低-中 - 需验证是否存在实际循环 |
| 状态管理分散 | settings → config → runtime 三级 | 中 - 数据流复杂，可能不一致 |
| 错误处理不一致 | 部分 bare except | 低 - 影响可观测性 |

### 3. 一次性任务功能架构影响
| 方面 | 评估 | 备注 |
|------|------|------|
| 设计合理性 | 良好 | ISO 8601 存储 + 自动清理，设计简洁 |
| 集成度 | 高 | 与现有调度系统无缝整合 |
| 潜在债务 | 低-中 | 时间解析逻辑分散在 CLI 和 Manager 两层 |
| 边界情况 | 待审查 | 时区处理、任务过期、并发执行 |

---

## 并行任务图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           架构审查任务依赖图                              │
└─────────────────────────────────────────────────────────────────────────┘

Wave 1: 基础分析（无依赖，可并行）
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Task 1.1    │  │  Task 1.2    │  │  Task 1.3    │  │  Task 1.4    │
│ 插件系统扩展  │  │  Runner 抽象  │  │ 配置系统扩展  │  │ 命令系统扩展  │
│ 性深度审查   │  │ 层审查       │  │ 性审查       │  │ 性审查       │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                              │
                              ▼
Wave 2: 架构设计审查（依赖 Wave 1 完成）
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Task 2.1    │  │  Task 2.2    │  │  Task 2.3    │  │  Task 2.4    │
│ 分层架构审查  │  │ 依赖关系审查  │  │ 抽象层合规性  │  │ 状态管理审查  │
│             │  │             │  │ 审查         │  │             │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                              │
                              ▼
Wave 3: 专项深度审查（依赖 Wave 1-2）
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Task 3.1    │  │  Task 3.2    │  │  Task 3.3    │
│ Cron 模块架构 │  │ 错误处理审查  │  │ 整合分析    │
│ 影响评估     │  │             │  │ 与报告      │
└──────────────┘  └──────────────┘  └──────────────┘
```

**关键路径**：Task 1.x → Task 2.x → Task 3.3
**并行度**：Wave 1 (4 任务并行) → Wave 2 (4 任务并行) → Wave 3 (3 任务并行)
**理论加速比**：约 3.5x（对比串行执行）

---

## 详细 TODO 列表

### Wave 1: 扩展性审查（高优先级）

#### Task 1.1: 插件系统扩展性深度审查
**目标**：评估当前 entrypoints-based 插件系统的扩展瓶颈

**检查点**：
- [ ] **1.1.1** 审查 `plugins.py` 第 1-313 行
  - 插件发现机制（_discover_entrypoints）
  - 重复插件处理逻辑
  - 加载错误追踪机制
  - 验证器支持

- [ ] **1.1.2** 审查插件生命周期管理
  - 是否有明确的加载阶段？
  - 是否有卸载/禁用机制？
  - 是否支持热更新？
  - 插件间依赖如何处理？

- [ ] **1.1.3** 审查 `engines.py` 第 1-120 行
  - 引擎后端加载流程
  - 配置验证器实现
  - 引擎可用性检查

- [ ] **1.1.4** 审查 `transports.py` 实现
  - 传输层后端加载流程
  - 与引擎加载的差异

- [ ] **1.1.5** 添加新引擎的成本评估
  - 需要修改的文件数
  - 需要理解的接口数
  - 测试覆盖率要求

**输出**：插件系统扩展性评估报告（含改进建议）

---

#### Task 1.2: Runner 抽象层审查
**目标**：评估 Runner 抽象的质量和扩展性

**检查点**：
- [ ] **1.2.1** 审查 `runner.py` 第 1-350 行
  - Runner Protocol 定义
  - BaseRunner 抽象类
  - SessionLockMixin 实现
  - ResumeTokenMixin 实现
  - JsonlSubprocessRunner 具体实现

- [ ] **1.2.2** 审查具体 Runner 实现
  - `runners/codex.py` (行 1-400) - 评估实现复杂度
  - `runners/claude.py` (行 1-300) - 对比 codex 差异
  - `runners/opencode.py` (行 1-350) - 评估通用性
  - `runners/pi.py` (行 1-400) - 识别特殊处理

- [ ] **1.2.3** 评估 Runner 接口稳定性
  - 接口变更历史（git log --oneline runners/）
  - 哪些方法被所有 runner 实现
  - 哪些方法是可选的

- [ ] **1.2.4** 识别 Runner 扩展障碍
  - 是否有引擎特定的硬编码？
  - 配置参数是否统一？
  - 错误处理是否一致？

**输出**：Runner 抽象层评估报告

---

#### Task 1.3: 配置系统扩展性审查
**目标**：评估 Settings → Config → Runtime 三层架构的扩展性

**检查点**：
- [ ] **1.3.1** 审查 `settings.py` 第 1-500 行
  - TakopiSettings 结构
  - Pydantic 验证规则
  - 嵌套配置类设计
  - 环境变量映射

- [ ] **1.3.2** 审查 `config.py` 第 1-200 行
  - ProjectsConfig 结构
  - 配置加载/保存逻辑
  - 迁移机制（config_migrations.py）
  - 配置热重载（config_watch.py）

- [ ] **1.3.3** 评估配置扩展成本
  - 添加新设置字段需要修改的文件
  - 向后兼容性保证机制
  - 配置验证的覆盖范围

- [ ] **1.3.4** 识别配置管理问题
  - 配置分散在多少文件中？
  - 是否有重复配置？
  - 配置优先级是否清晰？

**输出**：配置系统扩展性评估报告

---

#### Task 1.4: 命令系统扩展性审查
**目标**：评估基于 entrypoints 的命令系统扩展性

**检查点**：
- [ ] **1.4.1** 审查 `commands.py` 第 1-100 行
  - CommandBackend 定义
  - 命令发现机制
  - 命令注册流程

- [ ] **1.4.2** 审查 CLI 命令实现（`cli/` 目录）
  - 命令结构模式
  - 参数解析方式
  - 与 core 层交互方式

- [ ] **1.4.3** 评估命令扩展成本
  - 添加新命令需要修改的文件
  - 命令间的依赖关系
  - 命令测试策略

**输出**：命令系统扩展性评估报告

---

### Wave 2: 架构设计审查（中优先级）

#### Task 2.1: 分层架构与职责单一性审查
**目标**：验证各层职责是否清晰，是否存在越界

**检查点**：
- [ ] **2.1.1** 绘制分层架构图
  - CLI Layer → Plugin Layer → Orchestration Layer → Bridge Layer → Runner Layer → Transport Layer
  - 标注每层核心职责

- [ ] **2.1.2** 审查越界调用
  - Transport Layer 是否直接访问 Runner Layer？
  - CLI Layer 是否绕过 Orchestration Layer？
  - Bridge Layer 是否包含业务逻辑？

- [ ] **2.1.3** 审查 `transport_runtime.py` 第 1-345 行
  - 统计方法数量（当前 18 个）
  - 识别不属于该层的逻辑
  - 建议拆分策略

- [ ] **2.1.4** 审查 `runner_bridge.py` 第 1-500 行
  - 桥接层是否只负责转发？
  - 是否包含状态转换逻辑？

**输出**：分层架构合规性报告

---

#### Task 2.2: 依赖关系审查
**目标**：识别循环依赖和不当依赖

**检查点**：
- [ ] **2.2.1** 生成模块依赖图
  ```bash
  # 使用 pydeps 或手动分析
  find src/yee88 -name "*.py" -exec grep -l "from \.config import\|import.*config" {} \;
  ```

- [ ] **2.2.2** 审查 `config.py` 导入范围
  - 哪些模块导入了 config？
  - config 是否导入了这些模块？（循环依赖）
  - 是否存在延迟导入（TYPE_CHECKING）？

- [ ] **2.2.3** 审查 `settings.py` 与 `config.py` 关系
  - 双向依赖？
  - 依赖方向是否合理？

- [ ] **2.2.4** 识别并记录所有可疑依赖
  - utils/ 被上层模块导入情况
  - model.py 的依赖范围

**输出**：依赖关系分析报告

---

#### Task 2.3: 抽象层与依赖倒置审查
**目标**：验证抽象是否充分，是否遵循依赖倒置原则

**检查点**：
- [ ] **2.3.1** 审查接口定义
  - Runner (Protocol) 定义完整性
  - Transport (Protocol) 定义完整性
  - Backend 抽象一致性

- [ ] **2.3.2** 审查具体实现依赖
  - 上层是否依赖具体实现？
  - 依赖注入是否使用？

- [ ] **2.3.3** 识别抽象泄漏
  - CodexRunner 特定逻辑是否泄漏到通用层？
  - Telegram 特定逻辑是否泄漏到 Transport 抽象？

**输出**：抽象层合规性报告

---

#### Task 2.4: 状态管理审查
**目标**：评估多级状态管理的合理性和一致性风险

**检查点**：
- [ ] **2.4.1** 绘制状态流转图
  - Settings (静态配置)
  - ProjectsConfig (运行时配置)
  - TransportRuntime (运行时状态)
  - ThreadScheduler (调度状态)

- [ ] **2.4.2** 审查状态同步机制
  - settings → config 转换逻辑
  - config 热重载触发条件
  - runtime 状态更新时机

- [ ] **2.4.3** 识别状态不一致风险点
  - 并发修改场景
  - 配置热重载边界
  - 持久化与内存状态差异

**输出**：状态管理评估报告

---

### Wave 3: 专项深度审查（高优先级）

#### Task 3.1: Cron 模块架构影响评估
**目标**：深度评估一次性任务功能的架构影响

**检查点**：
- [ ] **3.1.1** 审查 `cron/models.py` 第 1-14 行
  - CronJob 数据结构
  - one_time 字段语义
  - 字段命名一致性

- [ ] **3.1.2** 审查 `cron/manager.py` 第 1-141 行
  - 任务持久化格式（TOML）
  - 时间解析逻辑（_parse_one_time 在 cli/cron.py）
  - get_due_jobs 执行逻辑
  - 一次性任务自动清理机制

- [ ] **3.1.3** 审查 `cron/scheduler.py` 第 1-58 行
  - 调度循环设计
  - 任务执行并发控制
  - 错误处理策略

- [ ] **3.1.4** 边界情况分析
  - 时区处理（是否使用 UTC？）
  - 任务过期处理（过期的 +30m 任务）
  - 并发执行风险（同一任务的多次触发）
  - 任务持久化原子性

- [ ] **3.1.5** 与现有系统集成评估
  - 与 ThreadScheduler 的协作
  - 与 TransportRuntime 的交互
  - 配置共享机制

**输出**：Cron 模块架构影响评估报告

---

#### Task 3.2: 错误处理一致性审查
**目标**：评估错误处理策略的统一性

**检查点**：
- [ ] **3.2.1** 审查异常层次结构
  - ConfigError 使用范围
  - PluginLoadFailed / PluginNotFound 使用
  - RunnerUnavailableError 使用

- [ ] **3.2.2** 审查错误处理模式
  - scheduler.py 第 147-156 行的 bare except
  - cron/scheduler.py 第 47-53 行的错误处理
  - runner.py 第 259-273 行的错误转换

- [ ] **3.2.3** 评估日志记录一致性
  - 结构化日志使用情况
  - 错误上下文完整性
  - 日志级别合理性

- [ ] **3.2.4** 识别错误处理改进点
  - 需要添加特定异常的场景
  - 需要收紧异常捕获的范围

**输出**：错误处理一致性报告

---

#### Task 3.3: 整合分析与最终报告
**目标**：汇总所有审查结果，生成优先级矩阵和重构建议

**检查点**：
- [ ] **3.3.1** 汇总所有子任务发现
  - 整理各任务的 Critical/Warning/Info 级别问题
  - 去重和归类

- [ ] **3.3.2** 风险优先级矩阵
  | 问题 | 影响 | 修复成本 | 优先级 | 建议行动 |
  |------|------|----------|--------|----------|

- [ ] **3.3.3** 重构路线图
  - 短期（1-2 周）：低风险高价值改进
  - 中期（1-2 月）：架构债务清理
  - 长期（3-6 月）：重大重构

- [ ] **3.3.4** 编写最终架构审查报告
  - 执行摘要（面向决策者）
  - 详细发现（面向开发者）
  - 改进建议（含代码示例）
  - 实施路线图

**输出**：完整架构审查报告

---

## 任务类别与技能建议

### 任务分类表

| Task | 类别 | 建议技能 | 预估时间 | 难度 |
|------|------|----------|----------|------|
| 1.1 插件系统 | 代码审查 | python, architecture-analysis | 2h | 中 |
| 1.2 Runner 抽象 | 代码审查 | python, design-patterns | 2h | 中 |
| 1.3 配置系统 | 代码审查 | python, pydantic | 1.5h | 低-中 |
| 1.4 命令系统 | 代码审查 | python, cli-design | 1h | 低 |
| 2.1 分层架构 | 架构分析 | architecture-analysis, layering | 2h | 中 |
| 2.2 依赖关系 | 架构分析 | python, dependency-analysis | 1.5h | 中 |
| 2.3 抽象层 | 架构分析 | design-patterns, solid-principles | 1.5h | 中 |
| 2.4 状态管理 | 架构分析 | state-management, concurrency | 1.5h | 中 |
| 3.1 Cron 模块 | 专项审查 | python, cron, datetime | 1.5h | 中 |
| 3.2 错误处理 | 代码质量 | python, exception-handling | 1h | 低 |
| 3.3 整合报告 | 文档撰写 | technical-writing, analysis | 4h | 中 |

### 推荐 Agent 配置

**Wave 1 任务（代码审查类）**：
```yaml
recommended_agent:
  category: quick
  skills: ["python", "ast-grep", "lsp-diagnostics"]
  run_in_background: true
```

**Wave 2 任务（架构分析类）**：
```yaml
recommended_agent:
  category: ultrabrain
  skills: ["architecture-analysis", "oracle"]
  run_in_background: true
```

**Wave 3 任务（专项 + 报告）**：
```yaml
recommended_agent:
  category: writing
  skills: ["tech-docs-creator", "humanizer-zh"]
  run_in_background: false  # 需要人工确认最终报告
```

---

## 执行策略

### 并行执行建议

**方案 A：全力并行（推荐）**
- 同时启动 Wave 1 全部 4 个任务
- Wave 1 完成后同时启动 Wave 2 全部 4 个任务
- Wave 3 按顺序执行（3.1 → 3.2 → 3.3）
- **总时间**：约 6-8 小时（含报告）

**方案 B：保守串行**
- 按优先级逐个执行任务
- **总时间**：约 12-15 小时

### 依赖管理

```
# 依赖图说明
Wave 1 (4 任务): 相互独立，可完全并行
Wave 2 (4 任务): 依赖 Wave 1 完成，内部相互独立
Wave 3 (3 任务): 
  - 3.1 (Cron) 依赖 Wave 1 完成
  - 3.2 (错误处理) 依赖 Wave 1-2 完成
  - 3.3 (报告) 依赖所有前置任务
```

### 风险控制

| 风险 | 概率 | 缓解措施 |
|------|------|----------|
| 任务发现重叠问题 | 中 | 每日站会同步发现 |
| 单个任务超时 | 低 | 设置 3 小时超时，超时则拆分 |
| 报告整合困难 | 中 | 统一模板，提前评审模板 |

---

## 审查入口点

### 快速开始命令

```bash
# 查看项目结构
tree -L 2 src/yee88/

# 统计代码行数
find src/yee88 -name "*.py" -not -path "*/__pycache__/*" | xargs wc -l | sort -n

# 查看最近修改
git log --oneline --since="2 weeks ago" --name-only | head -50

# 查看依赖关系
grep -r "^from yee88\." src/yee88/ | grep -v __pycache__ | cut -d: -f2 | sort | uniq -c | sort -rn | head -20
```

### 关键文件清单

**必须审查**：
1. `src/yee88/plugins.py` - 插件系统核心
2. `src/yee88/cron/manager.py` - 定时任务管理
3. `src/yee88/cron/scheduler.py` - 定时任务调度
4. `src/yee88/runner.py` - Runner 抽象基类
5. `src/yee88/router.py` - 自动路由
6. `src/yee88/scheduler.py` - 线程调度
7. `src/yee88/transport_runtime.py` - 运行时门面
8. `src/yee88/settings.py` - 配置定义
9. `src/yee88/config.py` - 配置管理

**参考审查**：
1. `src/yee88/runners/codex.py` - Runner 实现示例
2. `src/yee88/telegram/bridge.py` - Transport 实现
3. `src/yee88/commands.py` - 命令系统
4. `pyproject.toml` - 项目配置和 entrypoints

---

## 验收标准

### 每个子任务的验收标准

**代码审查类任务（1.x, 2.x, 3.1-3.2）**：
- [ ] 完成所有检查点的代码审查
- [ ] 记录至少 3 个具体问题（Critical/Warning/Info）
- [ ] 提供改进建议（含代码示例）
- [ ] 输出 Markdown 格式的子报告

**整合报告任务（3.3）**：
- [ ] 汇总所有子任务发现
- [ ] 风险优先级矩阵完整
- [ ] 重构路线图清晰（含时间估算）
- [ ] 最终报告通过 Momus 审查（如启用高精度模式）

### 整体项目验收

- [ ] 所有 11 个任务完成
- [ ] 发现的问题分类清晰（Critical ≤ 5, Warning ≤ 10, Info ≤ 20）
- [ ] 提供可执行的重构建议
- [ ] 报告通过技术评审

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Entrypoint | Python 包元数据中的插件注册点 |
| Runner | AI 引擎适配器抽象 |
| Transport | 消息传输层抽象（如 Telegram） |
| Bridge | 连接 Transport 和 Runner 的中间层 |
| 上帝对象 | 职责过多、方法过多的类 |
| 循环依赖 | 模块 A 导入 B，B 又导入 A |

### B. 参考资料

- [pyproject.toml entrypoints](https://packaging.python.org/en/latest/specifications/entry-points/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Python Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

### C. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-31 | 初始版本 |

---

**计划完成时间**：2026-01-31
**计划编制者**：Prometheus（架构规划 Agent）
**审核状态**：待审核
