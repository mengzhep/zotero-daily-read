from loguru import logger
from omegaconf import DictConfig
from .retriever import ZoteroRetriever
from .selector import PaperSelector
from .summarizer import Summarizer
from .construct_email import render_email
from .utils import send_email
from datetime import datetime


class Executor:
    def __init__(self, config: DictConfig):
        self.config = config
        self.retriever = ZoteroRetriever(config)
        self.selector = PaperSelector(config)
        self.summarizer = Summarizer(config)

    def _find_related_papers(self, corpus, selected_paper):
        """Simple related paper finder: same collection and different item."""
        related = []
        for p in corpus:
            if p.item_key == selected_paper.item_key:
                continue
            if set(p.paths) & set(selected_paper.paths):
                related.append(p)
        # Fallback: if no same-collection papers, return random others
        if not related:
            related = [p for p in corpus if p.item_key != selected_paper.item_key]
        # Prefer older papers
        related = sorted(related, key=lambda p: p.added_date)
        return related[:self.config.daily_read.num_related_papers]

    def run(self):
        corpus = self.retriever.fetch_corpus()
        if not corpus:
            logger.error("No Zotero papers found. Please check your zotero settings.")
            return

        paper = self.selector.select(corpus)

        # Optionally fetch full text for deeper reading
        if not paper.abstract or paper.abstract == paper.title:
            logger.info(f"No abstract for {paper.title}, trying to fetch PDF text...")
            paper.full_text = self.retriever.get_item_pdf_text(paper.item_key)

        related = self._find_related_papers(corpus, paper)

        logger.info("Generating deep reading summary...")
        summary = self.summarizer.summarize(paper, related)

        logger.info("Sending email...")
        html = render_email(summary, self.config.llm.get("language", "English"))
        send_email(self.config, html)
        logger.info("Email sent successfully")

        # Record review and add Zotero tag
        self.selector.record_review(paper)
        tag = f"{self.config.daily_read.zotero_tag_prefix}-{datetime.now().strftime('%Y-%m-%d')}"
        self.retriever.add_tag(paper.item_key, tag)
