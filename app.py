import streamlit as st
import fitz
import pytesseract
from PIL import Image
from rapidfuzz import fuzz
import re
import io

st.set_page_config(
    page_title="مطابقة المستندات",
    page_icon="📄",
    layout="centered"
)

st.title("📄 مطابقة المستندات")
st.write("ارفع المستندين، وسيتم استخراج المعلومات المهمة ومقارنتها.")

def extract_text(file):
    data = file.read()

    if file.type == "application/pdf":
        text = ""

        pdf = fitz.open(stream=data, filetype="pdf")

        for page in pdf:
            page_text = page.get_text()

            if page_text.strip():
                text += page_text + "\n"
            else:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                text += pytesseract.image_to_string(
                    image,
                    lang="ara+eng"
                ) + "\n"

        return text

    else:
        image = Image.open(io.BytesIO(data))
        return pytesseract.image_to_string(
            image,
            lang="ara+eng"
        )


def normalize(text):
    text = text.strip().lower()

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

    text = re.sub(r"\s+", " ", text)

    return text


def compare_values(value1, value2):
    if not value1 or not value2:
        return None

    score = fuzz.ratio(
        normalize(value1),
        normalize(value2)
    )

    return score


file1 = st.file_uploader(
    "📄 المستند الأول",
    type=["png", "jpg", "jpeg", "pdf"],
    key="file1"
)

file2 = st.file_uploader(
    "🪪 المستند الثاني",
    type=["png", "jpg", "jpeg", "pdf"],
    key="file2"
)

if file1 and file2:

    st.success("تم رفع المستندين بنجاح ✅")

    if st.button("🔍 مطابقة المستندات"):

        with st.spinner("جاري قراءة المستندات..."):

            text1 = extract_text(file1)
            text2 = extract_text(file2)

        st.subheader("📋 النص المستخرج")

        with st.expander("عرض نص المستند الأول"):
            st.text(text1[:5000])

        with st.expander("عرض نص المستند الثاني"):
            st.text(text2[:5000])

        st.subheader("🔍 نتيجة المطابقة")

        # مقارنة أولية للنص الكامل
        score = fuzz.token_set_ratio(
            normalize(text1),
            normalize(text2)
        )

        st.metric(
            "نسبة التشابه الأولية",
            f"{score:.0f}%"
        )

        if score >= 80:
            st.success("🟢 يوجد تشابه كبير بين المستندين")
        elif score >= 50:
            st.warning("🟡 يوجد تشابه جزئي ويحتاج إلى مراجعة")
        else:
            st.error("🔴 المستندات مختلفة بشكل كبير")

        st.info(
            "هذه نسخة أولية. في المرحلة التالية سنجعل البرنامج "
            "يستخرج الاسم ورقم البطاقة واسم الأب والجد والأم والجنسية "
            "ويقارن كل معلومة بشكل مستقل."
        )

