import streamlit as st
from PIL import Image, ImageOps, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io
import math

st.set_page_config(
    page_title="PhotoPrint Pro",
    page_icon="📸",
    layout="wide"
)

st.title("📸 PhotoPrint Pro")
st.caption("تجهيز وترتيب الصور للطباعة على ورق A4")

# =========================
# مقاسات الصور بالسنتيمتر
# =========================

SIZES = {
    "صورة هوية 3×4 سم": (3, 4),
    "صورة 4×6 سم": (4, 6),
    "صورة 5×5 سم": (5, 5),
    "صورة 6×9 سم": (6, 9),
    "صورة 10×15 سم": (10, 15),
}

# A4 بالسنتيمتر
A4_W = 21.0
A4_H = 29.7

# =========================
# تحويل سم إلى نقاط PDF
# =========================

def cm_to_pt(cm):
    return cm * 28.3464567


# =========================
# تجهيز الصورة
# =========================

def prepare_image(image, width_cm, height_cm):

    image = image.convert("RGB")

    target_ratio = width_cm / height_cm
    image_ratio = image.width / image.height

    if image_ratio > target_ratio:

        new_width = int(
            image.height * target_ratio
        )

        left = (
            image.width - new_width
        ) // 2

        image = image.crop(
            (
                left,
                0,
                left + new_width,
                image.height
            )
        )

    else:

        new_height = int(
            image.width / target_ratio
        )

        top = (
            image.height - new_height
        ) // 2

        image = image.crop(
            (
                0,
                top,
                image.width,
                top + new_height
            )
        )

    return image


# =========================
# إنشاء PDF
# =========================

def create_pdf(
    image,
    width_cm,
    height_cm,
    copies,
    margin_cm,
    gap_cm
):

    page_width, page_height = A4

    photo_w = cm_to_pt(width_cm)
    photo_h = cm_to_pt(height_cm)

    margin = cm_to_pt(margin_cm)
    gap = cm_to_pt(gap_cm)

    available_w = page_width - (
        margin * 2
    )

    available_h = page_height - (
        margin * 2
    )

    columns = max(
        1,
        int(
            (available_w + gap)
            /
            (photo_w + gap)
        )
    )

    rows = max(
        1,
        int(
            (available_h + gap)
            /
            (photo_h + gap)
        )
    )

    per_page = columns * rows

    pages = math.ceil(
        copies / per_page
    )

    output = io.BytesIO()

    pdf = canvas.Canvas(
        output,
        pagesize=A4
    )

    prepared = prepare_image(
        image,
        width_cm,
        height_cm
    )

    image_buffer = io.BytesIO()

    prepared.save(
        image_buffer,
        format="JPEG",
        quality=95
    )

    image_buffer.seek(0)

    img_reader = ImageReader(
        image_buffer
    )

    copy_number = 0

    for page in range(pages):

        for row in range(rows):

            for col in range(columns):

                if copy_number >= copies:
                    break

                x = (
                    margin
                    +
                    col * (photo_w + gap)
                )

                y = (
                    page_height
                    -
                    margin
                    -
                    photo_h
                    -
                    row * (photo_h + gap)
                )

                pdf.drawImage(
                    img_reader,
                    x,
                    y,
                    width=photo_w,
                    height=photo_h,
                    preserveAspectRatio=True,
                    anchor="c"
                )

                # علامات قص بسيطة
                pdf.setLineWidth(0.3)

                pdf.line(
                    x - 3,
                    y,
                    x + 3,
                    y
                )

                pdf.line(
                    x,
                    y - 3,
                    x,
                    y + 3
                )

                pdf.line(
                    x + photo_w - 3,
                    y,
                    x + photo_w + 3,
                    y
                )

                pdf.line(
                    x + photo_w,
                    y - 3,
                    x + photo_w,
                    y + 3
                )

                copy_number += 1

            if copy_number >= copies:
                break

        pdf.showPage()

    pdf.save()

    output.seek(0)

    return (
        output,
        columns,
        rows,
        per_page,
        pages
    )


# =========================
# رفع الصورة
# =========================

uploaded = st.file_uploader(
    "📸 ارفع الصورة",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)

if uploaded:

    image = Image.open(
        uploaded
    )

    st.success(
        "تم رفع الصورة بنجاح ✅"
    )

    left, right = st.columns(2)

    with left:

        st.subheader(
            "الصورة الأصلية"
        )

        st.image(
            image,
            use_container_width=True
        )

    with right:

        st.subheader(
            "إعدادات الطباعة"
        )

        size_name = st.selectbox(
            "📐 مقاس الصورة",
            list(SIZES.keys())
        )

        width_cm, height_cm = SIZES[
            size_name
        ]

        copies = st.number_input(
            "🔢 عدد النسخ",
            min_value=1,
            max_value=500,
            value=8,
            step=1
        )

        margin_cm = st.number_input(
            "📏 هامش الورقة سم",
            min_value=0.0,
            max_value=3.0,
            value=0.5,
            step=0.1
        )

        gap_cm = st.number_input(
            "↔️ المسافة بين الصور سم",
            min_value=0.0,
            max_value=2.0,
            value=0.2,
            step=0.1
        )

        generate = st.button(
            "🖨️ تجهيز للطباعة",
            type="primary",
            use_container_width=True
        )

    if generate:

        with st.spinner(
            "جاري تجهيز ورقة الطباعة..."
        ):

            (
                pdf,
                columns,
                rows,
                per_page,
                pages
            ) = create_pdf(
                image,
                width_cm,
                height_cm,
                copies,
                margin_cm,
                gap_cm
            )

        st.divider()

        st.header(
            "✅ تم تجهيز الملف"
        )

        a, b, c, d = st.columns(4)

        with a:
            st.metric(
                "عدد النسخ",
                copies
            )

        with b:
            st.metric(
                "صور بالورقة",
                per_page
            )

        with c:
            st.metric(
                "عدد الأعمدة",
                columns
            )

        with d:
            st.metric(
                "عدد الصفحات",
                pages
            )

        st.download_button(
            "📥 تحميل PDF للطباعة",
            data=pdf,
            file_name="photo_print_A4.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
