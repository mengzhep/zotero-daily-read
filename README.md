# Zotero Daily Read

每天从你的 Zotero 图书馆中精选一篇文献，由 AI 进行深度精读，并通过邮件发送给你。

## 核心功能

- **智能选文**：基于加权随机算法，优先选择加入较早、很久没有复习过的论文
- **深度精读**：AI 生成 6 大模块内容：
  1. 为什么今天读这篇？
  2. 核心思想一句话回顾
  3. 研究背景与问题
  4. 核心方法与创新点
  5. 关键结论
  6. 局限性与可改进方向
- **知识卡片**：生成 Anki 风格的 Q&A 记忆卡片
- **思考题**：提供 2 个思考题促进主动回忆
- **延伸阅读**：从你 Zotero 的同一分类中推荐相关论文
- **复习记录**：本地 `data/review_log.json` + Zotero 标签双重记录

## 快速开始

### 1. Fork 本仓库

点击右上角 **Fork**。

### 2. 配置 GitHub Actions Secrets

进入 **Settings → Secrets and variables → Actions → New repository secret**，添加：

| Secret | 说明 |
|--------|------|
| `ZOTERO_ID` | Zotero 数字用户 ID |
| `ZOTERO_KEY` | Zotero API Key（需要写权限来添加复习标签） |
| `SENDER` | 发件邮箱 |
| `SENDER_PASSWORD` | SMTP 授权码 |
| `RECEIVER` | 收件邮箱 |
| `OPENAI_API_KEY` | LLM API Key |
| `OPENAI_API_BASE` | LLM API 地址 |

### 3. 配置 `CUSTOM_CONFIG` 变量

进入 **Settings → Secrets and variables → Actions → Variables → New repository variable**，添加变量名 `CUSTOM_CONFIG`：

```yaml
zotero:
  user_id: ${oc.env:ZOTERO_ID}
  api_key: ${oc.env:ZOTERO_KEY}
  include_path: ["研究生/**", "研究生/**/**"]

email:
  sender: ${oc.env:SENDER}
  receiver: ${oc.env:RECEIVER}
  smtp_server: smtp.qq.com
  smtp_port: 465
  sender_password: ${oc.env:SENDER_PASSWORD}

llm:
  api:
    key: ${oc.env:OPENAI_API_KEY}
    base_url: ${oc.env:OPENAI_API_BASE}
  language: Chinese
  generation_kwargs:
    max_tokens: 16384
    model: kimi-for-coding

executor:
  debug: ${oc.env:DEBUG,null}
```

### 4. 手动测试

进入 **Actions → Test Daily Read → Run workflow**。

### 5. 每日自动运行

主工作流默认每天 UTC 22:30 运行。

## 配置说明

```yaml
daily_read:
  mode: weighted_random        # 选文模式：weighted_random / random / oldest_first
  max_history_days: 30         # 多少天内复习过的论文权重降低
  review_log_path: data/review_log.json  # 复习记录路径
  zotero_tag_prefix: daily-read          # 添加到 Zotero 论文的标签前缀
  num_knowledge_cards: 5       # 知识点卡片数量
  num_thinking_questions: 2    # 思考题数量
  include_related_papers: true # 是否推荐相关论文
  num_related_papers: 3        # 推荐相关论文数量
```

## Anki 导入

邮件中会包含 Anki 牌组的文本内容，格式为 `正面\t背面\n`。你可以：
1. 复制该文本
2. 在 Anki 中选择 "导入"
3. 选择 "制表符分隔" 格式
4. 字段映射为 "正面" 和 "背面"

## 许可证

AGPLv3
