# ui/signals.py
import os
import tempfile
import shutil
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import File
from .models import Lesson

logger = logging.getLogger(__name__)

try:
    from docx2pdf import convert
except ImportError:
    convert = None
    logger.warning("⚠️ 'docx2pdf' moduli topilmadi. DOCX → PDF konvertatsiya o‘tkazilmaydi.")


@receiver(post_save, sender=Lesson)
def convert_docx_to_pdf(sender, instance: Lesson, created, **kwargs):
    """
    DOC/DOCX dars yuklanganda avtomatik tarzda PDF versiyasini yaratadi.
    """
    if not convert:
        return

    if instance.kind != "doc" or not instance.document_file:
        return

    ext = os.path.splitext(instance.document_file.name)[1].lower()
    if ext not in (".doc", ".docx"):
        return

    src_path = instance.document_file.path
    if not os.path.exists(src_path):
        logger.warning(f"Fayl topilmadi: {src_path}")
        return

    # Windows/Mac uchun docx2pdf ishlaydi
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, os.path.basename(src_path).rsplit(".", 1)[0] + ".pdf")

            logger.info(f"DOCX → PDF konvertatsiya: {src_path} → {out_path}")
            convert(src_path, out_path)

            if not os.path.exists(out_path):
                logger.warning(f"Konvertatsiyadan so‘ng PDF topilmadi: {out_path}")
                return

            # Saqlash (signal recursion oldini olish)
            from django.db.models.signals import post_save as _ps
            _ps.disconnect(convert_docx_to_pdf, sender=Lesson)

            with open(out_path, "rb") as f:
                pdf_name = os.path.basename(out_path)
                instance.document_file.save(pdf_name, File(f), save=False)
                instance.kind = "pdf"
                instance.save(update_fields=["document_file", "kind"])

            _ps.connect(convert_docx_to_pdf, sender=Lesson)
            logger.info(f"✅ {instance} uchun PDF versiya yaratildi.")

    except Exception as e:
        logger.error(f"DOCX konvertatsiya xatosi ({instance}): {e}")
        # Xato chiqsa ham dars saqlanishi to‘xtamasin
        return
