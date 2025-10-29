# ui/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from .models import TorrensTest, TorrensTask, Testimonial


# ---------- Bootstrap integratsiyalangan login forma ----------
class BootstrapAuthForm(AuthenticationForm):
    """Login formasi: Bootstrap klasslarini avtomatik qo‘shadi."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css_class} form-control".strip()
            field.widget.attrs.setdefault("placeholder", field.label)
            # foydali autocomplete
            if name == "username":
                field.widget.attrs.setdefault("autocomplete", "username")
            elif name == "password":
                field.widget.attrs.setdefault("autocomplete", "current-password")


# ---------- Torrens test va topshiriqlari ----------
class TorrensTestForm(forms.ModelForm):
    class Meta:
        model = TorrensTest
        fields = ("title", "description", "is_published", "time_limit_minutes")
        labels = {
            "title": "Test sarlavhasi",
            "description": "Qisqacha tavsif",
            "is_published": "Nashr etilsin",
            "time_limit_minutes": "Vaqt limiti (daq.)",
        }
        help_texts = {
            "time_limit_minutes": "0 — cheklanmagan.",
        }
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": 'Masalan, "Ijodiy fikrlash testi"',
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Test haqida qisqacha ma’lumot",
            }),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "time_limit_minutes": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "placeholder": "Masalan: 30 (0 — cheklanmagan)",
            }),
        }

    def clean_time_limit_minutes(self):
        v = self.cleaned_data.get("time_limit_minutes") or 0
        if v < 0 or v > 24 * 60:
            raise ValidationError("Vaqt limiti 0–1440 oraliqda bo‘lishi kerak.")
        return v


class TorrensTaskForm(forms.ModelForm):
    class Meta:
        model = TorrensTask
        fields = ("order", "prompt", "response_type", "hint", "reference_image")
        labels = {
            "order": "Tartib raqami",
            "prompt": "Topshiriq matni (ko‘rsatma)",
            "response_type": "Javob turi",
            "hint": "Izoh (ixtiyoriy)",
            "reference_image": "Namunaviy rasm (ixtiyoriy)",
        }
        widgets = {
            "order": forms.NumberInput(attrs={
                "class": "form-control", "min": 1,
                "placeholder": "Topshiriq tartib raqami"
            }),
            "prompt": forms.Textarea(attrs={
                "class": "form-control", "rows": 3,
                "placeholder": "Topshiriq matni (ko‘rsatma)"
            }),
            "response_type": forms.Select(attrs={"class": "form-select"}),
            "hint": forms.Textarea(attrs={
                "class": "form-control", "rows": 2,
                "placeholder": "Izoh yoki yordamchi ko‘rsatma (ixtiyoriy)"
            }),
            "reference_image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
        }

    def clean_order(self):
        order = self.cleaned_data.get("order") or 1
        if order < 1 or order > 1000:
            raise ValidationError("Tartib 1–1000 oralig‘ida bo‘lishi kerak.")
        return order

    def clean_prompt(self):
        txt = (self.cleaned_data.get("prompt") or "").strip()
        if len(txt) < 5:
            raise ValidationError("Topshiriq matni juda qisqa.")
        return txt


# ---------- Fikrlar (Testimonial) formasi ----------
class TestimonialForm(forms.ModelForm):
    """Foydalanuvchi fikrini (testimonial) yuborish uchun forma."""
    class Meta:
        model = Testimonial
        fields = ["full_name", "role", "quote", "photo", "rating"]
        labels = {
            "full_name": "Ism Familiya",
            "role": "Lavozim/Rol",
            "quote": "Fikr (testimonial)",
            "photo": "Rasm (ixtiyoriy)",
            "rating": "Reyting (1–5)",
        }
        help_texts = {
            "role": "Masalan: TATU talabasi, Frontend o‘qituvchisi va h.k.",
            "rating": "1 — minimal, 5 — maksimal baho.",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ism Familiya",
            }),
            "role": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Masalan: TATU talabasi, Frontend o‘qituvchisi...",
            }),
            "quote": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Fikringizni yozing...",
            }),
            "photo": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "rating": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "max": 5,
                "placeholder": "1 dan 5 gacha baho bering",
            }),
        }

    def clean_rating(self):
        r = self.cleaned_data.get("rating")
        # Modelda max cheklov yo‘q, form bilan qat’iylaymiz.
        if r is None:
            raise ValidationError("Reyting kiritilishi shart.")
        if not (1 <= int(r) <= 5):
            raise ValidationError("Reyting 1–5 oraliqda bo‘lishi kerak.")
        return int(r)

    def clean_photo(self):
        img = self.cleaned_data.get("photo")
        if not img:
            return img
        # ixtiyoriy: rasm hajmi va piksel o‘lchamini tekshirish
        max_mb = 5
        if img.size > max_mb * 1024 * 1024:
            raise ValidationError(f"Rasm hajmi {max_mb} MB dan kichik bo‘lishi kerak.")
        try:
            w, h = get_image_dimensions(img)
            if w < 100 or h < 100:
                raise ValidationError("Rasm o‘lchami juda kichik (kamida 100x100).")
        except Exception:
            # Agar Pillow o‘qiy olmasa
            raise ValidationError("Yaroqsiz rasm fayli.")
        return img
