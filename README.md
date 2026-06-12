# 技术交流评估报告生成器

基于技术交流/考察素材，产出结构化技术评估报告的 MiMo Code 技能。回答"这项技术到底行不行、值不值得进一步探索"。

## 项目特点

- **三阶段并行流水线** - 素材读取与行业检索并行执行
- **CRITIC 对抗审查** - 自动检查报告中的矛盾和偏见
- **FACT-CHECKER 数值核验** - 确保所有数值声明准确无误
- **双格式输出** - 同时生成 Word 文档和 HTML 可视化报告

## 安装

将 `tech-exchange-evaluator/` 目录复制到 MiMo Code 的 skills 目录下。

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
└─ Agent-B [行业检索] ──→ 行业基准包（7次并行搜索）

Phase 2（串行）
└─ Agent-C [报告撰写] ──→ CRITIC对抗审查 + FACT-CHECKER数值核验

Phase 3（串行）
└─ 主Agent [双格式输出] ──→ Word文档 + HTML可视化报告
```

## 输出

报告自动输出为 Word 文档和 HTML 可视化报告，保存在 `output/` 目录下。

- 精简版：`技术评估报告_{日期}_{技术主题}.docx`
- 完整版：`技术评估报告_{日期}_{技术主题}_完整版.docx`
- HTML 版：`技术评估报告_{日期}_{技术主题}.html`
- 图表数据：`report_data.json`

## 技术栈

- **Python 3.11+**
- **测试框架**：pytest
- **配置管理**：YAML + 环境变量
- **消息队列**：异步消息队列
- **状态管理**：检查点 + 断点续传
- **安全防护**：XSS/SQL 注入防护

## 开发

```bash
# 安装依赖
pip install pytest pytest-asyncio

# 运行测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 生成覆盖率报告
pytest --cov=src tests/
```

## 项目结构

```
tech-eval-micode/
├── src/                    # 源代码
│   ├── config/            # 配置加载器
│   ├── pipeline/          # 流水线引擎
│   ├── state/             # 状态管理器
│   ├── communication/     # 消息队列
│   ├── search/            # 搜索验证器
│   ├── quality/           # 质量评分器
│   └── security/          # 安全模块
├── tests/                  # 测试文件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   ├── regression/        # 回归测试
│   └── fixtures/          # 测试数据
├── config/                 # 配置文件
├── tech-exchange-evaluator/ # MiMo Code 技能
├── micode.yaml             # MiMo Code 配置
└── pyproject.toml          # Python 项目配置
```

## 许可证

MIT License
