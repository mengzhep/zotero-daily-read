import json
import tiktoken
from openai import OpenAI
from loguru import logger
from omegaconf import DictConfig
from .protocol import ZoteroPaper, ReadingSummary
from .utils import _is_chinese


class Summarizer:
    def __init__(self, config: DictConfig):
        self.config = config
        self.openai_client = OpenAI(api_key=config.llm.api.key, base_url=config.llm.api.base_url)
        self.language = config.llm.get('language', 'English')

    def _build_deep_reading_prompt(self, paper: ZoteroPaper, related_papers: list[ZoteroPaper]) -> tuple[str, str]:
        lang = self.language
        num_cards = self.config.daily_read.num_knowledge_cards
        num_questions = self.config.daily_read.num_thinking_questions
        related_titles = "\n".join([f"- {p.title}" for p in related_papers[:self.config.daily_read.num_related_papers]])

        latex_rule = (
            "所有数学公式必须使用标准 LaTeX 格式：行内公式用 \$...\$ "
            "（例如 \\rho = \\frac{1}{2}(S_0\\sigma_0 + S_1\\sigma_1)），"
            "独立公式用 \$\$...\$\$。"
            "不要使用 Unicode 上下标或其他非标准格式。"
        )

        if _is_chinese(lang):
            system_prompt = (
                "你是学术精读助手。请用中文输出，不要包含英文。"
                "你的任务是对用户 Zotero 中的一篇旧文献进行深度精读，帮助用户温故而知新。"
                "输出必须是严格的 JSON 格式，包含以下字段："
                "core_idea, background, methods, conclusions, limitations, knowledge_cards, thinking_questions, why_today, anki_deck。"
                "knowledge_cards 是一个数组，每个元素有 question 和 answer 字段，适合导入 Anki。"
                "thinking_questions 是一个字符串数组。"
                "anki_deck 是一个字符串，内容是可直接导入 Anki 的 CSV/TSV 格式（正面\\t背面\\n）。"
                + latex_rule +
                "只输出 JSON，不要前言或后缀。"
            )
            instruction = (
                f"请对以下论文进行深度精读。这篇论文于 {paper.added_date.strftime('%Y年%m月%d日')} 被加入 Zotero，"
                f"属于 {' / '.join(paper.paths)} 研究方向。\n"
                f"论文标题：{paper.title}\n"
                f"作者：{', '.join(paper.authors)}\n"
                f"摘要：{paper.abstract}\n"
            )
            if paper.full_text:
                instruction += f"\n论文正文节选：{paper.full_text[:5000]}\n"
            instruction += (
                f"\n与用户相关的其他论文：\n{related_titles}\n"
                f"\n请生成 {num_cards} 个知识点卡片和 {num_questions} 个思考题。"
            )
        else:
            latex_rule_en = (
                "All mathematical formulas must use standard LaTeX notation: inline with \$...\$ "
                "(e.g. \\rho = \\frac{1}{2}(S_0\\sigma_0 + S_1\\sigma_1)) and display with \$\$...\$\$. "
                "Do not use Unicode subscripts/superscripts or other non-standard formats."
            )
            system_prompt = (
                "You are an academic deep-reading assistant. "
                "Generate a structured deep-reading summary for one paper from the user's Zotero library. "
                "Output must be strict JSON with fields: core_idea, background, methods, conclusions, "
                "limitations, knowledge_cards, thinking_questions, why_today, anki_deck. "
                "knowledge_cards is an array of {question, answer} objects suitable for Anki. "
                "thinking_questions is an array of strings. "
                "anki_deck is a string of tab-separated front\\tback lines ready for Anki import. "
                + latex_rule_en +
                "Return only JSON."
            )
            instruction = (
                f"Deep-read the following paper. It was added to Zotero on {paper.added_date.strftime('%Y-%m-%d')} "
                f"and belongs to {' / '.join(paper.paths)}.\n"
                f"Title: {paper.title}\n"
                f"Authors: {', '.join(paper.authors)}\n"
                f"Abstract: {paper.abstract}\n"
            )
            if paper.full_text:
                instruction += f"\nExcerpt from full text: {paper.full_text[:5000]}\n"
            instruction += (
                f"\nRelated papers by the user:\n{related_titles}\n"
                f"\nGenerate {num_cards} knowledge cards and {num_questions} thinking questions."
            )

        return system_prompt, instruction

    def summarize(self, paper: ZoteroPaper, related_papers: list[ZoteroPaper]) -> ReadingSummary:
        system_prompt, instruction = self._build_deep_reading_prompt(paper, related_papers)

        enc = tiktoken.encoding_for_model("gpt-4o")
        tokens = enc.encode(instruction)
        instruction = enc.decode(tokens[:6000])

        generation_kwargs = dict(self.config.llm.get('generation_kwargs', {}))

        response = self.openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": instruction},
            ],
            response_format={"type": "json_object"},
            **generation_kwargs,
        )
        content = response.choices[0].message.content
        logger.info(f"[SUMMARY] generated for {paper.title}: {content[:200]}...")
        data = json.loads(content)

        summary = ReadingSummary(paper=paper)
        summary.core_idea = data.get("core_idea", "")
        summary.background = data.get("background", "")
        summary.methods = data.get("methods", "")
        summary.conclusions = data.get("conclusions", "")
        summary.limitations = data.get("limitations", "")
        summary.knowledge_cards = data.get("knowledge_cards", [])
        summary.thinking_questions = data.get("thinking_questions", [])
        summary.why_today = data.get("why_today", "")
        summary.anki_deck = data.get("anki_deck", "")

        summary.related_papers = [
            {"title": p.title, "url": p.url} for p in related_papers[:self.config.daily_read.num_related_papers]
        ]

        return summary
