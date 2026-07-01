import random
import math
from datetime import datetime, timedelta
from loguru import logger
from .protocol import ZoteroPaper
from .utils import load_review_log, save_review_log


class PaperSelector:
    def __init__(self, config):
        self.config = config
        self.log_path = config.daily_read.review_log_path
        self.mode = config.daily_read.mode
        self.max_history_days = config.daily_read.max_history_days

    def _load_log(self) -> dict:
        return load_review_log(self.log_path)

    def _save_log(self, log: dict):
        save_review_log(self.log_path, log)

    def _last_review_date(self, log: dict, item_key: str) -> datetime | None:
        for review in reversed(log.get("reviews", [])):
            if review.get("item_key") == item_key:
                return datetime.strptime(review["date"], "%Y-%m-%d")
        return None

    def _compute_weights(self, corpus: list[ZoteroPaper], log: dict) -> list[float]:
        now = datetime.now()
        cutoff = now - timedelta(days=self.max_history_days)
        weights = []
        for paper in corpus:
            last_review = self._last_review_date(log, paper.item_key)
            age_days = (now - paper.added_date).days

            # Base weight: older papers get higher weight
            base_weight = 1.0 + math.log1p(max(age_days, 0))

            # Review penalty: recently reviewed papers get much lower weight
            if last_review is None:
                review_factor = 3.0  # Never reviewed: highly preferred
            elif last_review < cutoff:
                review_factor = 2.0  # Reviewed but long ago
            else:
                days_since_review = (now - last_review).days
                review_factor = max(0.1, days_since_review / self.max_history_days)

            weights.append(base_weight * review_factor)
        return weights

    def select(self, corpus: list[ZoteroPaper]) -> ZoteroPaper:
        if not corpus:
            raise ValueError("No papers available for selection")

        log = self._load_log()

        if self.mode == "oldest_first":
            paper = min(corpus, key=lambda p: p.added_date)
        elif self.mode == "random":
            paper = random.choice(corpus)
        else:  # weighted_random
            weights = self._compute_weights(corpus, log)
            paper = random.choices(corpus, weights=weights, k=1)[0]

        logger.info(f"Selected paper for daily read: {paper.title}")
        return paper

    def record_review(self, paper: ZoteroPaper):
        log = self._load_log()
        log["reviews"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "item_key": paper.item_key,
            "title": paper.title,
            "url": paper.url,
        })
        # Keep only last 365 reviews
        log["reviews"] = log["reviews"][-365:]
        self._save_log(log)
        logger.info(f"Recorded review of {paper.title} in {self.log_path}")
