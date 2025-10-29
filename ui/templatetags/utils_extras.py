# ui/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter(name="dict_get")
def dict_get(d, key):
    """
    Shablonlarda dictionary ichidan kalit orqali qiymat olish uchun filter.
    Foydalanish:
        {{ my_dict|dict_get:"kalit" }}
    """
    if not isinstance(d, dict):
        return None
    try:
        return d.get(key)
    except Exception:
        return None
