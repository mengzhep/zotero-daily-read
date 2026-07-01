from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ZoteroPaper:
    key: str
    item_key: str
    title: str
    authors: list[str]
    abstract: str
    url: str
    pdf_url: Optional[str] = None
    full_text: Optional[str] = None
    added_date: datetime = field(default_factory=datetime.utcnow)
    paths: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    doi: Optional[str] = None


@dataclass
class ReadingSummary:
    paper: ZoteroPaper
    core_idea: str = ""
    background: str = ""
    methods: str = ""
    conclusions: str = ""
    limitations: str = ""
    knowledge_cards: list[dict] = field(default_factory=list)
    thinking_questions: list[str] = field(default_factory=list)
    related_papers: list[dict] = field(default_factory=list)
    why_today: str = ""
    anki_deck: str = ""
