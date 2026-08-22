# 🎬 工业级端到端全自动审稿工作流规范 (Workflow Specification v3.1)

本文档定义了 `script-review-lead` 驱动的**端到端全自动、多智能体协同、纯 Markdown 增量滚雪球审稿工作流**的执行标准与规约。

---

## 1. 工作区目录标准结构 (Workspace Standard Layout)

当用户发起全量或长篇剧本审查时，系统自动在当前工作区建立如下**基于剧本名称自动隔离**的目录树：

```
📁 .script_review_workspace/
└── 📁 <剧本名>/                         # 自动按剧本名称隔离独立命名空间
    ├── 📁 episodes/                    # 原始剧本自动切分落盘目录
    │   ├── ep_001.md                   # 第 1 集/幕 独立剧本文件
    │   ├── ep_002.md                   # 第 2 集/幕 独立剧本文件
    │   └── ...
    ├── 📁 ledgers/                     # 纯 Markdown 高密度台账与变更日志
    │   ├── global_ledgers.md           # 当前最新全剧四大资产总台账 (纯净表头基准)
    │   ├── changelog_ep_001.md         # 第 1 集引起的台账变更 Diff 日志
    │   ├── changelog_ep_002.md         # 第 2 集引起的台账变更 Diff 日志
    │   ├── 📁 snapshots/               # (长剧集 >20集) 每10集台账快照备份
    │   │   ├── global_ledgers_ep_010.md
    │   │   └── ...
    │   └── ...
    ├── 📁 reports/                     # 分集独立审查报告
    │   ├── report_ep_001.md            # 第 1 集综合审查报告
    │   ├── report_ep_002.md            # 第 2 集综合审查报告
    │   └── ...
    └── 📄 final_whitepaper.md          # 全剧终极宏观审改白皮书 (Final Executive Report)
```

---

## 2. 五阶段端到端执行流程 (5-Stage Pipeline)

```
[原始长剧本文档]
       │
       ▼ 【Stage 1: 智能分章落盘 (Script Chapter Splitting)】
[ep_001.md, ep_002.md, ..., ep_N.md] + [ledgers/global_ledgers.md] (落盘至 <剧本名>/)
       │
       ▼ 【Stage 2: 增量滚雪球审查循环 (Snowball Loop · i=1..N)】
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 1. 载入: ep_i.md + 当前 ledgers/global_ledgers.md                       │
 │ 2. 并行派发 4 大专项子 Agent 审查 (Continuity/Logic/Psychology/Prod)    │
 │    (子 Agent 先通过 view_file 装载对应 SKILL.md，再读取剧本与台账)       │
 │ 3. script-review-lead 聚合 4 份报告，生成双向修补 Diff                 │
 │ 4. 物理写盘分集报告: reports/report_ep_i.md                            │
 │ 5. 物理写盘增量日志: ledgers/changelog_ep_i.md                         │
 │ 6. 遵循铁律原地演进: ledgers/global_ledgers.md (继承至第 i+1 集)        │
 └──────────────────────────────────┬─────────────────────────────────────┘
       │ (循环结束，所有章节完成)
       ▼ 【Stage 3: 全景宏观复盘 (Macro Bird's-Eye Synthesis)】
[审计全剧戏剧压力曲线 + 终极伏笔闭环率 + 人物弧光总盘点 + P0 双向 Diff 汇总]
       │
       ▼ 【Stage 4: 交付终极白皮书 (Final Delivery)】
[物理落盘 final_whitepaper.md + 生成 IDE 交付物 Artifact]
       │
       ▼ 【Stage 5: 用户结构化交互汇报 (Final Presentation)】
[向用户展示评级、压力曲线表、P0 修补清单与下一步修改路线图]
```

---

## 3. 分章识别与切分规则 (Splitting Rules)

分章器按以下优先级顺序匹配剧本中的章节/集数切分标记：
1. **明确集数标记**：`第[一二三四五六七八九十0-9]+[集话回]`、`EPISODE [0-9]+`、`EP[0-9]+`、`【第X集】`；
2. **院线电影幕次标记**：`第[一二三四1-4]幕`、`ACT [I|II|III|IV|1-4]`、`Sequence [1-8]`；
3. **纯场次自适应分块**：
   - 若单集无明确集头但含场次标记（`第X场`、`SCENE X`、`01-01 内景` 等 >= 5 场）：
   - 微短剧 (`short_drama`) 按每 10 场为一个审查单元；
   - 电影 (`movie`) 与电视剧 (`series`) 按每 15 场为一个审查单元。
4. **长文本语义分段兜底**：
   - 若文本超长 (> 3500 字符) 且无任何集/场标记，按双换行语义段落聚类（每段约 3000 字）自动切分，防止单章注意力衰减。

---

## 4. 四大专家子 Agent 并行调用协议与反架空防线 (Anti-Bypass Protocol)

### 4.1 多智能体原生调用硬性铁律与执行门禁
1. **严禁 Lead 越权代写与脚本伪造**：Lead Agent 严禁在自身主上下文中直接输出或通过编写/运行本地 Python 脚本批量伪造生成 4 大专家的分集审查报告。
2. **必须真实唤醒子 Agent**：针对每一个切分章节 `ep_i.md`（$i = 1 \dots N$），必须调用 `invoke_subagent` 真实唤醒 4 个独立的专家子 Agent（场记、逻辑、心理、制片），并等待接收系统推送的子 Agent 真实审查报告。
3. **🚨 批次写盘硬门禁 (Batch Execution Gate)**：每批次（1~3集）子 Agent 审查完成后，Lead Agent **必须在当前回合立即调用预置写盘引擎 `batch_writer.py` 完成分集报告、增量日志与总台账三步物理写盘**；在未完成写盘与台账演进前，**严禁调用 `invoke_subagent` 派发下一批次！**
4. **⚡ 严禁 `schedule` 轮询**：Antigravity 具有原生反应式消息唤醒机制。每次调用 `invoke_subagent` 后，**严禁调用 `schedule` 工具或运行 sleep 命令进行轮询**，直接结束当前回合等待系统通知即可。
5. **长剧集分批推进机制**：针对多集长篇剧本（如 10~100 集），Lead Agent 严格按批次（如每批 1~3 集）依次调用 `invoke_subagent` 推进，在完成当前批次写盘与台账演进后，再推进下一批。

### 4.2 专家子 Agent 派发规约
在审查第 i 集时，总控并发调用以下 4 个技能（子 Agent 接收文件路径并首先通过 `view_file` 加载技能规则）：

| 专家 Agent | 接收输入路径 (推荐绝对路径) | 核心审查职责 | 产出重点 |
| :--- | :--- | :--- | :--- |
| **script-continuity-auditor** | `<plugin_path>/skills/script-continuity-auditor/SKILL.md`<br>`episodes/ep_i.md`<br>`ledgers/global_ledgers.md` | 工业场头格式、出场核验、空间轴线、道具状态机、伤病生理演变、微观不可拍摄小说描写 | 动作连贯 Diff、道具状态变更项 |
| **script-logic-timeline-checker** | `<plugin_path>/skills/script-logic-timeline-checker/SKILL.md`<br>`episodes/ep_i.md`<br>`ledgers/global_ledgers.md` | 因果链、机械降神、伏笔闭环、信息差、集尾钩子、戏剧压力指数 (1-10) | 双向因果 Diff、伏笔变更项、压力评估 |
| **script-character-psychology-analyzer** | `<plugin_path>/skills/script-character-psychology-analyzer/SKILL.md`<br>`episodes/ep_i.md`<br>`ledgers/global_ledgers.md` | 人设一致性 (OOC)、权力位阶 (Status Shift)、情感账户收支、说明性对白排查 | Show Don't Tell 视听示范、情感账户变更项 |
| **script-production-domain-expert** | `<plugin_path>/skills/script-production-domain-expert/SKILL.md`<br>`episodes/ep_i.md`<br>`ledgers/global_ledgers.md` | 政策合规红线、行业专业常识（医/法/刑/商）、版权融梗、纯心理描写镜头化、预算黑洞 | 合规替换 Diff、制片合规变更项、降本建议 |

---

## 5. 纯 Markdown 台账状态机演进四大铁律

1. **全量继承，严禁丢行**：历史轮次记录的所有条目（含已闭环 `[✓]`、待回收 `[+]`/`[⚠️]`、锁定 `[LOCKED]`）必须 100% 完整保留在表中，严禁删除历史行。
2. **ID 严格单调递增**：新项 ID 必须按最大已有 ID 顺延（如 `F-01`, `F-02` ➔ `F-03`），严禁断号或重复编号。
3. **锁定项不可篡改**：凡带有 `[LOCKED]` 标记的条目，后续轮次强制作为不可撼动的基准设定，严禁篡改。
4. **增量必记 Changelog**：当集的所有增量更新（新增/演进/闭环）必须同步记录到 `ledgers/changelog_ep_i.md`。

---

## 6. 断点续审与长剧集快照机制 (Resume & Snapshots)

1. **断点无缝续审**：若审查因故中断，系统自动扫描 `.script_review_workspace/<剧本名>/reports/` 目录下已生成的 `report_ep_*.md` 文件。系统将自动跳过已完成的章节，直接从第 k+1 集继续无缝推进审查。
2. **分卷阶段快照**：长剧集 (>20 集) 审查过程中，写盘引擎自动在跨越满 10 集里程碑（如第 10、20、30 集）时将最新总台账归档至 `ledgers/snapshots/global_ledgers_ep_i.md`（自适应兼容 1~5 集等任意批次步长），有效防止因多轮 Markdown 重写导致的历史条目意外丢失。

---

## 7. 全剧终极白皮书 (final_whitepaper.md) 标准结构

1. **项目概况与商业完成度评级** (S / A / B / C)
2. **全剧戏剧压力与节奏曲线图谱** (基于全集 1~10 分压力值识别中段塌陷与注水戏)
3. **全剧四大资产总台账** (全量伏笔闭环率统计、全景道具生命周期表、终极人物关系网)
4. **全剧 P0 级致命硬伤汇总与双向修补 Diff 清单** (清零指南)
5. **全剧 P1 级重点视听化打磨集锦** (精选 Show, Don't Tell 改写示范)
6. **分集报告索引与下一步工业化修改路标 (Action Roadmap)**
