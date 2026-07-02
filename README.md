# Minimal Multi-Agent Harness

一个最小可运行的 `Planner → Worker → Reviewer` Python 多智能体框架。

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
