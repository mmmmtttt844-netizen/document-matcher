import streamlit as st
import fitz
import pytesseract
from PIL import Image
import io
import re
from rapidfuzz import fuzz

st.set_page_config(
    page_title="مطابقة المستندات",
    page_icon="📄",
    layout="wide"
)

st.title("📄 مطابقة المستندات")
st.write("ارفع المستندات وشاهد المعلومات جنبًا إلى جنب.")

# =========================
# قراءة الصور
# =========================

def read_image(image):
    return pytesseract.image_to_string(
        image,
        lang="ara+eng"
    )


# =========================
# قراءة PDF
# =========================

def read_pdf(data):
    text = ""

    pdf = fitz.open(
        stream=data,
        filetype="pdf"
    )

    for page in pdf:

        page_text = page.get_text()

        if page_text.strip():
            text += page_text + "\n"

        else:
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            text += read_image(image) + "\n"

    return text


# =========================
# استخراج النص
# =========================

def extract_text(file):

    data = file.read()

    if file.type == "application/pdf":
        return read_pdf(data)

    image = Image.open(
        io.BytesIO(data)
    )

    return read_image(image)


# =========================
# تنظيف النص
# =========================

def clean(value):

    if value is None:
        return ""

    value = str(value).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي"
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# =========================
# استخراج الحقول
# =========================

def extract_information(text):

    info = {}

    patterns = {

        "الاسم":
        r"(?:الاسم|اسم)\s*[:\-]?\s*(.{3,60})",

        "اسم الأب":
        r"(?:اسم الأب|الاب)\s*[:\-]?\s*(.{3,50})",

        "اسم الجد":
        r"(?:اسم الجد|الجد)\s*[:\-]?\s*(.{3,50})",

        "اسم الأم":
        r"(?:اسم الأم|الام)\s*[:\-]?\s*(.{3,50})",

        "الجنسية":
        r"(?:الجنسية)\s*[:\-]?\s*(.{2,30})",

        "العنوان":
        r"(?:العنوان)\s*[:\-]?\s*(.{3,100})",

        "التاريخ":
        r"(?:التاريخ|تاريخ)\s*[:\-]?\s*(.{5,30})",

        "الهاتف":
        r"(?:الهاتف|الموبايل|موبايل|رقم الهاتف)\s*[:\-]?\s*([0-9٠-٩\-\+\s]{7,20})",

        "المبلغ":
        r"(?:المبلغ|القيمة)\s*[:\-]?\s*([0-9٠-٩,\.\s]+)",

        "رقم المستند":
        r"(?:رقم المستند|رقم الوثيقة|رقم المعاملة)\s*[:\-]?\s*([0-9٠-٩A-Za-z\-\/]+)"
    }

    for field, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            info[field] = value

    return info


# =========================
# رفع المستندات
# =========================

files = st.file_uploader(
    "📂 ارفع المستندات",
    type=[
        "png",
        "jpg",
        "jpeg",
        "pdf"
    ],
    accept_multiple_files=True
)


if not files:

    st.info(
        "ارفع مستندين أو أكثر للبدء."
    )

else:

    st.success(
        f"تم رفع {len(files)} مستند/مستندات ✅"
    )

    if len(files) < 2:

        st.warning(
            "تحتاج إلى مستندين على الأقل."
        )

    else:

        if st.button(
            "🔍 تحليل ومقارنة المستندات",
            type="primary"
        ):

            documents = []

            progress = st.progress(0)

            for index, file in enumerate(files):

                with st.spinner(
                    f"جاري تحليل {file.name}..."
                ):

                    text = extract_text(file)

                    info = extract_information(
                        text
                    )

                    documents.append({
                        "name": file.name,
                        "info": info
                    })

                progress.progress(
                    (index + 1) / len(files)
                )

            st.success(
                "تم تحليل المستندات ✅"
            )

            # ==================================
            # اختيار مستندين للمقارنة
            # ==================================

            st.header("🔎 اختيار المستندات")

            names = [
                doc["name"]
                for doc in documents
            ]

            col1, col2 = st.columns(2)

            with col1:

                first_name = st.selectbox(
                    "المستند الأول",
                    names,
                    index=0
                )

            with col2:

                second_name = st.selectbox(
                    "المستند الثاني",
                    names,
                    index=1
                )

            first = next(
                doc for doc in documents
                if doc["name"] == first_name
            )

            second = next(
                doc for doc in documents
                if doc["name"] == second_name
            )

            # ==================================
            # جدول المقارنة
            # ==================================

            st.header("📊 مقارنة المعلومات")

            fields = list(
                set(first["info"].keys())
                |
                set(second["info"].keys())
            )

            if not fields:

                st.error(
                    "لم يتم العثور على معلومات قابلة للمقارنة."
                )

            else:

                for field in fields:

                    value1 = first["info"].get(
                        field,
                        "غير موجود"
                    )

                    value2 = second["info"].get(
                        field,
                        "غير موجود"
                    )

                    score = fuzz.token_set_ratio(
                        clean(value1),
                        clean(value2)
                    )

                    if score >= 90:

                        color = "#d4edda"
                        icon = "🟢"

                    elif score >= 60:

                        color = "#fff3cd"
                        icon = "🟡"

                    else:

                        color = "#f8d7da"
                        icon = "🔴"

                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #ddd;
                            border-radius:10px;
                            padding:12px;
                            margin-bottom:10px;
                        ">

                        <h4>{icon} {field}</h4>

                        <div style="
                            display:grid;
                            grid-template-columns:1fr 1fr;
                            gap:10px;
                        ">

                        <div style="
                            background:#f5f5f5;
                            padding:12px;
                            border-radius:8px;
                        ">
                        <b>المستند الأول</b><br>
                        {value1}
                        </div>

                        <div style="
                            background:{color};
                            padding:12px;
                            border-radius:8px;
                        ">
                        <b>المستند الثاني</b><br>
                        {value2}
                        </div>

                        </div>

                        <p>
                        <b>نسبة التشابه:</b>
                        {score:.0f}%
                        </p>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )
