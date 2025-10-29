# ui/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.urls import reverse
import os

User = get_user_model()


# ---------- Asosiy kataloglar ----------
class Instructor(models.Model):
    full_name = models.CharField(max_length=120)
    title = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to="instructors/", blank=True, null=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    class Meta:
        ordering = ("full_name",)

    def __str__(self):
        return self.full_name

    @property
    def facebook_url(self):
            return self.facebook or ""

    @property
    def twitter_url(self):
        return self.twitter or ""

    @property
    def instagram_url(self):
        return self.instagram or ""

class Testimonial(models.Model):
    full_name    = models.CharField(max_length=120)
    role         = models.CharField(max_length=120, blank=True)
    quote        = models.TextField()
    photo        = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    rating       = models.PositiveIntegerField(default=5,
                    validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_published = models.BooleanField(default=False)
    order        = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order", "id")
        indexes = [models.Index(fields=["is_published", "order"])]

    def __str__(self):
        return self.full_name

    # Templatega mos aliaslar:
    @property
    def profession(self) -> str:
        return self.role or ""

    @property
    def text(self) -> str:
        return self.quote or ""


class Category(models.Model):
    name  = models.CharField(max_length=120, unique=True)
    slug  = models.SlugField(max_length=140, unique=True, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    class Meta:
        ordering = ("name",)
        indexes = [models.Index(fields=["slug"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name or "")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('courses')}?category={self.slug}"


class Course(models.Model):
    category        = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="courses")
    instructor      = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, related_name="courses")
    title           = models.CharField(max_length=200)
    slug            = models.SlugField(max_length=240, unique=True, blank=True)
    short_desc      = models.TextField(blank=True)
    image           = models.ImageField(upload_to="courses/", blank=True, null=True)
    price           = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    rating          = models.FloatField(default=0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    duration_hours  = models.PositiveIntegerField(default=0)
    students_count  = models.PositiveIntegerField(default=0)
    is_featured     = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "title")
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_featured"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title or "")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})

    # Template eski nomni so‘raydi — migratsiyasiz muvofiqlik:
    @property
    def duration_minutes(self) -> int:
        try:
            return int((self.duration_hours or 0) * 60)
        except Exception:
            return 0


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title  = models.CharField(max_length=200)
    order  = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ("order", "id")
        unique_together = ("course", "order")
        indexes = [models.Index(fields=["course", "order"])]

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class HomepageSlide(models.Model):
    title              = models.CharField(max_length=150)
    subtitle           = models.CharField(max_length=150, blank=True)
    description        = models.TextField(blank=True)
    image              = models.ImageField(upload_to="slides/")
    cta_primary_text   = models.CharField(max_length=40, blank=True, default="Batafsil")
    cta_primary_url    = models.CharField(max_length=200, blank=True, default="#")
    cta_secondary_text = models.CharField(max_length=40, blank=True, default="Hoziroq qo‘shiling")
    cta_secondary_url  = models.CharField(max_length=200, blank=True, default="#")
    is_active          = models.BooleanField(default=True)
    order              = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ("order", "id")
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return self.title


# ---------- Dars (video/text/pdf/doc/test) ----------
class Lesson(models.Model):
    KIND_CHOICES = (
        ("video", "Video"),
        ("text",  "Text / Lecture"),
        ("pdf",   "PDF"),
        ("doc",   "Word (DOC/DOCX)"),
        ("test",  "Test"),
    )

    section         = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="lessons")
    order           = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])
    kind            = models.CharField(max_length=10, choices=KIND_CHOICES, default="video")
    title           = models.CharField(max_length=220)

    # text
    text            = models.TextField(blank=True)

    # video
    video_url       = models.URLField(blank=True)
    video_file      = models.FileField(upload_to="videos/", blank=True, null=True)

    # docs
    document_file   = models.FileField(upload_to="docs/", blank=True, null=True)

    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")
        unique_together = ("section", "order")
        indexes = [models.Index(fields=["section", "order"])]

    def __str__(self):
        return self.title

    def clean(self):
        if self.kind == "video" and not (self.video_url or self.video_file):
            raise ValidationError("Video darsi uchun YouTube link yoki video fayl kerak.")

        if self.kind == "text" and not self.text:
            raise ValidationError("Text darsi uchun matn kiriting.")

        if self.kind == "pdf":
            if not self.document_file:
                raise ValidationError("PDF darsi uchun fayl kerak.")
            ext = os.path.splitext(self.document_file.name)[1].lower()
            if ext != ".pdf":
                raise ValidationError("PDF darsi uchun faqat .pdf yuklang.")

        if self.kind == "doc":
            if not self.document_file:
                raise ValidationError("DOC/DOCX darsi uchun fayl kerak.")
            ext = os.path.splitext(self.document_file.name)[1].lower()
            if ext not in [".doc", ".docx"]:
                raise ValidationError("DOC darsi uchun faqat .doc yoki .docx yuklang.")


# ---------- Test (Quiz) ----------
class Quiz(models.Model):
    lesson            = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='test')
    title             = models.CharField(max_length=200, blank=True)
    time_limit_seconds= models.PositiveIntegerField(default=0, help_text="0 = cheksiz vaqt")
    pass_percent      = models.PositiveIntegerField(default=0, help_text="0 = pass talabi yo‘q")
    attempts_limit    = models.PositiveIntegerField(default=0, help_text="0 = cheksiz urinish")

    # Admin nazorati + random
    limit_questions   = models.PositiveIntegerField(null=True, blank=True,
                           help_text="Nechta savol berilsin (bo‘sh – hammasi).")
    shuffle_questions = models.BooleanField(default=True)
    shuffle_choices   = models.BooleanField(default=True)

    # Maslahat chegaralari
    advice_mid_min    = models.PositiveSmallIntegerField(default=50)
    advice_high_min   = models.PositiveSmallIntegerField(default=80)
    advice_low        = models.TextField(blank=True, default=(
                          "Natijangiz past. Darsni qayta ko‘rib chiqing, qisqa konspekt tuzing va ko‘proq amaliy mashq bajaring."
                       ))
    advice_mid        = models.TextField(blank=True, default=(
                          "Yaxshi! Endi murakkabroq misollarni bajaring va qo‘shimcha vazifalar bilan mustahkamlang."
                       ))
    advice_high       = models.TextField(blank=True, default=(
                          "A’lo! Keyingi modulga o‘ting va chuqurlashtirilgan topshiriqlarni sinab ko‘ring."
                       ))

    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        ordering = ("lesson",)

    def __str__(self):
        return self.title or f"Test for: {self.lesson.title}"

    def get_advice(self, percent: float) -> str:
        if percent >= self.advice_high_min:
            return self.advice_high
        if percent >= self.advice_mid_min:
            return self.advice_mid
        return self.advice_low


class Question(models.Model):
    TYPE_CHOICES = (
        ("sc", "Single choice"),
        ("mc", "Multiple choice"),
        ("txt", "Text (manual grade)"),
    )
    quiz        = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    order       = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])
    text        = models.TextField()
    qtype       = models.CharField(max_length=3, choices=TYPE_CHOICES, default="sc")
    points      = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])
    image       = models.ImageField(upload_to="quiz/", blank=True, null=True)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ("order", "id")
        unique_together = ("quiz", "order")
        indexes = [models.Index(fields=["quiz", "order"])]

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class Choice(models.Model):
    question   = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text       = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


# ---------- Urinishlar (admin analitika & eksport) ----------
class QuizAttempt(models.Model):
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    lesson        = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz          = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    created_at    = models.DateTimeField(auto_now_add=True)
    finished_at   = models.DateTimeField(null=True, blank=True)

    points_total  = models.FloatField(default=0)
    points_gained = models.FloatField(default=0)
    percent       = models.FloatField(default=0)

    # Qaysi savollar berilgani va foydalanuvchi tanlovlari
    question_ids  = models.JSONField(default=list, blank=True)
    answers_json  = models.JSONField(default=dict, blank=True)

    # Viewda ko‘rsatilgan maslahatni saqlaymiz (views.py POST da yuborilasiz):
    advice_shown  = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user} – {self.quiz} – {self.percent}%"


# ui/models.py — TORRENS MODELLARI (to‘liq blokni almashtiring)



# ---------- Torrens (ijodkorlik) ----------
class TorrensTest(models.Model):
    title              = models.CharField(max_length=200)
    slug               = models.SlugField(max_length=220, unique=True, blank=True)
    description        = models.TextField(blank=True)
    is_published       = models.BooleanField(default=False)
    time_limit_minutes = models.PositiveIntegerField(default=0, help_text="0 = cheklanmagan")
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes  = [
            models.Index(fields=["slug"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title or "")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("torrens_detail", kwargs={"slug": self.slug})


class TorrensTask(models.Model):
    RESP_CHOICES = (
        ("text",    "Matn yozish"),
        ("list",    "G'oyalar ro'yxati"),
        ("drawing", "Rasm/chizma"),
    )
    test            = models.ForeignKey(TorrensTest, on_delete=models.CASCADE, related_name="tasks")
    order           = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])
    prompt          = models.TextField(help_text="Topshiriq matni (ko'rsatma)")
    response_type   = models.CharField(max_length=20, choices=RESP_CHOICES, default="text")
    hint            = models.TextField(blank=True)
    reference_image = models.ImageField(upload_to="torrens/ref/", blank=True, null=True)

    # 🆕 Kombinatsion javoblar konfiguratsiyasi
    allow_text      = models.BooleanField(default=True)     # matn javobiga ruxsat
    allow_images    = models.BooleanField(default=True)     # ko‘p rasm javobiga ruxsat
    max_images      = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(0)])

    class Meta:
        ordering         = ("order", "id")
        unique_together  = ("test", "order")
        indexes          = [models.Index(fields=["test", "order"])]

    def __str__(self):
        return f"{self.test.title} — #{self.order}"


# 🆕 Topshiriqqa biriktiriladigan ko‘p rasm (ko‘rsatma/namuna sifatida)
class TorrensTaskImage(models.Model):
    task    = models.ForeignKey(TorrensTask, on_delete=models.CASCADE, related_name="extra_images")
    image   = models.ImageField(upload_to="torrens/task_images/")
    caption = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Torrens topshiriq rasmi"
        verbose_name_plural = "Torrens topshiriq rasmlari"

    def __str__(self):
        return f"Task#{self.task_id} image"


class TorrensSubmission(models.Model):
    STATUS = (
        ("draft",    "Jarayonda"),
        ("finished", "Yakunlangan"),
        ("graded",   "Baholangan"),
    )
    test        = models.ForeignKey(TorrensTest, on_delete=models.CASCADE, related_name="submissions")
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="torrens_submissions")
    started_at  = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    total_score = models.FloatField(default=0)
    status      = models.CharField(max_length=10, choices=STATUS, default="draft")

    class Meta:
        ordering        = ("-started_at",)
        # finished_at NULL bo‘lsa, ko‘p draft bo‘lishi mumkin — bu mantiqan to‘g‘ri.
        unique_together = ("test", "user", "finished_at")
        indexes         = [models.Index(fields=["test", "user", "-started_at"])]

    def __str__(self):
        return f"{self.user} — {self.test} — {self.status}"


class TorrensAnswer(models.Model):
    submission    = models.ForeignKey(TorrensSubmission, on_delete=models.CASCADE, related_name="answers")
    task          = models.ForeignKey(TorrensTask, on_delete=models.CASCADE, related_name="answers")

    # Mavjud javob turlari (saqlab qolindi)
    text_answer   = models.TextField(blank=True)
    list_answer   = models.JSONField(blank=True, null=True)
    drawing_image = models.ImageField(upload_to="torrens/ans/", blank=True, null=True)

    score         = models.FloatField(default=0)
    note          = models.TextField(blank=True)

    class Meta:
        unique_together = ("submission", "task")
        indexes         = [models.Index(fields=["submission", "task"])]

    def __str__(self):
        return f"Ans: {self.submission} / task#{self.task.order}"


# 🆕 Talaba javobiga biriktiriladigan ko‘p rasm (0..N ta)
class TorrensAnswerImage(models.Model):
    answer  = models.ForeignKey(TorrensAnswer, on_delete=models.CASCADE, related_name="images")
    image   = models.ImageField(upload_to="torrens/ans_images/")
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Ans#{self.answer_id} image"



# ---------- Kutubxona ----------
class LibraryItem(models.Model):
    STANDARD_CHOICES = (("DC", "Dublin Core"), ("MARC21", "MARC 21"))

    standard   = models.CharField(max_length=10, choices=STANDARD_CHOICES, default="DC")
    title      = models.CharField(max_length=500)

    file       = models.FileField(upload_to="library/", blank=True, null=True)
    link       = models.URLField(blank=True)
    thumb      = models.ImageField(upload_to="library/thumbs/", blank=True, null=True)

    dc_creator = models.CharField(max_length=500, blank=True)
    dc_date    = models.CharField(max_length=50, blank=True)
    dc_format  = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at", "is_published"])]

    def __str__(self):
        return self.title

    def clean(self):
        if not self.file and not self.link:
            raise ValidationError("Hech bo‘lmasa fayl yoki havola kiriting.")

    @property
    def display_creator(self):
        return self.dc_creator

    @property
    def display_year(self) -> str:
        return (self.dc_date or "").split("-")[0]

    @property
    def href(self) -> str:
        return self.file.url if self.file else (self.link or "#")
