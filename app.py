import streamlit as st
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io
import math

# ==========================================
# إعداد الصفحة
# ==========================================

st.set_page_config(
    page_title="PhotoPrint Pro",
    page_icon="📸",
    layout="wide"
)

st.title("📸 PhotoPrint Pro")
st.caption("تجهيز عدة صور للطباعة تلقائيًا على ورق A4")

# ==========================================
# المقاسات
# ==========================================

SIZES = {
    "3 × 4 سم": (3, 4),
    "4 × 6 سم": (4, 6),
    "5 × 5 سم": (5, 5),
    "6 × 9 سم": (6, 9),
    "10 × 15 سم": (10, 15),
}

# ==========================================
# القوالب
# ==========================================

TEMPLATES = {
    "6 صور بالسطر": 6,
    "8 صور بالسطر": 8,
    "10 صور بالسطر": 10,
    "5 صور بالسطر": 5,
    "4 صور بالسطر": 4,
    "مخصص": None,
}

A4_WIDTH, A4_HEIGHT = A4
CM = 28.3464567


def cm_to_pt(value):
    return value * CM


# ==========================================
# قص الصورة حسب المقاس
# ==========================================

def crop_image(image, width_cm, height_cm):

    image = image.convert("RGB")

    target_ratio = width_cm / height_cm
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


# ==========================================
# تحويل الصورة إلى ImageReader
# ==========================================

def make_reader(image):

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=95
    )

    buffer.seek(0)

    return ImageReader(buffer)


# ==========================================
# حساب ترتيب الصور
# ==========================================

def calculate_layout(
    width_cm,
    height_cm,
    columns,
    gap_cm,
    margin_cm
):

    photo_w = cm_to_pt(width_cm)
    photo_h = cm_to_pt(height_cm)

    gap = cm_to_pt(gap_cm)
    margin = cm_to_pt(margin_cm)

    available_w = (
        A4_WIDTH - margin * 2
    )

    available_h = (
        A4_HEIGHT - margin * 2
    )

    # العدد الفعلي الممكن بالسطر
    max_columns = int(
        (available_w + gap)
        /
        (photo_w + gap)
    )

    columns = min(
        columns,
        max_columns
    )

    if columns < 1:
        return None

    rows = int(
        (available_h + gap)
        /
        (photo_h + gap)
    )

    if rows < 1:
        return None

    per_page = columns * rows

    return {
        "columns": columns,
        "rows": rows,
        "per_page": per_page,
        "photo_w": photo_w,
        "photo_h": photo_h,
        "gap": gap,
        "margin": margin,
    }


# ==========================================
# إنشاء PDF متعدد الصور
# ==========================================

def create_pdf(
    image_items,
    width_cm,
    height_cm,
    columns,
    gap_cm,
    margin_cm
):

    layout = calculate_layout(
        width_cm,
        height_cm,
        columns,
        gap_cm,
        margin_cm
    )

    if layout is None:
        return None, 0

    photo_w = layout["photo_w"]
    photo_h = layout["photo_h"]
    gap = layout["gap"]
    rows = layout["rows"]
    columns = layout["columns"]

    total_slots = columns * rows

    # --------------------------------------
    # تحضير كل الصور والنسخ
    # --------------------------------------

    items = []

    for item in image_items:

        prepared = crop_image(
            item["image"],
            width_cm,
            height_cm
        )

        reader = make_reader(
            prepared
        )

        for _ in range(
            item["copies"]
        ):

            items.append({
                "reader": reader,
                "name": item["name"]
            })

    # --------------------------------------
    # إنشاء PDF
    # --------------------------------------

    output = io.BytesIO()

    pdf = canvas.Canvas(
        output,
        pagesize=A4
    )

    total_pages = (
        math.ceil(
            len(items) / total_slots
        )
        if items
        else 0
    )

    for index, item in enumerate(items):

        slot = index % total_slots

        row = slot // columns
        col = slot % columns

        if slot == 0:

            # توسيط القالب
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

            start_x = (
                A4_WIDTH - total_w
            ) / 2

            start_y = (
                A4_HEIGHT + total_h
            ) / 2

        x = (
            start_x
            +
            col * (
                photo_w + gap
            )
        )

        y = (
            start_y
            -
            photo_h
            -
            row * (
                photo_h + gap
            )
        )

        pdf.drawImage(
            item["reader"],
            x,
            y,
            width=photo_w,
            height=photo_h,
            preserveAspectRatio=False
        )

        # علامات القص
        pdf.setLineWidth(0.35)

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

        # إذا الصفحة امتلأت
        if (
            (index + 1) % total_slots == 0
        ):

            pdf.showPage()

    # إذا بقيت صور بصفحة أخيرة
    if len(items) % total_slots != 0:
        pdf.showPage()

    pdf.save()

    output.seek(0)

    return output, total_pages


# ==========================================
# رفع عدة صور
# ==========================================

uploaded_files = st.file_uploader(
    "📸 ارفع الصور",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
    accept_multiple_files=True
)


if uploaded_files:

    st.success(
        f"تم رفع {len(uploaded_files)} صور ✅"
    )

    st.divider()

    # ======================================
    # إعدادات عامة
    # ======================================

    col1, col2 = st.columns(2)

    with col1:

        size_name = st.selectbox(
            "📐 مقاس الصور",
            list(SIZES.keys())
        )

        photo_w, photo_h = SIZES[
            size_name
        ]

    with col2:

        template_name = st.selectbox(
            "🧩 قالب الطباعة",
            list(TEMPLATES.keys())
        )

    template_columns = TEMPLATES[
        template_name
    ]

    if template_columns is None:

        columns = st.number_input(
            "عدد الصور بالسطر",
            min_value=1,
            max_value=10,
            value=6
        )

    else:

        columns = template_columns

    # ======================================
    # المسافة
    # ======================================

    gap = st.number_input(
        "↔️ المسافة بين الصور (سم)",
        min_value=0.0,
        max_value=2.0,
        value=0.15,
        step=0.05
    )

    st.divider()

    st.subheader(
        "🧾 عدد النسخ لكل صورة"
    )

    # ======================================
    # قائمة الصور
    # ======================================

    image_items = []

    total_copies = 0

    for index, file in enumerate(
        uploaded_files
    ):

        try:

            image = Image.open(
                file
            ).convert("RGB")

        except:

            st.error(
                f"تعذر قراءة {file.name}"
            )

            continue

        col1, col2, col3 = st.columns(
            [1, 3, 2]
        )

        with col1:

            st.image(
                image,
                width=100
            )

        with col2:

            st.write(
                f"**{file.name}**"
            )

            st.caption(
                f"{image.width} × {image.height} px"
            )

        with col3:

            copies = st.number_input(
                "عدد النسخ",
                min_value=1,
                max_value=100,
                value=6,
                key=f"copies_{index}"
            )

        image_items.append({
            "image": image,
            "name": file.name,
            "copies": copies
        })

        total_copies += copies

        st.divider()

    # ======================================
    # ملخص
    # ======================================

    layout = calculate_layout(
        photo_w,
        photo_h,
        columns,
        gap,
        0.5
    )

    if layout:

        pages = math.ceil(
            total_copies
            /
            layout["per_page"]
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "📸 إجمالي النسخ",
                total_copies
            )

        with c2:
            st.metric(
                "🖼️ صور بالصفحة",
                layout["per_page"]
            )

        with c3:
            st.metric(
                "📄 عدد صفحات A4",
                pages
            )

        st.info(
            f"القالب الحالي: "
            f"{layout['columns']} صور بالسطر × "
            f"{layout['rows']} أسطر"
        )

    # ======================================
    # إنشاء PDF
    # ======================================

    st.divider()

    if st.button(
        "🖨️ إنشاء PDF للطباعة",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "جاري ترتيب الصور وإنشاء PDF..."
        ):

            pdf, pages = create_pdf(
                image_items,
                photo_w,
                photo_h,
                columns,
                gap,
                0.5
            )

        if pdf:

            st.success(
                f"✅ تم إنشاء PDF بنجاح — {pages} صفحة"
            )

            st.download_button(
                "📥 تحميل PDF الجاهز للطباعة",
                data=pdf,
                file_name="PhotoPrint_A4.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

        else:

            st.error(
                "❌ لا يمكن وضع هذا المقاس داخل A4. "
                "اختار مقاسًا أصغر."
            )
