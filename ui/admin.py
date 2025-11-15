# ui/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
import csv

from .models import (
    # Asosiy
    Category,
    Instructor,
    Course,
    Section,
    Lesson,
    # Quiz
    Quiz,
    Question,
    Choice,
    QuizAttempt,
    # Torrens
    TorrensTest,
    TorrensTask,
    TorrensSubmission,
    TorrensAnswer,
    # Boshqa
    LibraryItem,
    HomepageSlide,
    Testimonial,
)

# --- Torrens ko‘p rasmli modellari ixtiyoriy (mavjud bo‘lmasa xato bermasin) ---
_HAS_MULTI_IMAGES = True
try:
    from .models import TorrensTaskImage, TorrensAnswerImage
except Exception:
    _HAS_MULTI_IMAGES = False


# ==========================
# KATEGORIYA / INSTRUKTOR / KURS
# ==========================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    fields = ("name", "slug", "image")
    list_per_page = 25


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("thumb", "full_name", "title")
    search_fields = ("full_name", "title")
    list_per_page = 25

    @admin.display(description="Foto")
    def thumb(self, obj):
        if getattr(obj, "photo", None):
            return format_html(
                '<img src="{}" style="height:40px;border-radius:6px" />',
                obj.photo.url,
            )
        return "—"


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = (
        "order",
        "kind",
        "title",
        "video_url",
        "video_file",
        "document_file",
        "duration_minutes",
    )
    show_change_link = True


class SectionInline(admin.StackedInline):
    model = Section
    extra = 0
    fields = ("title", "order")
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "cover",
        "title",
        "category",
        "instructor",
        "price",
        "is_featured",
        "created_at",
    )
    list_filter = ("category", "is_featured")
    search_fields = ("title", "instructor__full_name")
    prepopulated_fields = {"slug": ("title",)}
    fields = (
        "category",
        "instructor",
        "title",
        "slug",
        "short_desc",
        "image",
        "price",
        "rating",
        "duration_hours",
        "students_count",
        "is_featured",
        "created_at",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("category", "instructor")
    inlines = [SectionInline]
    date_hierarchy = "created_at"
    list_editable = ("is_featured",)
    list_per_page = 25

    @admin.display(description="Muqova")
    def cover(self, obj):
        if getattr(obj, "image", None):
            return format_html(
                '<img src="{}" style="height:36px;border-radius:6px" />',
                obj.image.url,
            )
        return "—"


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    autocomplete_fields = ("course",)
    inlines = [LessonInline]
    list_editable = ("order",)
    list_per_page = 25


# ==========================
# QUIZ (TEST)
# ==========================

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    fields = ("text", "is_correct")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "text_short",
        "quiz",
        "qtype",
        "points",
        "order",
        "choices_count",
    )
    list_filter = ("qtype", "quiz")
    search_fields = ("text",)
    inlines = [ChoiceInline]
    list_editable = ("order", "points")
    list_per_page = 25

    @admin.display(description="Question")
    def text_short(self, obj):
        return (obj.text[:70] + "…") if len(obj.text) > 70 else obj.text

    @admin.display(description="Choices")
    def choices_count(self, obj):
        return obj.choices.count()


class QuestionInline(admin.StackedInline):
    """
    Quiz sahifasida savollarni ko‘rsatish (Choice’lar esa Question sahifasida).
    """
    model = Question
    extra = 0
    fields = ("order", "text", "qtype", "points", "image", "explanation")
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "lesson_link",
        "num_questions",
        "limit_questions",
        "shuffle_questions",
        "shuffle_choices",
        "pass_percent",
        "time_limit_seconds",
        "attempts_limit",
    )
    list_editable = (
        "limit_questions",
        "shuffle_questions",
        "shuffle_choices",
        "pass_percent",
    )
    search_fields = ("title", "lesson__title")
    inlines = [QuestionInline]
    list_per_page = 25

    @admin.display(description="Lesson")
    def lesson_link(self, obj):
        if not obj.lesson_id:
            return "—"
        url = reverse("admin:ui_lesson_change", args=[obj.lesson_id])
        return format_html('<a href="{}">{}</a>', url, obj.lesson.title)

    @admin.display(description="Questions")
    def num_questions(self, obj):
        return obj.questions.count()


class QuizInline(admin.StackedInline):
    """
    OneToOne(Lesson) — dars sahifasida test sozlamalari.
    """
    model = Quiz
    extra = 0
    max_num = 1
    can_delete = True
    fields = (
        "title",
        "pass_percent",
        "time_limit_seconds",
        "attempts_limit",
        "limit_questions",
        "shuffle_questions",
        "shuffle_choices",
        "advice_low",
        "advice_mid",
        "advice_high",
        "advice_mid_min",
        "advice_high_min",
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "section",
        "kind",
        "order",
        "duration_minutes",
        "has_quiz",
        "manage_quiz",
    )
    list_filter = ("kind", "section__course")
    search_fields = ("title", "section__title", "section__course__title")
    autocomplete_fields = ("section",)
    inlines = [QuizInline]
    list_editable = ("order",)
    list_per_page = 25

    @admin.display(boolean=True, description="Has test?")
    def has_quiz(self, obj):
        return bool(getattr(obj, "test", None))

    @admin.display(description="Manage test")
    def manage_quiz(self, obj):
        q = getattr(obj, "test", None)
        if q:
            url = reverse("admin:ui_quiz_change", args=[q.id])
            return format_html('<a class="button" href="{}">Edit quiz</a>', url)
        if obj.kind == "test":
            url = reverse("admin:ui_quiz_add")
            return format_html('<a class="button" href="{}">Add quiz</a>', url)
        return "—"


# ---- QuizAttempt: analitika + CSV eksport ----

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "quiz",
        "lesson",
        "percent",
        "points_gained",
        "points_total",
        "created_at",
    )
    list_filter = ("quiz", "lesson", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    date_hierarchy = "created_at"
    actions = ["export_attempts_csv"]
    list_per_page = 50

    @admin.action(description="Tanlangan urinishlarni CSV yuklab olish")
    def export_attempts_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="quiz_attempts.csv"'
        w = csv.writer(resp)
        w.writerow(
            [
                "User",
                "Quiz ID",
                "Lesson ID",
                "Points gained",
                "Points total",
                "Percent",
                "Created",
                "Finished",
                "Question IDs",
                "Answers JSON",
            ]
        )
        for a in queryset:
            w.writerow(
                [
                    str(a.user) if a.user_id else "",
                    a.quiz_id,
                    a.lesson_id,
                    a.points_gained,
                    a.points_total,
                    a.percent,
                    a.created_at,
                    a.finished_at,
                    ";".join(map(str, a.question_ids or [])),
                    a.answers_json,
                ]
            )
        return resp


# ==========================
# TORRENS ADMIN
# ==========================

if _HAS_MULTI_IMAGES:

    class TorrensTaskImageInline(admin.TabularInline):
        model = TorrensTaskImage
        extra = 0
        fields = ("image_thumb", "image", "caption")
        readonly_fields = ("image_thumb",)

        @admin.display(description="Preview")
        def image_thumb(self, obj):
            if obj.image:
                return format_html(
                    '<img src="{}" style="height:48px;border-radius:6px" />',
                    obj.image.url,
                )
            return "—"

    class TorrensAnswerImageInline(admin.TabularInline):
        model = TorrensAnswerImage
        extra = 0
        fields = ("image_thumb", "image", "caption")
        readonly_fields = ("image_thumb",)

        @admin.display(description="Preview")
        def image_thumb(self, obj):
            if obj.image:
                return format_html(
                    '<img src="{}" style="height:48px;border-radius:6px" />',
                    obj.image.url,
                )
            return "—"


class TorrensTaskInline(admin.TabularInline):
    """
    TorrensTest sahifasida topshiriqlar ro'yxati.
    Asosiy maydonlar bu yerda, rasmlarni esa TorrensTask adminida ko‘proq
    detallar bilan tahrir qilish mumkin.
    """
    model = TorrensTask
    extra = 1
    ordering = ("order",)

    def get_fields(self, request, obj=None):
        base = ["order", "prompt", "response_type", "hint", "reference_image"]
        if hasattr(self.model, "allow_text"):
            base.append("allow_text")
        if hasattr(self.model, "allow_images"):
            base.append("allow_images")
        if hasattr(self.model, "max_images"):
            base.append("max_images")
        return base


@admin.register(TorrensTask)
class TorrensTaskAdmin(admin.ModelAdmin):
    """
    Har bir Torrens topshirig'ini alohida ochib,
    UNGA bir nechta rasm (TorrensTaskImage) biriktirish uchun admin.
    """
    list_display = (
        "id",
        "test",
        "order",
        "response_type",
        "allow_text",
        "allow_images",
        "images_count",
    )
    list_filter = ("test", "response_type", "allow_text", "allow_images")
    search_fields = ("prompt",)
    ordering = ("test", "order")

    if _HAS_MULTI_IMAGES:
        inlines = [TorrensTaskImageInline]

    def get_fields(self, request, obj=None):
        base = ["test", "order", "prompt", "hint", "response_type", "reference_image"]
        if hasattr(TorrensTask, "allow_text"):
            base.append("allow_text")
        if hasattr(TorrensTask, "allow_images"):
            base.append("allow_images")
        if hasattr(TorrensTask, "max_images"):
            base.append("max_images")
        return base

    @admin.display(description="Rasmlar")
    def images_count(self, obj):
        if _HAS_MULTI_IMAGES:
            try:
                return obj.extra_images.count()
            except Exception:
                return 0
        return "—"


@admin.register(TorrensTest)
class TorrensTestAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "time_limit_minutes", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    fields = (
        "title",
        "slug",
        "description",
        "is_published",
        "time_limit_minutes",
        "created_at",
    )
    readonly_fields = ("created_at",)
    inlines = [TorrensTaskInline]
    list_per_page = 25


@admin.register(TorrensSubmission)
class TorrensSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "test", "status", "total_score", "started_at", "finished_at")
    list_filter = ("status", "test")
    search_fields = ("user__username", "test__title")
    actions = ["export_torrens_csv"]
    list_per_page = 50

    @admin.action(description="Torrens submissions CSV")
    def export_torrens_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="torrens_submissions.csv"'
        w = csv.writer(resp)
        w.writerow(["User", "Test ID", "Status", "Total score", "Started", "Finished"])
        for s in queryset:
            w.writerow(
                [
                    str(s.user),
                    s.test_id,
                    s.status,
                    s.total_score,
                    s.started_at,
                    s.finished_at,
                ]
            )
        return resp


@admin.register(TorrensAnswer)
class TorrensAnswerAdmin(admin.ModelAdmin):
    list_display = ("submission", "task", "score", "drawing_thumb", "images_count")
    list_filter = ("submission__test",)
    search_fields = ("submission__user__username", "task__test__title")
    list_editable = ("score",)
    if _HAS_MULTI_IMAGES:
        inlines = [TorrensAnswerImageInline]

    @admin.display(description="Drawing")
    def drawing_thumb(self, obj):
        if obj.drawing_image:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px" />',
                obj.drawing_image.url,
            )
        return "—"

    @admin.display(description="Rasmlar")
    def images_count(self, obj):
        if _HAS_MULTI_IMAGES:
            try:
                return obj.images.count()
            except Exception:
                return 0
        return "—"


# ==========================
# BOSHQA MODELLAR
# ==========================

@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = (
        "cover",
        "title",
        "standard",
        "display_creator",
        "display_year",
        "is_published",
        "created_at",
    )
    list_filter = ("standard", "is_published")
    search_fields = ("title", "dc_creator", "dc_format")
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            "Umumiy",
            {"fields": ("is_published", "standard", "title", "file", "link", "thumb")},
        ),
        (
            "Dublin Core (DC)",
            {
                "classes": ("collapse",),
                "fields": ("dc_creator", "dc_date", "dc_format"),
            },
        ),
        ("Texnik", {"fields": ("created_at",)}),
    )
    list_per_page = 25

    @admin.display(description="Muqova")
    def cover(self, obj):
        if getattr(obj, "thumb", None):
            return format_html(
                '<img src="{}" style="height:36px;border-radius:6px" />',
                obj.thumb.url,
            )
        return "—"


@admin.register(HomepageSlide)
class HomepageSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("title",)
    fields = (
        "title",
        "subtitle",
        "description",
        "image",
        "cta_primary_text",
        "cta_primary_url",
        "cta_secondary_text",
        "cta_secondary_url",
        "is_active",
        "order",
    )
    list_editable = ("order",)
    list_per_page = 25


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "role",
        "rating",
        "is_published",
        "order",
        "created_at",
    )
    list_filter = ("is_published",)
    search_fields = ("full_name", "role", "quote")
    ordering = ("order", "id")
    list_editable = ("is_published", "order", "rating")
    actions = ["publish_selected", "unpublish_selected"]
    list_per_page = 50

    @admin.action(description="Tanlangan fikrlarni e’lon qilish")
    def publish_selected(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Tanlangan fikrlarni yashirish")
    def unpublish_selected(self, request, queryset):
        queryset.update(is_published=False)
