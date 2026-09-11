import streamlit as st
import fitz
import pytesseract
from PIL import Image
import io

st.set_page_config(
    page_title="مطابقة المستندات",
    page_icon="📄",
    layout="centered"
)

st.title("📄 نظام مطابقة المستندات")
st.write("ارفع عدة صور أو ملفات PDF، وسيتم قراءة محتواها.")

def read_image(image):
    return pytesseract.image_to_string(
        image,
        lang="ara+eng"
    )

def read_pdf(file_data):
    text = ""

    pdf = fitz.open(
        stream=file_data,
        filetype="pdf"
    )

    for page_number, page in enumerate(pdf):

        # أولاً نحاول قراءة النص الموجود داخل PDF
        page_text = page.get_text()

        if page_text.strip():
            text += page_text + "\n"

        else:
            # إذا كان PDF عبارة عن صورة، نستخدم OCR
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


def extract_text(file):

    file_data = file.read()

    if file.type == "application/pdf":
        return read_pdf(file_data)

    else:
        image = Image.open(
            io.BytesIO(file_data)
        )

        return read_image(image)


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

    if st.button(
        "📖 قراءة المستندات",
        type="primary"
    ):

        st.info(
            "جاري قراءة المستندات، انتظر قليلاً..."
        )

        for number, file in enumerate(
            files,
            start=1
        ):

            st.divider()

            st.subheader(
                f"📄 المستند {number}: {file.name}"
            )

            try:

                text = extract_text(file)

                if text.strip():

                    st.success(
                        "تم استخراج النص بنجاح ✅"
                    )

                    with st.expander(
                        "عرض النص المستخرج"
                    ):
                        st.text(
                            text[:10000]
                        )

                else:

                    st.warning(
                        "لم يتم العثور على نص في هذا المستند."
                    )

            except Exception as e:

                st.error(
                    f"حدث خطأ أثناء قراءة المستند: {e}"
                )

else:

    st.info(
        "ارفع مستندين أو أكثر للبدء."
    )
