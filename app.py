import streamlit as st
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io
import math

# ==============================
# إعداد الموقع
# ==============================

st.set_page_config(
    page_title="PhotoPrint Pro",
    page_icon="📸",
    layout="wide"
)

st.title("📸 PhotoPrint Pro")
st.write("برنامج تجهيز الصور للطباعة تلقائيًا على ورق A4")

# ==============================
# المقاسات
# ==============================

SIZES = {
    "3 × 4 سم": (3, 4),
    "4 × 6 سم": (4, 6),
    "5 × 5 سم": (5, 5),
    "6 × 9 سم": (6, 9),
    "10 × 15 سم": (10, 15),
}

# ==============================
# القوالب
# ==============================

TEMPLATES = {
    "6 صور — سطر واحد": (6, 1),
    "8 صور — سطر واحد": (8, 1),
    "10 صور — سطر واحد": (10, 1),
    "12 صورة — سطرين (6 + 6)": (6, 2),
    "18 صورة — 3 أسطر (6 + 6 + 6)": (6, 3),
    "24 صورة — 4 أسطر (6 + 6 + 6 + 6)": (6, 4),
    "مخصص": None,
}

# A4 بالنقاط
A4_WIDTH, A4_HEIGHT = A4

CM = 28.3464567


def cm_to_pt(value):
    return value * CM


# ==============================
# قص الصورة حسب المقاس
# ==============================

def crop_image(image, target_w, target_h):

    image = image.convert("RGB")

    target_ratio = target_w / target_h
    current_ratio = image.width / image.height

    if current_ratio > target_ratio:

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


# ==============================
# تجهيز الصورة للـ PDF
# ==============================

def image_reader(image):

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=95
    )

    buffer.seek(0)

    return ImageReader(buffer)


# ==============================
# إنشاء PDF
# ==============================

def create_pdf(
    image,
    photo_w_cm,
    photo_h_cm,
    columns,
    rows,
    margin_cm,
    gap_cm
):

    photo_w = cm_to_pt(photo_w_cm)
    photo_h = cm_to_pt(photo_h_cm)

    margin = cm_to_pt(margin_cm)
    gap = cm_to_pt(gap_cm)

    # حساب الحجم الكامل للقالب
    total_w = (
        columns * photo_w
        +
        (columns - 1) * gap
    )

    total_h = (
        rows * photo_h
        +
        (rows - 1) * gap
    )

    # إذا القالب أكبر من A4
    if (
        total_w > A4_WIDTH - 2 * margin
        or
        total_h > A4_HEIGHT - 2 * margin
    ):
        return None

    # توسيط القالب
    start_x = (
        A4_WIDTH - total_w
    ) / 2

    start_y = (
        A4_HEIGHT + total_h
    ) / 2

    prepared = crop_image(
        image,
        photo_w_cm,
        photo_h_cm
    )

    reader = image_reader(
        prepared
    )

    output = io.BytesIO()

    pdf = canvas.Canvas(
        output,
        pagesize=A4
    )

    for row in range(rows):

        for col in range(columns):

            x = (
                start_x
                +
                col * (photo_w + gap)
            )

            y = (
                start_y
                -
                photo_h
                -
                row * (photo_h + gap)
            )

            pdf.drawImage(
                reader,
                x,
                y,
                width=photo_w,
                height=photo_h,
                preserveAspectRatio=False
            )

            # علامات قص
            pdf.setLineWidth(0.4)

            # أعلى يسار
            pdf.line(
                x - 4,
                y + photo_h,
                x + 3,
                y + photo_h
            )

            pdf.line(
                x,
                y + photo_h + 4,
                x,
                y + photo_h - 3
            )

            # أعلى يمين
            pdf.line(
                x + photo_w - 3,
                y + photo_h,
                x + photo_w + 4,
                y + photo_h
            )

            pdf.line(
                x + photo_w,
                y + photo_h + 4,
                x + photo_w,
                y + photo_h - 3
            )

            # أسفل يسار
            pdf.line(
                x - 4,
                y,
                x + 3,
                y
            )

            pdf.line(
                x,
                y - 4,
                x,
                y + 3
            )

            # أسفل يمين
            pdf.line(
                x + photo_w - 3,
                y,
                x + photo_w + 4,
                y
            )

            pdf.line(
                x + photo_w,
                y - 4,
                x + photo_w,
                y + 3
            )

    pdf.showPage()
    pdf.save()

    output.seek(0)

    return output


# ==============================
# رفع الصورة
# ==============================

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
        "تم رفع الصورة ✅"
    )

    st.divider()

    # ==========================
    # الإعدادات
    # ==========================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "📐 مقاس الصورة"
        )

        size_name = st.selectbox(
            "اختار المقاس",
            list(SIZES.keys())
        )

        photo_w, photo_h = SIZES[
            size_name
        ]

    with col2:

        st.subheader(
            "🧩 قالب الطباعة"
        )

        template_name = st.selectbox(
            "اختار القالب",
            list(TEMPLATES.keys())
        )

    # ==========================
    # القالب
    # ==========================

    template = TEMPLATES[
        template_name
    ]

    if template is None:

        col1, col2 = st.columns(2)

        with col1:

            columns = st.number_input(
                "عدد الصور بالسطر",
                min_value=1,
                max_value=10,
                value=6
            )

        with col2:

            rows = st.number_input(
                "عدد الأسطر",
                min_value=1,
                max_value=10,
                value=1
            )

    else:

        columns, rows = template

    # ==========================
    # المسافات
    # ==========================

    col1, col2 = st.columns(2)

    with col1:

        gap = st.number_input(
            "↔️ المسافة بين الصور (سم)",
            min_value=0.0,
            max_value=2.0,
            value=0.15,
            step=0.05
        )

    with col2:

        st.info(
            f"القالب يحتوي على "
            f"**{columns * rows} صورة**"
        )

    # ==========================
    # معاينة
    # ==========================

    st.divider()

    st.subheader(
        "👀 المعاينة"
    )

    # معاينة بسيطة للقالب
    preview_cols = st.columns(
        min(columns, 10)
    )

    for i in range(columns):

        with preview_cols[i]:

            st.image(
                image,
                use_container_width=True
            )

    if rows > 1:

        for r in range(rows - 1):

            preview_cols = st.columns(
                min(columns, 10)
            )

            for i in range(columns):

                with preview_cols[i]:

                    st.image(
                        image,
                        use_container_width=True
                    )

    # ==========================
    # إنشاء PDF
    # ==========================

    st.divider()

    if st.button(
        "🖨️ إنشاء PDF جاهز للطباعة",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "جاري إنشاء قالب الطباعة..."
        ):

            pdf = create_pdf(
                image,
                photo_w,
                photo_h,
                columns,
                rows,
                0.5,
                gap
            )

        if pdf is None:

            st.error(
                "❌ هذا القالب أكبر من مساحة ورقة A4. "
                "جرّب مقاس صورة أصغر أو عدد صور أقل."
            )

        else:

            st.success(
                "✅ تم إنشاء القالب بنجاح!"
            )

            st.download_button(
                "📥 تحميل PDF للطباعة",
                data=pdf,
                file_name="photo_print_A4.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
