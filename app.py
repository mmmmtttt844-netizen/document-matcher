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
    layout="centered"
)

st.title("📄 نظام مطابقة المستندات")
st.write("ارفع عدة صور أو ملفات PDF، وسيتم استخراج ومقارنة المعلومات المهمة.")

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

def read_pdf(file_data):

    text = ""

    pdf = fitz.open(
        stream=file_data,
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

def clean_text(text):

    text = text.lower()

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
        text = text.replace(old, new)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================
# البحث عن رقم
# =========================

def find_numbers(text):

    numbers = re.findall(
        r"\d{4,}",
        text
    )

    return list(dict.fromkeys(numbers))


# =========================
# استخراج معلومات أولية
# =========================

def extract_information(text):

    information = {}

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # الأرقام المهمة
    numbers = find_numbers(text)

    if numbers:
        information["الأرقام"] = numbers

    # البحث عن بعض الحقول المعروفة
    patterns = {

        "الاسم": r"(?:الاسم|اسم)\s*[:\-]?\s*(.{3,60})",

        "اسم الأب": r"(?:اسم الأب|الاب)\s*[:\-]?\s*(.{3,50})",

        "اسم الأم": r"(?:اسم الأم|الام)\s*[:\-]?\s*(.{3,50})",

        "الجنسية": r"(?:الجنسية)\s*[:\-]?\s*(.{2,30})",

        "العنوان": r"(?:العنوان)\s*[:\-]?\s*(.{3,100})",

        "التاريخ": r"(?:التاريخ|تاريخ)\s*[:\-]?\s*(.{5,30})",

        "الهاتف": r"(?:الهاتف|موبايل|الموبايل|رقم الهاتف)\s*[:\-]?\s*([0-9٠-٩\-\+\s]{7,20})",

        "المبلغ": r"(?:المبلغ|القيمة)\s*[:\-]?\s*([0-9٠-٩,\.\s]+)"
    }

    for field, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            information[field] = value

    return information


# =========================
# مقارنة قيمتين
# =========================

def compare_values(value1, value2):

    value1 = clean_text(str(value1))
    value2 = clean_text(str(value2))

    if not value1 or not value2:
        return 0

    return fuzz.token_set_ratio(
        value1,
        value2
    )


# =========================
# رفع الملفات
# =========================

files = st.file_uploader(
    "📂 اختر المستندات",
    type=[
        "png",
        "jpg",
        "jpeg",
        "pdf"
    ],
    accept_multiple_files=True
)


if files:

    st.success(
        f"تم رفع {len(files)} مستند/مستندات بنجاح ✅"
    )

    if len(files) < 2:

        st.warning(
            "ارفع مستندين على الأقل للمطابقة."
        )

    else:

        if st.button(
            "🔍 استخراج المعلومات والمطابقة",
            type="primary"
        ):

            documents = []

            progress = st.progress(0)

            for index, file in enumerate(files):

                with st.spinner(
                    f"جاري قراءة {file.name}..."
                ):

                    text = extract_text(file)

                    info = extract_information(
                        text
                    )

                    documents.append({
                        "name": file.name,
                        "text": text,
                        "info": info
                    })

                progress.progress(
                    (index + 1) / len(files)
                )


            st.success(
                "تم استخراج المعلومات ✅"
            )


            # =========================
            # عرض المعلومات
            # =========================

            for document in documents:

                st.divider()

                st.subheader(
                    f"📄 {document['name']}"
                )

                info = document["info"]

                if not info:

                    st.warning(
                        "لم يتم العثور على حقول واضحة."
                    )

                else:

                    for field, value in info.items():

                        if isinstance(value, list):

                            st.write(
                                f"**{field}:** "
                                + ", ".join(value)
                            )

                        else:

                            st.write(
                                f"**{field}:** {value}"
                            )


            # =========================
            # المطابقة
            # =========================

            st.divider()

            st.header(
                "🔍 نتائج المطابقة"
            )

            base = documents[0]

            for other in documents[1:]:

                st.subheader(
                    f"مقارنة: {base['name']} ↔ {other['name']}"
                )

                fields = set(
                    base["info"].keys()
                ) & set(
                    other["info"].keys()
                )

                if not fields:

                    st.warning(
                        "لم نجد حقول مشتركة واضحة للمقارنة."
                    )

                    continue

                matched = 0
                total = 0

                for field in fields:

                    value1 = base["info"][field]
                    value2 = other["info"][field]

                    if isinstance(value1, list):

                        value1 = " ".join(
                            map(str, value1)
                        )

                    if isinstance(value2, list):

                        value2 = " ".join(
                            map(str, value2)
                        )

                    score = compare_values(
                        value1,
                        value2
                    )

                    total += 1

                    if score >= 90:

                        matched += 1

                        st.success(
                            f"🟢 {field}: مطابق "
                            f"({score:.0f}%)"
                        )

                    elif score >= 60:

                        st.warning(
                            f"🟡 {field}: يحتاج مراجعة "
                            f"({score:.0f}%)"
                        )

                    else:

                        st.error(
                            f"🔴 {field}: مختلف "
                            f"({score:.0f}%)"
                        )

                    st.caption(
                        f"المستند الأول: {value1}"
                    )

                    st.caption(
                        f"المستند الثاني: {value2}"
                    )

                if total > 0:

                    final_score = (
                        matched / total
                    ) * 100

                    st.metric(
                        "نسبة المطابقة",
                        f"{final_score:.0f}%"
                    )
