import streamlit as st
import fitz
import pytesseract
from PIL import Image, ImageOps, ImageFilter
import io
import re
import unicodedata
from rapidfuzz import fuzz
from collections import defaultdict

# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="نظام مطابقة المستندات",
    page_icon="📄",
    layout="wide"
)

st.title("📄 نظام مطابقة المستندات")
st.caption("رفع عدة مستندات • قراءة عربية/إنجليزية • استخراج المعلومات • مقارنة ذكية")

# =========================================================
# إعدادات
# =========================================================

OCR_LANG = "ara+eng"

DATE_REGEX = re.compile(
    r"""
    (?:
        [0-9٠-٩]{1,4}
        \s*[/\-\.]
        [0-9٠-٩]{1,2}
        \s*[/\-\.]
        [0-9٠-٩]{2,4}
    )
    """,
    re.VERBOSE
)

PHONE_REGEX = re.compile(
    r"(?:\+?964|0)?[\s\-()]*7[0-9٠-٩]{8,10}"
)

NUMBER_REGEX = re.compile(
    r"\b[0-9٠-٩]{4,20}\b"
)

# =========================================================
# توحيد الأرقام العربية
# =========================================================

def normalize_digits(text):
    if not text:
        return ""

    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"

    table = str.maketrans(
        arabic_digits,
        english_digits
    )

    return text.translate(table)


# =========================================================
# تنظيف النص العربي
# =========================================================

def normalize_text(text):
    if text is None:
        return ""

    text = str(text)

    text = normalize_digits(text)

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # إزالة التشكيل
    text = "".join(
        ch
        for ch in text
        if unicodedata.category(ch) != "Mn"
    )

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[|]+", " ", text)

    return text.strip().lower()


# =========================================================
# توحيد التاريخ
# =========================================================

def normalize_date(value):
    if not value:
        return ""

    value = normalize_digits(value)

    match = re.search(
        r"(\d{1,4})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})",
        value
    )

    if not match:
        return normalize_text(value)

    a, b, c = match.groups()

    # إذا السنة أولاً
    if len(a) == 4:
        year = a
        month = b.zfill(2)
        day = c.zfill(2)

    else:
        day = a.zfill(2)
        month = b.zfill(2)
        year = c

        if len(year) == 2:
            year = "20" + year

    return f"{year}-{month}-{day}"


# =========================================================
# تنظيف رقم
# =========================================================

def normalize_number(value):
    if not value:
        return ""

    value = normalize_digits(value)

    return re.sub(
        r"[^0-9]",
        "",
        value
    )


# =========================================================
# تحسين صورة OCR
# =========================================================

def preprocess_image(image):
    image = image.convert("RGB")

    # تكبير الصورة
    width, height = image.size

    if width < 1600:
        scale = 1600 / width
        image = image.resize(
            (
                int(width * scale),
                int(height * scale)
            )
        )

    # رمادي
    gray = ImageOps.grayscale(image)

    # تحسين التباين
    gray = ImageOps.autocontrast(gray)

    # إزالة بعض الضوضاء
    gray = gray.filter(
        ImageFilter.SHARPEN
    )

    return gray


# =========================================================
# OCR صورة
# =========================================================

def ocr_image(image):
    processed = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed,
        lang=OCR_LANG,
        config="--psm 6"
    )

    return text


# =========================================================
# قراءة PDF
# =========================================================

def read_pdf(data):

    pages = []

    pdf = fitz.open(
        stream=data,
        filetype="pdf"
    )

    for page_index, page in enumerate(pdf):

        page_number = page_index + 1

        native_text = page.get_text().strip()

        if native_text:
            pages.append({
                "page": page_number,
                "text": native_text
            })

        else:
            pix = page.get_pixmap(
                matrix=fitz.Matrix(
                    2.5,
                    2.5
                ),
                alpha=False
            )

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            text = ocr_image(image)

            pages.append({
                "page": page_number,
                "text": text
            })

    return pages


# =========================================================
# قراءة أي ملف
# =========================================================

def read_document(file):

    data = file.getvalue()

    if file.type == "application/pdf":

        pages = read_pdf(data)

    else:

        image = Image.open(
            io.BytesIO(data)
        )

        text = ocr_image(image)

        pages = [{
            "page": 1,
            "text": text
        }]

    return pages


# =========================================================
# استخراج التواريخ
# =========================================================

def extract_dates(text):

    dates = DATE_REGEX.findall(text)

    return list(
        dict.fromkeys(
            normalize_date(d)
            for d in dates
        )
    )


# =========================================================
# استخراج أرقام
# =========================================================

def extract_numbers(text):

    text = normalize_digits(text)

    numbers = NUMBER_REGEX.findall(
        text
    )

    return list(
        dict.fromkeys(numbers)
    )


# =========================================================
# استخراج الهاتف
# =========================================================

def extract_phones(text):

    phones = PHONE_REGEX.findall(
        normalize_digits(text)
    )

    return list(
        dict.fromkeys(
            normalize_number(p)
            for p in phones
        )
    )


# =========================================================
# البحث المرن عن حقل
# =========================================================

def find_labeled_value(
    text,
    labels,
    max_length=100
):

    if not text:
        return ""

    label_pattern = "|".join(
        re.escape(x)
        for x in labels
    )

    pattern = (
        rf"(?:{label_pattern})"
        rf"\s*[:：\-]?\s*"
        rf"([^\n\r]{{2,{max_length}}})"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if not match:
        return ""

    value = match.group(1).strip()

    # قص أي حقل تالٍ إذا دخل بالنتيجة
    value = re.split(
        r"\s{2,}(?:الاسم|اسم|العنوان|التاريخ|الجنسية|الهاتف|المبلغ|رقم)",
        value,
        flags=re.IGNORECASE
    )[0]

    return value.strip(" :-")


# =========================================================
# استخراج اسم محتمل
# =========================================================

def extract_name(text):

    labels = [
        "الاسم",
        "اسم الشخص",
        "اسم المواطن",
        "اسم صاحب",
        "full name",
        "name"
    ]

    value = find_labeled_value(
        text,
        labels,
        80
    )

    if value:
        return value

    return ""


# =========================================================
# استخراج المعلومات
# =========================================================

def extract_information(pages):

    full_text = "\n".join(
        p["text"]
        for p in pages
    )

    information = {}

    # -------------------------
    # الاسم
    # -------------------------

    name = extract_name(
        full_text
    )

    if name:
        information["الاسم"] = name

    # -------------------------
    # الأب
    # -------------------------

    father = find_labeled_value(
        full_text,
        [
            "اسم الأب",
            "الأب",
            "الاب",
            "father"
        ],
        60
    )

    if father:
        information["اسم الأب"] = father

    # -------------------------
    # الجد
    # -------------------------

    grandfather = find_labeled_value(
        full_text,
        [
            "اسم الجد",
            "الجد",
            "grandfather"
        ],
        60
    )

    if grandfather:
        information["اسم الجد"] = grandfather

    # -------------------------
    # الأم
    # -------------------------

    mother = find_labeled_value(
        full_text,
        [
            "اسم الأم",
            "الأم",
            "الام",
            "mother"
        ],
        60
    )

    if mother:
        information["اسم الأم"] = mother

    # -------------------------
    # الجنسية
    # -------------------------

    nationality = find_labeled_value(
        full_text,
        [
            "الجنسية",
            "الجنسية العراقية",
            "nationality"
        ],
        40
    )

    if nationality:
        information["الجنسية"] = nationality

    # -------------------------
    # العنوان
    # -------------------------

    address = find_labeled_value(
        full_text,
        [
            "العنوان",
            "عنوان السكن",
            "السكن",
            "address"
        ],
        150
    )

    if address:
        information["العنوان"] = address

    # -------------------------
    # الهاتف
    # -------------------------

    phones = extract_phones(
        full_text
    )

    if phones:
        information["الهاتف"] = phones

    # -------------------------
    # التواريخ
    # -------------------------

    dates = extract_dates(
        full_text
    )

    if dates:
        information["التاريخ"] = dates

    # -------------------------
    # الأرقام
    # -------------------------

    numbers = extract_numbers(
        full_text
    )

    if numbers:
        information["الأرقام"] = numbers

    # -------------------------
    # المبلغ
    # -------------------------

    amount = find_labeled_value(
        full_text,
        [
            "المبلغ",
            "القيمة",
            "المبلغ الكلي",
            "total",
            "amount"
        ],
        50
    )

    if amount:
        information["المبلغ"] = amount

    # -------------------------
    # رقم المستند
    # -------------------------

    document_number = find_labeled_value(
        full_text,
        [
            "رقم المستند",
            "رقم الوثيقة",
            "رقم المعاملة",
            "رقم الطلب",
            "document number"
        ],
        50
    )

    if document_number:
        information["رقم المستند"] = document_number

    return information


# =========================================================
# قيمة للمقارنة
# =========================================================

def value_to_string(value):

    if isinstance(value, list):
        return " | ".join(
            str(x)
            for x in value
        )

    return str(value)


# =========================================================
# مقارنة قيمتين
# =========================================================

def compare_values(
    field,
    value1,
    value2
):

    if field == "التاريخ":

        d1 = normalize_date(
            value_to_string(value1)
        )

        d2 = normalize_date(
            value_to_string(value2)
        )

        if d1 and d2 and d1 == d2:
            return 100

    if field in [
        "الهاتف",
        "رقم المستند"
    ]:

        n1 = normalize_number(
            value_to_string(value1)
        )

        n2 = normalize_number(
            value_to_string(value2)
        )

        if n1 and n2 and n1 == n2:
            return 100

    a = normalize_text(
        value_to_string(value1)
    )

    b = normalize_text(
        value_to_string(value2)
    )

    if not a or not b:
        return 0

    return fuzz.token_set_ratio(
        a,
        b
    )


# =========================================================
# تحديد الحالة
# =========================================================

def status(score):

    if score >= 92:
        return (
            "🟢 مطابق",
            "#d4edda"
        )

    if score >= 65:
        return (
            "🟡 يحتاج مراجعة",
            "#fff3cd"
        )

    return (
        "🔴 مختلف",
        "#f8d7da"
    )


# =========================================================
# رفع الملفات
# =========================================================

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


if files:

    st.success(
        f"تم رفع {len(files)} مستند/مستندات ✅"
    )

    # =====================================================
    # تحليل المستندات
    # =====================================================

    if st.button(
        "🧠 تحليل المستندات",
        type="primary"
    ):

        documents = []

        progress = st.progress(0)

        for index, file in enumerate(files):

            with st.spinner(
                f"جاري قراءة {file.name}..."
            ):

                pages = read_document(
                    file
                )

                information = extract_information(
                    pages
                )

                documents.append({
                    "name": file.name,
                    "pages": pages,
                    "information": information
                })

            progress.progress(
                (index + 1) / len(files)
            )

        st.session_state["documents"] = documents

        st.success(
            "تم تحليل المستندات بنجاح ✅"
        )


# =========================================================
# عرض النتائج إذا موجودة
# =========================================================

if "documents" in st.session_state:

    documents = st.session_state[
        "documents"
    ]

    names = [
        d["name"]
        for d in documents
    ]

    st.divider()

    st.header(
        "🔎 اختر المستندين للمقارنة"
    )

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
            index=1 if len(names) > 1 else 0
        )

    first = next(
        d for d in documents
        if d["name"] == first_name
    )

    second = next(
        d for d in documents
        if d["name"] == second_name
    )

    # =====================================================
    # عرض المستندات
    # =====================================================

    st.divider()

    st.header(
        "📄 المستندات"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.subheader(
            f"1️⃣ {first['name']}"
        )

        st.write(
            f"عدد الصفحات: {len(first['pages'])}"
        )

    with c2:

        st.subheader(
            f"2️⃣ {second['name']}"
        )

        st.write(
            f"عدد الصفحات: {len(second['pages'])}"
        )

    # =====================================================
    # المقارنة
    # =====================================================

    st.divider()

    st.header(
        "📊 المقارنة التفصيلية"
    )

    info1 = first["information"]
    info2 = second["information"]

    fields = sorted(
        set(info1.keys())
        |
        set(info2.keys())
    )

    if not fields:

        st.error(
            "لم يتم استخراج معلومات واضحة من المستندين."
        )

    else:

        matched = 0
        review = 0
        different = 0

        results = []

        for field in fields:

            value1 = info1.get(
                field,
                "غير موجود"
            )

            value2 = info2.get(
                field,
                "غير موجود"
            )

            score = compare_values(
                field,
                value1,
                value2
            )

            label, color = status(
                score
            )

            if score >= 92:
                matched += 1

            elif score >= 65:
                review += 1

            else:
                different += 1

            results.append({
                "field": field,
                "value1": value1,
                "value2": value2,
                "score": score,
                "label": label,
                "color": color
            })

        # =================================================
        # ملخص
        # =================================================

        total = len(results)

        overall = (
            matched / total * 100
            if total
            else 0
        )

        a, b, c, d = st.columns(4)

        with a:
            st.metric(
                "نسبة المطابقة",
                f"{overall:.0f}%"
            )

        with b:
            st.metric(
                "🟢 مطابق",
                matched
            )

        with c:
            st.metric(
                "🟡 مراجعة",
                review
            )

        with d:
            st.metric(
                "🔴 مختلف",
                different
            )

        st.divider()

        # =================================================
        # جدول المقارنة جنباً إلى جنب
        # =================================================

        for result in results:

            field = result["field"]

            value1 = value_to_string(
                result["value1"]
            )

            value2 = value_to_string(
                result["value2"]
            )

            score = result["score"]

            label = result["label"]

            color = result["color"]

            st.markdown(
                f"""
                <div style="
                    border:2px solid #dddddd;
                    border-radius:12px;
                    padding:15px;
                    margin-bottom:15px;
                ">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    margin-bottom:10px;
                ">

                <h3 style="margin:0;">
                    {field}
                </h3>

                <span style="
                    background:{color};
                    padding:6px 12px;
                    border-radius:20px;
                    font-weight:bold;
                ">
                    {label} — {score:.0f}%
                </span>

                </div>

                <div style="
                    display:grid;
                    grid-template-columns:1fr 1fr;
                    gap:15px;
                ">

                <div style="
                    background:#f5f5f5;
                    border-radius:10px;
                    padding:15px;
                ">

                <b>📄 المستند الأول</b>

                <div style="
                    margin-top:8px;
                    font-size:17px;
                ">
                    {value1}
                </div>

                </div>

                <div style="
                    background:{color};
                    border-radius:10px;
                    padding:15px;
                ">

                <b>📄 المستند الثاني</b>

                <div style="
                    margin-top:8px;
                    font-size:17px;
                ">
                    {value2}
                </div>

                </div>

                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    # =====================================================
    # النص الخام
    # =====================================================

    with st.expander(
        "🔍 عرض النص الخام للمراجعة"
    ):

        for document in [
            first,
            second
        ]:

            st.subheader(
                document["name"]
            )

            for page in document["pages"]:

                st.markdown(
                    f"**صفحة {page['page']}**"
                )

                st.text(
                    page["text"][:12000]
                )

                st.divider()
