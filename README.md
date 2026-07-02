# Minimal Multi-Agent Harness v0.3.0

一个最小可运行的 `Planner → Worker → Reviewer` Python 多智能体框架。

## v0.3.0：Context Pack

Context Pack 是一组随每次任务自动加载的稳定知识，用来补充用户的一句话请求。Planner、Worker、Reviewer 会在看到当前任务之前先看到同一份项目背景、业务规则、术语、输出风格、用户偏好和参考样例。模型应优先遵守 Context Pack；若其中内容与用户当前任务冲突，则以当前任务为准。

知识文件位于 `knowledge/`：

```text
knowledge/
├── project_profile.md
├── business_rules.md
├── terminology.md
├── output_style.md
├── user_preferences.md
└── examples/
    ├── report_example.md
    ├── excel_example.md
    └── html_example.md
```

直接编辑对应 Markdown 文件即可维护知识。建议每条规则明确、简短、可验证，样例只保留值得复用的结构与风格。缺失文件会被自动跳过，不会阻断任务；修改后的内容从下一次任务开始生效。

每个任务响应和 `outputs/<task_id>.json` 都包含：

- `context_used`：本次是否加载了知识文件；
- `context_files`：本次实际加载的文件列表。

验证上下文是否生效时，可先在 `output_style.md` 增加一条容易识别的要求，例如“所有总结以风险提示结尾”，再提交：

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"task":"根据项目背景写一份本周进展简报，并生成 Markdown 文件"}'
```

检查响应中的 `context_used`、`context_files`，并确认 Planner 步骤、Worker 结果、Reviewer 最终回答及生成产物遵循该要求。然后提交一条明确冲突的当前任务，也可验证当前任务具有更高优先级。

## 安装

```bash
cd harness-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，至少填写 `OPENAI_API_KEY`。兼容 OpenAI 格式的服务可同时修改 `OPENAI_BASE_URL` 和 `OPENAI_MODEL`。

## 启动

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或：

```bash
python main.py
```

## 请求示例

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"task":"写一份 Python 快速排序的简短说明和示例代码"}'
```

响应中的 `task_id` 可用于查询，完整结果同时保存在 `outputs/<task_id>.json`：

```bash
curl http://127.0.0.1:8000/tasks/<task_id>
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 执行协议

- Planner 固定返回包含 `id`、`description`、`expected_output` 的 JSON 步骤；格式错误时自动纠正一次，仍无效则终止任务。
- Reviewer 返回 `approved` 和 `failed_step_ids`。未通过时仅返工指定步骤；空列表表示全部返工。
- `MAX_REWORK_ROUNDS` 控制最大返工轮数，默认 `2`。响应中的 `review_history` 保留每轮审核记录。
- Worker 可通过 `create_artifact` 生成 Markdown、HTML、Word 和 Excel 文件。路径必须位于 `harness-agent` 目录内，并使用对应扩展名。

## 企业级扩展方向

1. 用 Celery、RQ 或消息队列把同步任务改成异步任务，并增加状态机、超时、重试与取消。
2. 用 PostgreSQL 和对象存储保存任务、轨迹、产物与审计日志。
3. 加入用户认证、租户隔离、配额、限流、敏感信息脱敏与 RBAC。
4. 将 Python 工具放进无网络、低权限、限 CPU/内存的临时容器，增加工具白名单与人工审批。
5. 增加模型路由、结构化输出校验、重试、成本预算、缓存以及降级策略。
6. 使用 LangGraph 表达分支、循环和人工介入，并接入 tracing、指标、日志与告警。
