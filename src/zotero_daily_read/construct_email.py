from .protocol import ReadingSummary
from .utils import _is_chinese


framework = """
<!DOCTYPE HTML>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; color: #333; line-height: 1.6; }
    h1 { color: #2c3e50; }
    h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 6px; margin-top: 28px; }
    .meta { color: #666; font-size: 14px; margin-bottom: 16px; }
    .section { margin-bottom: 16px; }
    .card { background-color: #fffbe6; border-left: 4px solid #f0ad4e; padding: 12px; margin: 10px 0; border-radius: 4px; }
    .card strong { color: #8a6d3b; }
    .question { background-color: #e8f4fd; border-left: 4px solid #5bc0de; padding: 12px; margin: 10px 0; border-radius: 4px; }
    .related { background-color: #f9f9f9; padding: 10px; border-radius: 4px; }
    .anki { background-color: #f0f8ff; padding: 12px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }
    a { color: #d9534f; text-decoration: none; }
    .pdf-btn { display: inline-block; background-color: #d9534f; color: #fff; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
  </style>
</head>
<body>
__CONTENT__
<br><br>
<div style="color:#999;font-size:12px;">__FOOTER__</div>
</body>
</html>
"""


def render_email(summary: ReadingSummary, language: str = "English") -> str:
    if _is_chinese(language):
        labels = {
            "title": "📚 今日精读",
            "why_today": "一、为什么今天读这篇？",
            "core_idea": "二、核心思想一句话回顾",
            "background": "三、研究背景与问题",
            "methods": "四、核心方法与创新点",
            "conclusions": "五、关键结论",
            "limitations": "六、局限性与可改进方向",
            "knowledge_cards": "七、知识点小卡片（Anki 记忆卡）",
            "thinking_questions": "八、思考题",
            "related_papers": "九、延伸阅读建议",
            "anki_deck": "十、Anki 牌组导入内容",
            "footer": "如需退订，请在 GitHub Action 设置中移除您的邮箱。",
            "pdf": "PDF",
            "added": "加入时间",
            "collections": "所属分类",
            "authors": "作者",
            "no_related": "暂无相关推荐",
        }
    else:
        labels = {
            "title": "📚 Daily Deep Read",
            "why_today": "1. Why this paper today?",
            "core_idea": "2. Core idea in one sentence",
            "background": "3. Background and problem",
            "methods": "4. Methods and innovation",
            "conclusions": "5. Key conclusions",
            "limitations": "6. Limitations and future work",
            "knowledge_cards": "7. Knowledge cards (Anki)",
            "thinking_questions": "8. Thinking questions",
            "related_papers": "9. Related reading",
            "anki_deck": "10. Anki deck import",
            "footer": "To unsubscribe, remove your email in your Github Action setting.",
            "pdf": "PDF",
            "added": "Added",
            "collections": "Collections",
            "authors": "Authors",
            "no_related": "No related recommendations",
        }

    paper = summary.paper
    content_parts = []

    # Header
    content_parts.append(f"<h1>{labels['title']}</h1>")
    content_parts.append(f"<div class='meta'>")
    content_parts.append(f"<strong>{paper.title}</strong><br>")
    content_parts.append(f"{labels['authors']}: {', '.join(paper.authors)}<br>")
    content_parts.append(f"{labels['added']}: {paper.added_date.strftime('%Y-%m-%d')}<br>")
    content_parts.append(f"{labels['collections']}: {' / '.join(paper.paths)}")
    content_parts.append("</div>")

    if paper.pdf_url:
        content_parts.append(f"<p><a href='{paper.pdf_url}' class='pdf-btn'>{labels['pdf']}</a></p>")

    # Why today
    content_parts.append(f"<h2>{labels['why_today']}</h2>")
    content_parts.append(f"<div class='section'>{summary.why_today}</div>")

    # Core idea
    content_parts.append(f"<h2>{labels['core_idea']}</h2>")
    content_parts.append(f"<div class='section'>{summary.core_idea}</div>")

    # Background
    content_parts.append(f"<h2>{labels['background']}</h2>")
    content_parts.append(f"<div class='section'>{summary.background}</div>")

    # Methods
    content_parts.append(f"<h2>{labels['methods']}</h2>")
    content_parts.append(f"<div class='section'>{summary.methods}</div>")

    # Conclusions
    content_parts.append(f"<h2>{labels['conclusions']}</h2>")
    content_parts.append(f"<div class='section'>{summary.conclusions}</div>")

    # Limitations
    content_parts.append(f"<h2>{labels['limitations']}</h2>")
    content_parts.append(f"<div class='section'>{summary.limitations}</div>")

    # Knowledge cards
    content_parts.append(f"<h2>{labels['knowledge_cards']}</h2>")
    for card in summary.knowledge_cards:
        q = card.get("question", "")
        a = card.get("answer", "")
        content_parts.append(f"<div class='card'><strong>Q:</strong> {q}<br><strong>A:</strong> {a}</div>")

    # Thinking questions
    content_parts.append(f"<h2>{labels['thinking_questions']}</h2>")
    for q in summary.thinking_questions:
        content_parts.append(f"<div class='question'>{q}</div>")

    # Related papers
    content_parts.append(f"<h2>{labels['related_papers']}</h2>")
    if summary.related_papers:
        content_parts.append("<div class='related'><ul>")
        for rp in summary.related_papers:
            url = rp.get("url", "")
            title = rp.get("title", "")
            if url:
                content_parts.append(f"<li><a href='{url}'>{title}</a></li>")
            else:
                content_parts.append(f"<li>{title}</li>")
        content_parts.append("</ul></div>")
    else:
        content_parts.append(f"<div class='related'>{labels['no_related']}</div>")

    # Anki deck
    if summary.anki_deck:
        content_parts.append(f"<h2>{labels['anki_deck']}</h2>")
        content_parts.append(f"<div class='anki'>{summary.anki_deck}</div>")

    content = "\n".join(content_parts)
    return framework.replace("__CONTENT__", content).replace("__FOOTER__", labels["footer"])
