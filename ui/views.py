# ui/views.py

from urllib.parse import quote
import base64
import json
import random
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count, Q, Prefetch
from django.forms import inlineformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import FileResponse

# 💡 YANGI: admin forma importlari (torrens_create uchun)
from .forms import TestimonialForm, TorrensTestForm, TorrensTaskForm

from .models import (
    Category, Course, Instructor, Lesson, LibraryItem,
    # Quiz
    Quiz, Question, Choice, QuizAttempt,
    # Torrens
    TorrensTest, TorrensTask, TorrensSubmission, TorrensAnswer, Testimonial,
    # Agar modellaringizga qo‘shgan bo‘lsangiz — ko‘p rasm qo‘llab-quvvatlash
    # (oldingi javobimdagi modellardan)
    # ⚠️ Agar bu modellar hali yo‘q bo‘lsa, pastdagi importlarni comment qiling.
    # va avval models.py ni yangilang.
    # noqa: F401 (agar lint chiqqan bo‘lsa)
)

# Agar siz oldingi taklifimdagi ko‘p rasm modellarini qo‘shgan bo‘lsangiz, quyidagini oching:
try:
    from .models import TorrensTaskImage, TorrensAnswerImage  # type: ignore
    _HAS_MULTI_IMAGE_MODELS = True
except Exception:
    _HAS_MULTI_IMAGE_MODELS = False


# =========================================================
# Yordamchi: bo‘lim/lessonlarni tekislash
# =========================================================
def _flatten_lessons(course: Course):
    sections = (
        course.sections
        .prefetch_related(
            Prefetch("lessons", queryset=Lesson.objects.all().order_by("order", "id"))
        )
        .all()
    )
    flat = [l for s in sections for l in s.lessons.all()]
    return sections, flat


# =========================================================
# Asosiy sahifa
# =========================================================
def index(request):
    categories = (
        Category.objects
        .annotate(total=Count("courses"))
        .order_by("-total", "name")[:4]
    )

    featured_courses = list(Course.objects.filter(is_featured=True)[:6])
    if len(featured_courses) < 6:
        extras = Course.objects.exclude(id__in=[c.id for c in featured_courses])[:6 - len(featured_courses)]
        featured_courses += list(extras)

    instructors = Instructor.objects.all()[:4]
    testimonials = Testimonial.objects.filter(is_published=True)[:8]

    ctx = {
        "categories": categories,
        "featured_courses": featured_courses,
        "instructors": instructors,
        "testimonials": testimonials,
        "tests_preview": [],  # har doim bo‘lsin
    }
    return render(request, "ui/index.html", ctx)


# =========================================================
# Biz haqimizda
# =========================================================
def about(request):
    instructors = Instructor.objects.all().order_by("full_name")
    return render(request, "ui/about.html", {"instructors": instructors, "tests_preview": []})


# =========================================================
# Aloqa (email jo‘natish)
# =========================================================
def contact(request):
    ctx = {"sent": False, "tests_preview": []}
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if name and email and subject and message:
            body = (
                "Yangi kontakt xabari\n\n"
                f"Ism: {name}\nEmail: {email}\nMavzu: {subject}\n\nXabar:\n{message}"
            )
            send_mail(
                subject=f"[eLEARNING] {subject or 'Contact'}",
                message=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
                recipient_list=[getattr(settings, "CONTACT_TO_EMAIL", "admin@example.com")],
                fail_silently=True,
            )
            ctx["sent"] = True
        else:
            ctx["error"] = "Iltimos, barcha maydonlarni to‘ldiring."
    return render(request, "ui/contact.html", ctx)


# =========================================================
# Kurslar ro‘yxati
# =========================================================
def course_list(request):
    q = request.GET.get("q", "")
    cat_slug = request.GET.get("category")
    order = request.GET.get("order", "-created_at")

    courses = Course.objects.select_related("category", "instructor")

    if q:
        courses = courses.filter(Q(title__icontains=q) | Q(instructor__full_name__icontains=q))
    if cat_slug:
        courses = courses.filter(category__slug=cat_slug)

    allowed_orders = {"created_at", "-created_at", "price", "-price", "rating", "-rating", "title", "-title"}
    if order in allowed_orders:
        courses = courses.order_by(order)

    paginator = Paginator(courses, 9)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    cats = Category.objects.annotate(total=Count("courses")).order_by("name")

    context = {
        "page_obj": page_obj,
        "categories": cats,
        "active_category": cat_slug,
        "q": q,
        "order": order,
        "featured_courses": Course.objects.filter(is_featured=True)[:3],
        "tests_preview": [],
    }
    return render(request, "ui/courses.html", context)


# =========================================================
# Kurs detali
# =========================================================
def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor"),
        slug=slug,
    )
    related = Course.objects.filter(category=course.category).exclude(pk=course.pk)[:6]
    return render(request, "ui/course_detail.html", {"course": course, "related": related, "tests_preview": []})


def course_enroll(request, slug):
    course = get_object_or_404(Course, slug=slug)
    return render(request, "ui/enroll_success.html", {"course": course, "tests_preview": []})


# =========================================================
# QUIZ yordamchilar
# =========================================================
def _select_question_ids(quiz: Quiz):
    q_ids = list(quiz.questions.values_list("id", flat=True))
    if quiz.shuffle_questions:
        random.shuffle(q_ids)
    if quiz.limit_questions and quiz.limit_questions > 0:
        q_ids = q_ids[: quiz.limit_questions]
    return q_ids


def _build_quiz_view(quiz: Quiz, question_ids):
    q_queryset = (
        Question.objects
        .filter(quiz=quiz, id__in=question_ids)
        .select_related("quiz")
        .order_by("order", "id")
    )
    q_map = {q.id: q for q in q_queryset}
    ordered = [q_map[qid] for qid in question_ids if qid in q_map]

    items = []
    for q in ordered:
        choices_qs = q.choices.all()
        choices = list(choices_qs)
        if quiz.shuffle_choices:
            random.shuffle(choices)
        items.append({"q": q, "choices": choices})
    return items


def _pick_advice(quiz: Quiz, percent: float) -> str:
    low = getattr(quiz, "advice_low", "") or ""
    mid = getattr(quiz, "advice_mid", "") or ""
    high = getattr(quiz, "advice_high", "") or ""
    mid_min = getattr(quiz, "advice_mid_min", 50) or 50
    high_min = getattr(quiz, "advice_high_min", 80) or 80

    if percent >= high_min and high:
        return high
    if percent >= mid_min and mid:
        return mid
    return low or "Mashg‘ulotlarni davom ettiring: asosiy tushunchalarni yana bir bor ko‘rib chiqing."


# =========================================================
# Kursni o‘qish (video/pdf/doc/test)
# =========================================================
def course_learn(request, slug):
    course = get_object_or_404(Course, slug=slug)
    sections, flat = _flatten_lessons(course)

    sel = request.GET.get("l")
    lesson = next((x for x in flat if str(x.id) == str(sel)), None) if sel else (flat[0] if flat else None)

    prev_lesson = next_lesson = None
    if lesson:
        idx = flat.index(lesson)
        if idx > 0:
            prev_lesson = flat[idx - 1]
        if idx < len(flat) - 1:
            next_lesson = flat[idx + 1]

    office_embed_url = pdf_embed_url = ""
    if lesson and lesson.kind in ("pdf", "doc") and lesson.document_file:
        abs_url = request.build_absolute_uri(lesson.document_file.url)
        if lesson.kind == "pdf":
            pdf_embed_url = abs_url
        elif lesson.kind == "doc":
            office_embed_url = "https://view.officeapps.live.com/op/embed.aspx?src=" + quote(abs_url, safe="")

    quiz_result = None
    selected_map = {}
    quiz_view_items = []
    quiz_attempt_saved = None
    quiz_attempt_error = None

    if lesson and lesson.kind == "test":
        quiz = getattr(lesson, "test", None)
        if quiz:
            sess_key = f"quiz_sel_{lesson.id}"
            if request.method == "POST":
                posted_ids = request.POST.get("question_ids", "")
                if posted_ids:
                    try:
                        question_ids = [int(x) for x in posted_ids.split(",") if x.strip().isdigit()]
                        request.session[sess_key] = question_ids
                    except Exception:
                        question_ids = request.session.get(sess_key) or _select_question_ids(quiz)
                else:
                    question_ids = request.session.get(sess_key) or _select_question_ids(quiz)
            else:
                question_ids = _select_question_ids(quiz)
                request.session[sess_key] = question_ids

            quiz_view_items = _build_quiz_view(quiz, question_ids)

    return render(request, "ui/course_learn.html", {
        "course": course,
        "sections": sections,
        "lesson": lesson,
        "prev_lesson": prev_lesson,
        "next_lesson": next_lesson,
        "office_embed_url": office_embed_url,
        "pdf_embed_url": pdf_embed_url,
        "quiz_result": quiz_result,
        "selected_map": selected_map,
        "quiz_view": {
            "items": quiz_view_items or [],
            "question_ids_csv": ",".join(str(x["q"].id) for x in (quiz_view_items or [])),
            "attempt_saved": quiz_attempt_saved,
            "attempt_error": quiz_attempt_error,
        },
        "tests_preview": [],
    })


# =========================================================
# Kutubxona
# =========================================================
def library(request):
    items = LibraryItem.objects.filter(is_published=True).order_by("-created_at")
    return render(request, "ui/library.html", {"items": items, "tests_preview": []})


# =========================================================
# Ro‘yxatdan o‘tish / Kirish
# =========================================================
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Muvaffaqiyatli ro‘yxatdan o‘tdingiz!")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "ui/register.html", {"form": form, "tests_preview": []})


class MyLoginView(LoginView):
    template_name = "ui/login.html"

    def form_valid(self, form):
        remember = self.request.POST.get("remember")
        if not remember:
            self.request.session.set_expiry(0)
        return super().form_valid(form)


# =========================================================
# Jamoa / Fikrlar
# =========================================================
def team(request):
    instructors = Instructor.objects.all().order_by("full_name")
    return render(request, "ui/team.html", {"instructors": instructors, "tests_preview": []})


def testimonial(request):
    items = Testimonial.objects.filter(is_published=True).order_by("order", "id")
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.is_published = False
            inst.save()
            messages.success(request, "Rahmat! Fikringiz yuborildi va ko‘rib chiqiladi.")
            return redirect("testimonial")
        else:
            messages.error(request, "Ma’lumotlarni tekshirib qayta yuboring.")
    else:
        form = TestimonialForm()
    return render(request, "ui/testimonial.html", {"items": items, "form": form, "tests_preview": []})


# =========================================================
# TORRENS (ro‘yxat, detal, yaratish, topshirish, baholash)
# =========================================================
def torrens_list(request):
    tests = TorrensTest.objects.order_by("-created_at")
    return render(request, "ui/torrens_list.html", {
        "tests": tests,
        "tests_preview": [],
    })


def torrens_detail(request, slug):
    test = get_object_or_404(TorrensTest, slug=slug)
    return render(request, "ui/torrens_detail.html", {
        "test": test,
        "tests_preview": [],
    })


@staff_member_required
def torrens_create(request):
    TaskFormSet = inlineformset_factory(
        TorrensTest, TorrensTask, form=TorrensTaskForm, extra=1, can_delete=True
    )
    if request.method == "POST":
        form = TorrensTestForm(request.POST, request.FILES)
        formset = TaskFormSet(request.POST, request.FILES)
        if form.is_valid():
            test = form.save()
            formset = TaskFormSet(request.POST, request.FILES, instance=test)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Torrens testi yaratildi.")
                return redirect("torrens_detail", slug=test.slug)
        # xatolar bo‘lsa shu yerda qoladi
    else:
        form = TorrensTestForm()
        formset = TaskFormSet()

    return render(request, "ui/torrens_form.html", {
        "form": form,
        "formset": formset,
        "tests_preview": [],
    })


@login_required
def torrens_take(request, slug):
    """
    Topshiriqlar bo‘yicha javob qabul qilish:
    - text / list / drawing (mavjud)
    - allow_text bo‘lsa: qo‘shimcha matn (task_{id}_text)
    - allow_images bo‘lsa: bir nechta rasm (task_{id}_images, multiple)
    """
    test = get_object_or_404(TorrensTest, slug=slug, is_published=True)
    sub, _ = TorrensSubmission.objects.get_or_create(
        test=test, user=request.user, finished_at__isnull=True
    )

    if request.method == "POST":
        for task in test.tasks.all():
            ans, _ = TorrensAnswer.objects.get_or_create(submission=sub, task=task)

            # --- Eski turlar (moslik uchun) ---
            if task.response_type == "text":
                ans.text_answer = request.POST.get(f"task_{task.id}_text", "").strip()

            elif task.response_type == "list":
                raw = request.POST.get(f"task_{task.id}_list", "").strip()
                rows = [r.strip() for r in raw.splitlines() if r.strip()]
                ans.list_answer = rows

            elif task.response_type == "drawing":
                if request.FILES.get(f"task_{task.id}_image"):
                    ans.drawing_image = request.FILES[f"task_{task.id}_image"]
                data_url = request.POST.get(f"task_{task.id}_fabric_png", "")
                if data_url.startswith("data:image/png;base64,"):
                    _fmt, imgstr = data_url.split(";base64,", 1)
                    png_bytes = base64.b64decode(imgstr)
                    ans.drawing_image.save(f"torrens_task_{task.id}.png", ContentFile(png_bytes), save=False)

            # --- 🆕 Kombinatsion javoblar ---
            # Qo‘shimcha matn (hatto response_type boshqa bo‘lsa ham)
            add_text = request.POST.get(f"task_{task.id}_text", "").strip()
            if getattr(task, "allow_text", True) and add_text:
                # text_answer mavjud bo‘lsa, biriktirib boramiz
                ans.text_answer = (ans.text_answer or "").strip()
                ans.text_answer = (ans.text_answer + ("\n" if ans.text_answer else "") + add_text).strip()

            # Ko‘p rasm yuklash (multi)
            if _HAS_MULTI_IMAGE_MODELS and getattr(task, "allow_images", True):
                files = request.FILES.getlist(f"task_{task.id}_images") or []
                if files:
                    max_imgs = getattr(task, "max_images", 5) or 0
                    # Eski mavjud rasmlarni faqat yangi fayllar kelganda yangilaymiz (o‘rniga yozish)
                    ans.images.all().delete()
                    # Cheklovdan ortig‘ini qirqib tashlaymiz
                    files = files[:max(0, max_imgs)]
                    for f in files:
                        TorrensAnswerImage.objects.create(answer=ans, image=f)

                    if getattr(task, "max_images", 0) and len(files) >= task.max_images:
                        # foydalanuvchiga bildirgich
                        messages.info(request, f"#{task.order} topshiriqda maksimal {task.max_images} ta rasm saqlandi.")

            ans.save()

        if "finish" in request.POST:
            sub.finished_at = timezone.now()
            sub.status = "finished"
            sub.save()
            messages.success(request, "Javoblaringiz saqlandi va yakunlandi.")
            return redirect("torrens_detail", slug=test.slug)

        messages.success(request, "Javoblar saqlandi (davom etishingiz mumkin).")

    return render(request, "ui/torrens_take.html", {
        "test": test,
        "submission": sub,
        "tests_preview": [],
    })


@staff_member_required
def torrens_grade(request, slug, submission_id):
    test = get_object_or_404(TorrensTest, slug=slug)
    sub = get_object_or_404(TorrensSubmission, pk=submission_id, test=test)

    if request.method == "POST":
        total = 0.0
        for ans in sub.answers.select_related("task"):
            score_val = request.POST.get(f"score_{ans.id}", "")
            note_val = request.POST.get(f"note_{ans.id}", "")
            try:
                ans.score = float(score_val or 0)
            except ValueError:
                ans.score = 0.0
            ans.note = note_val
            ans.save()
            total += ans.score

        sub.total_score = total
        sub.status = "graded"
        sub.save()
        messages.success(request, "Baholash saqlandi.")
        return redirect("torrens_grade", slug=slug, submission_id=submission_id)

    return render(request, "ui/torrens_grade.html", {
        "test": test,
        "submission": sub,
        "tests_preview": [],
    })


@xframe_options_exempt
def preview_pdf(request, rel_path):
    full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
    f = open(full_path, 'rb')
    resp = FileResponse(f, content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="document.pdf"'
    return resp
