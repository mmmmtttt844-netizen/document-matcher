import io
import math
import streamlit as st
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from docx import Document
from docx.shared import Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="محمد هوبي | PhotoPrint",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# CSS - التصميم
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            linear-gradient(
                180deg,
                #f7faff 0%,
                #ffffff 45%,
                #f5f8fc 100%
            );
    }

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: #102a43;
        margin-top: 10px;
        margin-bottom: 0;
    }

    .subtitle {
        text-align: center;
        color: #627d98;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .brand {
        text-align: center;
        font-size: 15px;
        color: #1677ff;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .info-card {
        background: white;
        border-radius: 18px;
        padding: 20px;
        border: 1px solid #e6edf5;
        box-shadow: 0 8px 25px rgba(16, 42, 67, 0.06);
        margin-bottom: 15px;
    }

    .footer {
        text-align: center;
        color: #829ab1;
        font-size: 13px;
        padding: 30px 0 10px 0;
    }

    div.stButton > button {
        border-radius: 12px;
        min-height: 48px;
        font-weight: 700;
        border: none;
        background: linear-gradient(
            135deg,
            #1677ff,
            #0052cc
        );
        color: white;
    }

    div.stDownloadButton > button {
        border-radius: 12px;
        min-height: 48px;
        font-weight: 700;
    }

    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 18px;
        padding: 10px;
        border: 1px solid #dce6f2;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# رأس الموقع
# =========================================================

st.markdown(
    '<div class="brand">📸 PHOTO PRINT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-title">محمد هوبي</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'تجهيز صور 3×4 للطباعة — Word و PDF'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# إعدادات القالب الثابت
# =========================================================

PHOTO_WIDTH_CM = 3.0
PHOTO_HEIGHT_CM = 4.0

COLUMNS = 6

A4_WIDTH_CM = 21.0
A4_HEIGHT_CM = 29.7

TOP_MARGIN_CM = 0.5
LEFT_MARGIN_CM = 0.5

GAP_CM = 0.15

CM_TO_PT = 28.3464567


# =========================================================
# وظائف مساعدة
# =========================================================

def cm_to_pt(value):
    return value * CM_TO_PT


def crop_to_3x4(image):
    """
    قص الصورة إلى نسبة 3:4 من المنتصف.
    """

    image = image.convert("RGB")

    target_ratio = 3 / 4
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

    elif current_ratio < target_ratio:

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


def image_to_jpeg_buffer(image):
    """
    تحويل الصورة إلى JPEG في الذاكرة.
    """

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=95,
        optimize=True
    )

    buffer.seek(0)

    return buffer


def calculate_rows_per_page():
    """
    حساب عدد الأسطر التي تدخل في ورقة A4.
    """

    usable_height = (
        A4_HEIGHT_CM
        - TOP_MARGIN_CM
        - 0.5
    )

    row_height = (
        PHOTO_HEIGHT_CM
        + GAP_CM
    )

    return max(
        1,
        int(
            (
                usable_height
                + GAP_CM
            )
            /
            row_height
        )
    )


# =========================================================
# إنشاء PDF
# =========================================================

def create_pdf(image_items):

    rows_per_page = calculate_rows_per_page()

    photos_per_page = (
        COLUMNS * rows_per_page
    )

    total_photos = sum(
        item["copies"]
        for item in image_items
    )

    total_pages = math.ceil(
        total_photos / photos_per_page
    )

    output = io.BytesIO()

    pdf = canvas.Canvas(
        output,
        pagesize=A4
    )

    page_width, page_height = A4

    photo_width = cm_to_pt(
        PHOTO_WIDTH_CM
    )

    photo_height = cm_to_pt(
        PHOTO_HEIGHT_CM
    )

    gap = cm_to_pt(
        GAP_CM
    )

    left_margin = cm_to_pt(
        LEFT_MARGIN_CM
    )

    top_margin = cm_to_pt(
        TOP_MARGIN_CM
    )

    # تحضير الصور
    prepared_images = []

    for item in image_items:

        cropped = crop_to_3x4(
            item["image"]
        )

        buffer = image_to_jpeg_buffer(
            cropped
        )

        reader = ImageReader(
            buffer
        )

        for _ in range(
            item["copies"]
        ):

            prepared_images.append(
                reader
            )

    # رسم الصور
    for index, reader in enumerate(
        prepared_images
    ):

        slot = index % photos_per_page

        row = slot // COLUMNS
        column = slot % COLUMNS

        x = (
            left_margin
            +
            column *
            (
                photo_width
                + gap
            )
        )

        y = (
            page_height
            -
            top_margin
            -
            photo_height
            -
            row *
            (
                photo_height
                + gap
            )
        )

        # الصورة
        pdf.drawImage(
            reader,
            x,
            y,
            width=photo_width,
            height=photo_height,
            preserveAspectRatio=False,
            mask="auto"
        )

        # علامات القص
        pdf.setStrokeColorRGB(
            0.55,
            0.55,
            0.55
        )

        pdf.setLineWidth(
            0.35
        )

        mark = 3

        # أعلى يسار
        pdf.line(
            x - mark,
            y + photo_height,
            x + 1,
            y + photo_height
        )

        pdf.line(
            x,
            y + photo_height + mark,
            x,
            y + photo_height - 1
        )

        # أعلى يمين
        pdf.line(
            x + photo_width - 1,
            y + photo_height,
            x + photo_width + mark,
            y + photo_height
        )

        pdf.line(
            x + photo_width,
            y + photo_height + mark,
            x + photo_width,
            y + photo_height - 1
        )

        # أسفل يسار
        pdf.line(
            x - mark,
            y,
            x + 1,
            y
        )

        pdf.line(
            x,
            y - mark,
            x,
            y + 1
        )

        # أسفل يمين
        pdf.line(
            x + photo_width - 1,
            y,
            x + photo_width + mark,
            y
        )

        pdf.line(
            x + photo_width,
            y - mark,
            x + photo_width,
            y + 1
        )

        # صفحة جديدة
        if (
            (index + 1)
            % photos_per_page
            == 0
        ):

            pdf.showPage()

    # إذا الصفحة الأخيرة لم تكن ممتلئة
    if (
        len(prepared_images)
        % photos_per_page
        != 0
    ):

        pdf.showPage()

    pdf.save()

    output.seek(0)

    return output, total_pages


# =========================================================
# إنشاء Word
# =========================================================

def create_word(image_items):

    document = Document()

    section = document.sections[0]

    # A4
    section.page_width = Cm(
        A4_WIDTH_CM
    )

    section.page_height = Cm(
        A4_HEIGHT_CM
    )

    # الهوامش
    section.top_margin = Cm(
        TOP_MARGIN_CM
    )

    section.bottom_margin = Cm(
        0.5
    )

    section.left_margin = Cm(
        LEFT_MARGIN_CM
    )

    section.right_margin = Cm(
        0.5
    )

    # تحضير الصور والنسخ
    prepared_images = []

    for item in image_items:

        cropped = crop_to_3x4(
            item["image"]
        )

        buffer = image_to_jpeg_buffer(
            cropped
        )

        data = buffer.getvalue()

        for _ in range(
            item["copies"]
        ):

            prepared_images.append(
                data
            )

    rows_per_page = (
        calculate_rows_per_page()
    )

    photos_per_page = (
        COLUMNS * rows_per_page
    )

    # -----------------------------------------------------
    # إنشاء صفحات Word على شكل جداول
    # -----------------------------------------------------

    current = 0

    while current < len(
        prepared_images
    ):

        page_items = prepared_images[
            current:
            current + photos_per_page
        ]

        rows = math.ceil(
            len(page_items)
            / COLUMNS
        )

        table = document.add_table(
            rows=rows,
            cols=COLUMNS
        )

        table.autofit = False

        # إزالة المسافات داخل الجدول
        table.allow_autofit = False

        position = 0

        for row in table.rows:

            row.height = Cm(
                PHOTO_HEIGHT_CM
            )

            for cell in row.cells:

                cell.width = Cm(
                    PHOTO_WIDTH_CM
                )

                cell.vertical_alignment = (
                    WD_CELL_VERTICAL_ALIGNMENT.TOP
                )

                if position < len(
                    page_items
                ):

                    paragraph = (
                        cell.paragraphs[0]
                    )

                    paragraph.alignment = (
                        WD_ALIGN_PARAGRAPH.CENTER
                    )

                    paragraph.paragraph_format.space_before = 0
                    paragraph.paragraph_format.space_after = 0

                    run = (
                        paragraph.add_run()
                    )

                    run.add_picture(
                        io.BytesIO(
                            page_items[position]
                        ),
                        width=Cm(
                            PHOTO_WIDTH_CM
                        ),
                        height=Cm(
                            PHOTO_HEIGHT_CM
                        )
                    )

                    position += 1

                else:

                    cell.text = ""

        current += photos_per_page

        # صفحة جديدة إذا بقيت صور
        if current < len(
            prepared_images
        ):

            document.add_page_break()

    output = io.BytesIO()

    document.save(
        output
    )

    output.seek(0)

    return output


# =========================================================
# رفع الصور
# =========================================================

st.markdown(
    '<div class="info-card">',
    unsafe_allow_html=True
)

st.subheader(
    "📸 اختر الصور"
)

uploaded_files = st.file_uploader(
    "تگدر تختار أكثر من صورة بنفس الوقت",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
    accept_multiple_files=True
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# =========================================================
# عرض الصور
# =========================================================

if uploaded_files:

    st.success(
        f"تم اختيار {len(uploaded_files)} صورة ✅"
    )

    st.divider()

    st.subheader(
        "🖼️ الصور وعدد النسخ"
    )

    image_items = []

    total_copies = 0

    for index, uploaded_file in enumerate(
        uploaded_files
    ):

        try:

            image = Image.open(
                uploaded_file
            ).convert("RGB")

        except Exception:

            st.error(
                f"تعذر قراءة الصورة: "
                f"{uploaded_file.name}"
            )

            continue

        col1, col2, col3 = st.columns(
            [1.2, 3, 1.5]
        )

        with col1:

            st.image(
                image,
                width=100
            )

        with col2:

            st.write(
                f"**{uploaded_file.name}**"
            )

            st.caption(
                f"{image.width} × "
                f"{image.height} px"
            )

        with col3:

            copies = st.number_input(
                "عدد النسخ",
                min_value=1,
                max_value=200,
                value=6,
                step=1,
                key=f"copies_{index}"
            )

        image_items.append(
            {
                "image": image,
                "name": uploaded_file.name,
                "copies": copies
            }
        )

        total_copies += copies

        st.divider()

    # =====================================================
    # ملخص
    # =====================================================

    rows_per_page = (
        calculate_rows_per_page()
    )

    photos_per_page = (
        COLUMNS * rows_per_page
    )

    pages = math.ceil(
        total_copies
        /
        photos_per_page
    )

    a, b, c = st.columns(3)

    with a:

        st.metric(
            "📸 عدد الصور",
            len(image_items)
        )

    with b:

        st.metric(
            "🔢 إجمالي النسخ",
            total_copies
        )

    with c:

        st.metric(
            "📄 صفحات A4",
            pages
        )

    st.info(
        f"القالب ثابت: "
        f"**6 صور بالسطر** × "
        f"**{rows_per_page} أسطر تقريبًا بالصفحة**"
    )

    # =====================================================
    # تجهيز
    # =====================================================

    st.divider()

    if st.button(
        "🖨️ تجهيز Word و PDF",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "جاري تجهيز الملفات..."
        ):

            try:

                pdf_file, pdf_pages = (
                    create_pdf(
                        image_items
                    )
                )

                word_file = (
                    create_word(
                        image_items
                    )
                )

                st.session_state[
                    "pdf_file"
                ] = pdf_file.getvalue()

                st.session_state[
                    "word_file"
                ] = word_file.getvalue()

                st.session_state[
                    "generated"
                ] = True

            except Exception as error:

                st.session_state[
                    "generated"
                ] = False

                st.error(
                    "حدث خطأ أثناء إنشاء الملفات."
                )

                st.exception(
                    error
                )

    # =====================================================
    # أزرار التحميل
    # =====================================================

    if st.session_state.get(
        "generated",
        False
    ):

        st.success(
            "✅ تم تجهيز الملفات بنجاح"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.download_button(
                "📘 تحميل Word",
                data=st.session_state[
                    "word_file"
                ],
                file_name="محمد_هوبي_PhotoPrint.docx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
                use_container_width=True
            )

        with col2:

            st.download_button(
                "📕 تحميل PDF",
                data=st.session_state[
                    "pdf_file"
                ],
                file_name="محمد_هوبي_PhotoPrint.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# =========================================================
# حقوق الموقع
# =========================================================

st.markdown(
    """
    <div class="footer">
        © 2026 محمد هوبي — جميع الحقوق محفوظة<br>
        محمد هوبي | PhotoPrint
    </div>
    """,
    unsafe_allow_html=True
)
