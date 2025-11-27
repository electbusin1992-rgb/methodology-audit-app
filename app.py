import streamlit as st
import pandas as pd
import pdfplumber
from PIL import Image
import base64
import io
import openai

st.set_page_config(page_title="نظام تدقيق المنهجية", layout="wide")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ---------------------------
# دوال مساعدة
# ---------------------------

def extract_pdf_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def preview_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df


def count_and_preview_images(files):
    if files:
        st.write(f"عدد الملفات المرفوعة: **{len(files)}**")
        for f in files:
            img = Image.open(f)
            st.image(img, width=250)
    else:
        st.warning("لم يتم رفع أي ملف.")


def generate_report(methodology_text, excel_data, images_summary):
    prompt = f"""
    أنت مدقق مالي. لديك منهجية التقييم التالية:
    {methodology_text}

    وهذه بيانات مالية:
    {excel_data}

    وهذه ملخصات صور المشاريع والحوكمة والنجوم:
    {images_summary}

    ❗ اكتب تقرير تدقيق احترافي، مختصر، واضح، جاهز للتقديم للإدارة.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500
    )

    return response.choices[0].message.content


# ---------------------------
# واجهة التطبيق
# ---------------------------

st.title("📘 نظام تدقيق المنهجية وربطها بالمدخلات")

st.write("قم برفع الملفات المطلوبة ليتم تدقيق المنهجية ومقارنتها مع المدخلات المالية والحوكمة والمشاريع.")

st.markdown("---")

# ---------------------------
# 1️⃣ ملف المنهجية PDF
# ---------------------------

st.header("1️⃣ رفع ملف المنهجية (PDF)")

methodology_file = st.file_uploader("ارفع ملف المنهجية", type=["pdf"])

methodology_text = ""
if methodology_file:
    try:
        methodology_text = extract_pdf_text(methodology_file)
        st.success("تم استخراج نص المنهجية بنجاح.")
        st.text_area("نص المنهجية:", methodology_text, height=200)
    except:
        st.error("خطأ في قراءة ملف المنهجية.")


st.markdown("---")

# ---------------------------
# 2️⃣ ملف القوائم المالية Excel
# ---------------------------

st.header("2️⃣ رفع ملف القوائم المالية / النسب (Excel)")

excel_file = st.file_uploader("ارفع ملف Excel", type=["xlsx", "xls"])

excel_preview = None
if excel_file:
    try:
        excel_preview = preview_excel(excel_file)
        st.success("تم استعراض بيانات Excel بنجاح.")
        st.dataframe(excel_preview.head(10))
    except:
        st.error("خطأ في قراءة ملف Excel.")


st.markdown("---")

# ---------------------------
# 3️⃣ ملفات الحوكمة (صور)
# ---------------------------

st.header("3️⃣ ملفات الحوكمة (صور)")
governance_images = st.file_uploader("ارفع ملفات الحوكمة", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
count_and_preview_images(governance_images)

st.markdown("---")

# ---------------------------
# 4️⃣ ملفات المشاريع (صور)
# ---------------------------

st.header("4️⃣ ملفات المشاريع (صور)")
project_images = st.file_uploader("ارفع ملفات المشاريع", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
count_and_preview_images(project_images)

# ✔ الخطأ هنا تم إصلاحه — كان مكتوب markmarkdown
st.markdown("---")

# ---------------------------
# 5️⃣ ملفات التقييم بالنجوم (صور)
# ---------------------------

st.header("5️⃣ ملفات التقييم بالنجوم (صور)")
stars_images = st.file_uploader("ارفع ملفات النجوم", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
count_and_preview_images(stars_images)

st.markdown("---")

# ---------------------------
# زر توليد التقرير
# ---------------------------

if st.button("🔍 إنشاء تقرير تدقيق آلي جاهز"):
    if not methodology_text:
        st.error("يجب رفع ملف المنهجية.")
    elif excel_preview is None:
        st.error("يجب رفع ملف Excel.")
    else:
        st.success("جاري إعداد التقرير… يرجى الانتظار")

        img_count_summary = f"""
        عدد صور الحوكمة: {len(governance_images)}
        عدد صور المشاريع: {len(project_images)}
        عدد صور النجوم: {len(stars_images)}
        """

        excel_data_text = excel_preview.to_string()

        report = generate_report(methodology_text, excel_data_text, img_count_summary)

        st.subheader("📄 تقرير التدقيق الآلي (جاهز للنسخ والتقديم)")
        st.write(report)

        st.markdown("---")
        st.info("تم إنشاء التقرير باستخدام نموذج OpenAI.")


