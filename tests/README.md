# 测试配置

## 测试目录结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_material_reader.py    # 素材读取测试
│   ├── test_benchmark_searcher.py # 行业检索测试
│   ├── test_report_writer.py      # 报告撰写测试
│   └── test_fact_checker.py       # 数值核验测试
├── integration/             # 集成测试
│   ├── test_pipeline_flow.py      # 流水线流程测试
│   └── test_agent_coordination.py # Agent协调测试
├── regression/              # 回归测试
│   ├── test_report_quality.py     # 报告质量测试
│   └── test_output_consistency.py # 输出一致性测试
└── fixtures/                # 测试数据
    ├── sample_transcript.md       # 示例转写文本
    ├── sample_counterpart/        # 示例对方文档
    └── sample_benchmark/          # 示例基准文档
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行回归测试
pytest tests/regression/

# 生成覆盖率报告
pytest --cov=src tests/
```

## 测试原则

1. **独立性** - 每个测试独立运行，不依赖其他测试
2. **可重复** - 测试结果可重复，不依赖外部状态
3. **快速** - 单元测试应在秒级完成
4. **清晰** - 测试名称和断言清晰表达意图
