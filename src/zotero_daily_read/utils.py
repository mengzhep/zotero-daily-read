import os
import re
import glob
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from datetime import datetime
from omegaconf import DictConfig, ListConfig
from loguru import logger
import fnmatch

def _is_chinese(language: str | None) -> bool:
    if language is None:
        return False
    return language.strip().lower() in {"chinese", "zh", "中文", "简体中文", "繁体中文"}


def normalize_path_patterns(patterns: list[str] | ListConfig | None, config_key: str) -> list[str] | None:
    if patterns is None:
        return None
    if not isinstance(patterns, (list, ListConfig)):
        raise TypeError(
            f"config.zotero.{config_key} must be a list of glob patterns or null, "
            'for example ["研究生/**"]. Single strings are not supported.'
        )
    if any(not isinstance(pattern, str) for pattern in patterns):
        raise TypeError(f"config.zotero.{config_key} must contain only glob pattern strings.")
    return list(patterns)


def glob_match(path: str, pattern: str) -> bool:
    # Python 3.12 compatible glob matching supporting '**'
    if '**' not in pattern:
        return fnmatch.fnmatch(path, pattern)
    # Handle '**' recursive patterns
    if pattern.endswith('/**'):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + '/')
    if pattern.startswith('**/'):
        suffix = pattern[3:]
        return path == suffix or path.endswith('/' + suffix) or ('/' + suffix) in path
    if '/**/' in pattern:
        prefix, suffix = pattern.split('/**/', 1)
        return path.startswith(prefix + '/') and (path.endswith('/' + suffix) or ('/' + suffix + '/') in path or path == prefix + '/' + suffix)
    return fnmatch.fnmatch(path, pattern)


def send_email(config: DictConfig, html: str):
    sender = config.email.sender
    receiver = config.email.receiver
    password = config.email.sender_password
    smtp_server = config.email.smtp_server
    smtp_port = config.email.smtp_port

    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = _format_addr(f'Zotero Daily Read <{sender}>')
    msg['To'] = _format_addr(f'You <{receiver}>')
    today = datetime.now().strftime('%Y/%m/%d')
    msg['Subject'] = Header(f'每日精读 {today}', 'utf-8').encode()

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        logger.info("Email sent successfully via SSL")
    except Exception as e:
        logger.warning(f"Failed to use SSL: {e}\nTry to use TLS.")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
      