from datetime import datetime
from typing import Optional
from pyzotero import zotero
from loguru import logger
from omegaconf import DictConfig
from ..protocol import ZoteroPaper
from ..utils import glob_match, normalize_path_patterns


class ZoteroRetriever:
    def __init__(self, config: DictConfig):
        self.config = config
        self.include_path_patterns = normalize_path_patterns(config.zotero.include_path, "include_path")
        self.ignore_path_patterns = normalize_path_patterns(config.zotero.ignore_path, "ignore_path")
        self.zot = zotero.Zotero(config.zotero.user_id, 'user', config.zotero.api_key)

    def _get_collection_path(self, collections: dict, col_key: str) -> str:
        name = collections[col_key]['data']['name']
        parent = collections[col_key]['data'].get('parentCollection')
        if parent:
            return self._get_collection_path(collections, parent) + '/' + name
        return name

    def fetch_corpus(self) -> list[ZoteroPaper]:
        logger.info("Fetching Zotero corpus")
        collections = self.zot.everything(self.zot.collections())
        collections = {c['key']: c for c in collections}

        items = self.zot.everything(self.zot.items(itemType='conferencePaper || journalArticle || preprint'))
        logger.info(f"Fetched {len(items)} Zotero items")

        corpus = []
        for item in items:
            data = item['data']
            title = data.get('title', 'Unknown Title')
            abstract = data.get('abstractNote', '')
            # Use abstract if available; otherwise fallback to title so empty-abstract papers still participate.
            if not abstract:
                abstract = title

            authors = []
            for creator in data.get('creators', []):
                if 'lastName' in creator and 'firstName' in creator:
                    authors.append(f"{creator['firstName']} {creator['lastName']}")
                elif 'name' in creator:
                    authors.append(creator['name'])
                elif 'lastName' in creator:
                    authors.append(creator['lastName'])

            paths = []
            for col_key in data.get('collections', []):
                if col_key in collections:
                    paths.append(self._get_collection_path(collections, col_key))

            url = data.get('url', '')
            doi = data.get('DOI', '')
            if not url and doi:
                url = f"https://doi.org/{doi}"

            pdf_url = None
            # Find child attachments to get PDF link
            try:
                children = self.zot.children(item['key'])
                for child in children:
                    if child['data'].get('itemType') == 'attachment':
                        mime = child['data'].get('contentType', '')
                        if 'pdf' in mime.lower():
                            pdf_url = child['data'].get('url', '')
                            if not pdf_url:
                                pdf_url = f"https://www.zotero.org/users/{self.config.zotero.user_id}/items/{child['key']}"
                            break
            except Exception as e:
                logger.debug(f"Failed to get children for {title}: {e}")

            added_date = datetime.strptime(data.get('dateAdded', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')), '%Y-%m-%dT%H:%M:%SZ')
            tags = [t['tag'] for t in data.get('tags', [])]

            corpus.append(ZoteroPaper(
                key=item['key'],
                item_key=item['key'],
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                added_date=added_date,
                paths=paths,
                tags=tags,
                doi=doi,
            ))

        corpus = self._filter_by_path(corpus)
        logger.info(f"Selected {len(corpus)} papers after path filtering")
        return corpus

    def _filter_by_path(self, corpus: list[ZoteroPaper]) -> list[ZoteroPaper]:
        if self.include_path_patterns:
            logger.info(f"Selecting papers matching include_path: {self.include_path_patterns}")
            corpus = [
                c for c in corpus
                if any(glob_match(path, pattern) for path in c.paths for pattern in self.include_path_patterns)
            ]
        if self.ignore_path_patterns:
            logger.info(f"Excluding papers matching ignore_path: {self.ignore_path_patterns}")
            corpus = [
                c for c in corpus
                if not any(glob_match(path, pattern) for path in c.paths for pattern in self.ignore_path_patterns)
            ]
        return corpus

    def add_tag(self, item_key: str, tag: str):
        try:
            # pyzotero add_tags expects the full item dict in newer versions
            item = self.zot.item(item_key)
            self.zot.add_tags(item, tag)
            logger.info(f"Added tag '{tag}' to item {item_key}")
        except Exception as e:
            logger.warning(f"Failed to add tag '{tag}' to item {item_key}: {e}")

    def get_item_pdf_text(self, item_key: str) -> Optional[str]:
        """Try to download and extract text from the first PDF attachment of an item."""
        try:
            children = self.zot.children(item_key)
            for child in children:
                if child['data'].get('itemType') == 'attachment':
                    mime = child['data'].get('contentType', '')
                    if 'pdf' in mime.lower():
                        key = child['key']
                        logger.info(f"Downloading PDF for item {item_key} attachment {key}")
                        import requests, tempfile, pymupdf4llm
                        r = requests.get(
                            f"https://api.zotero.org/users/{self.config.zotero.user_id}/items/{key}/file/view?key={self.config.zotero.api_key}",
                            timeout=60,
                        )
                        if r.status_code != 200:
                            logger.warning(f"Failed to download PDF: {r.status_code}")
                            return None
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                            f.write(r.content)
                            tmp_path = f.name
                        text = pymupdf4llm.to_markdown(tmp_path)
                        os.unlink(tmp_path)
                        return text[:15000]
        except Exception as e:
            logger.warning(f"Failed to extract PDF text for {item_key}: {e}")
        return None
