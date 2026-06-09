# 技术交流评估报告生成器

基于技术交流/考察素材，产出结构化技术评估报告的 Claude Code skill。回答"这项技术到底行不行、值不值得进一步探索"。

## 安装

本项目的 `.claude/commands/tech-exchange-evaluation.md` 已就绪，在项目目录下直接使用：

```
/tech-exchange-evaluation
```

## 素材准备

```
input/
├── transcript.md          # 会议转写文本（必须）
├── counterpart/           # 对方技术文档（可选）
│   ├── 产品白皮书.pdf
│   └── 技术方案.md
└── benchmark/             # 我方参考基准文档（可选）
    ├── 行业标准.md
    └── 内部调研报告.pdf
```

- Markdown（.md）直接放入，无需处理
- PDF（.pdf）直接放入，工具原生支持
- Word（.docx）需先转换：`pandoc xxx.docx -o xxx.md`

## 使用示例

```
/tech-exchange-evaluation
transcript 是 input/transcript.md，
benchmark 放在 input/benchmark/ 目录下
```

如果没有参考基准文档，只提供转写文本也可以——报告会在相应章节标注置信度降级。

## 报告版本

| 版本 | 命令 | 章节 | 适用场景 |
|------|------|------|---------|
| **精简版（默认）** | `/tech-exchange-evaluation` | 4章 | 快速决策，重点突出 |
| **完整版** | `/tech-exchange-evaluation --full` | 8章 | 详细存档，全面分析 |

### 精简版结构（4章）

1. **执行摘要** — 结论先行，3-5句话
2. **交流背景** — 对方是谁、交流形式、核心技术
3. **对方技术主张** — 事实层，标注来源
4. **初步结论** — 核心发现 + 量化分析 + 推荐方案与决策路径 + 风险 + 待核实清单

### 完整版结构（8章）

1. 执行摘要
2. 交流背景
3. 对方技术主张（事实层）
4. 我方现场观感
5. 行业基准对照
6. 多维评估（判断层）
7. 适配性与决策路径
8. 风险与待核实清单

## 执行流程

采用三阶段并行流水线：

```
Phase 1（并行）
├─ Agent-A [素材读取] ──→ 结构化素材包
└─ Agent-B [行业检索] ──→ 行业基准包（6次Tavily搜索）

Phase 2（串行）
└─ Agent-C [报告撰写] ──→ CRITIC对抗审查 + FACT-CHECKER数值核验

Phase 3（串行）
└─ 主Agent [DOCX生成] ──→ Word文档
```

## 输出

报告自动输出为 Word 文档（.docx），保存在 `output/` 目录下。

- 精简版：`技术评估报告_{日期}_{技术主题}.docx`
- 完整版：`技术评估报告_{日期}_{技术主题}_完整版.docx`
