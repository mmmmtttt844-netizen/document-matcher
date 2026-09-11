import streamlit as st

st.set_page_config(
    page_title="مطابقة المستندات",
    page_icon="📄",
    layout="centered"
)

st.title("📄 نظام مطابقة المستندات")
st.write("ارفع مستندًا واحدًا أو عدة مستندات للمقارنة.")

files = st.file_uploader(
    "📂 اختر المستندات",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

if files:
    st.success(f"تم رفع {len(files)} مستند/مستندات بنجاح ✅")

    st.subheader("📋 المستندات المرفوعة")

    for number, file in enumerate(files, start=1):
        st.write(f"**{number}. {file.name}**")

    if len(files) >= 2:
        st.divider()

        if st.button("🔍 بدء المطابقة", type="primary"):
            st.info("تم استلام المستندات. سنبدأ الآن باستخراج المعلومات المهمة.")

    else:
        st.warning("ارفع مستندين على الأقل حتى نتمكن من المطابقة.")
