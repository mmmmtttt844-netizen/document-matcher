import streamlit as st

st.set_page_config(
    page_title="مطابقة المستندات",
    page_icon="📄",
    layout="centered"
)

st.title("📄 مطابقة المستندات")
st.write("ارفع المستندين حتى نجهز للمطابقة.")

st.subheader("المستند الأول")
file1 = st.file_uploader(
    "ارفع صورة أو PDF",
    type=["png", "jpg", "jpeg", "pdf"],
    key="file1"
)

st.subheader("المستند الثاني")
file2 = st.file_uploader(
    "ارفع صورة أو PDF",
    type=["png", "jpg", "jpeg", "pdf"],
    key="file2"
)

if file1 and file2:
    st.success("تم رفع المستندين بنجاح ✅")

    if st.button("🔍 مطابقة المستندات"):
        st.info("تم استلام المستندات. مرحلة استخراج المعلومات والمطابقة قيد الإعداد.")

        st.write("### المعلومات التي سنطابقها:")
        fields = [
            "الاسم",
            "رقم البطاقة الوطنية",
            "الجنسية",
            "اسم الأب",
            "اسم الجد",
            "اسم الأم"
        ]

        for field in fields:
            st.write(f"⬜ {field}")
