# 技术交流评估报告生成器

基于技术交流/考察素材，产出结构化技术评估报告的 Claude Code skill。

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

## 输出

报告为 Markdown 格式，包含八个章节：执行摘要、交流背景、对方技术主张、我方现场观感、行业基准对照、多维评估、适配性与引入路径、风险与待核实清单。

如需转为 Word 文档，可后续使用 `minimax-docx` 技能处理。
