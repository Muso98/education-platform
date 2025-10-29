# ui/templatetags/media_extras.py
import re
import logging
from urllib.parse import urlparse, parse_qs, quote
from django import template

register = template.Library()
logger = logging.getLogger(__name__)

# — Regexlar —
_YT_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')   # YouTube video ID — harf/raqam/_/-
_VIMEO_ID_RE = re.compile(r'^\d+$')               # Vimeo video ID — raqamlar


# ============================================================
# Helper funksiyalar
# ============================================================
def _extract_youtube_id(url: str) -> str:
    """YouTube havolalaridan video ID ni aniqlaydi (watch?v=, youtu.be, embed, shorts)."""
    if not url:
        return ''
    try:
        u = urlparse(url)
        host = (u.hostname or '').lower()
        path = (u.path or '').strip('/')

        # youtu.be/<id>
        if host == "youtu.be":
            cand = path.split('/')[0]
            return cand if _YT_ID_RE.match(cand) else ''

        # youtube.com/watch?v=<id>
        if host.endswith("youtube.com"):
            qs = parse_qs(u.query or '')
            if "v" in qs:
                cand = qs["v"][0]
                return cand if _YT_ID_RE.match(cand) else ''

            # youtube.com/embed/<id> yoki /shorts/<id>
            parts = path.split('/')
            if len(parts) >= 2 and parts[0] in {"embed", "shorts"}:
                cand = parts[1]
                return cand if _YT_ID_RE.match(cand) else ''
    except Exception as e:
        logger.debug(f"❌ YouTube ID ajratishda xato: {e}")
    return ''


def _extract_vimeo_id(url: str) -> str:
    """Vimeo havolalaridan video ID ni aniqlaydi (video/<id> yoki to‘g‘ridan /<id>)."""
    if not url:
        return ''
    try:
        u = urlparse(url)
        host = (u.hostname or '').lower()
        path = (u.path or '').strip('/')

        if "vimeo.com" in host:
            parts = [p for p in path.split('/') if p]
            if parts:
                cand = parts[-1]
                if _VIMEO_ID_RE.match(cand):
                    return cand
    except Exception as e:
        logger.debug(f"❌ Vimeo ID ajratishda xato: {e}")
    return ''


# ============================================================
# Django Template Filtrlari
# ============================================================

@register.filter
def is_mp4(url: str) -> bool:
    """URL .mp4 bilan tugasa True qaytaradi."""
    if not url:
        return False
    u = url.split('?', 1)[0].split('#', 1)[0].lower()
    return u.endswith('.mp4')


@register.filter
def youtube_id(url: str) -> str:
    """YouTube video ID ni qaytaradi (topilmasa bo‘sh satr)."""
    return _extract_youtube_id(url)


@register.filter
def is_youtube(url: str) -> bool:
    """Berilgan URL YouTube havolasimi?"""
    return bool(_extract_youtube_id(url))


@register.filter
def youtube_embed(url: str) -> str:
    """YouTube uchun xavfsiz iframe embed URL yaratadi."""
    vid = _extract_youtube_id(url)
    if not vid:
        return ''
    return (
        f"https://www.youtube-nocookie.com/embed/{vid}"
        f"?rel=0&modestbranding=1&playsinline=1"
    )


@register.filter
def is_vimeo(url: str) -> bool:
    """Berilgan URL Vimeo havolasimi?"""
    return bool(_extract_vimeo_id(url))


@register.filter
def vimeo_embed(url: str) -> str:
    """Vimeo uchun minimal interfeysli iframe URL yaratadi."""
    vid = _extract_vimeo_id(url)
    if not vid:
        return ''
    return f"https://player.vimeo.com/video/{quote(vid, safe='')}?byline=0&portrait=0&title=0"
