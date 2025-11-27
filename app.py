import streamlit as st
import pdfplumber
import pandas as pd
from PIL import Image
import io
import textwrap

# لو بتستخدم OpenAI لاحقاً:
# import openai
# openai.api_key = st.secrets.get("OPENAI_API_KEY", None)

# -----------------------------
# إعدادات عامة للتطبيق
# -----------------------------
st.set_page_config(
    page_title="نظام تدقيق المنهجية وربط المدخلات",
    layout="wide"
)

st.title("📊 نظام تدقيق المنهجية وربطها بالمدخلات (نسخة أولية)")
st.markdown(
    """
هذا النموذج يسمح لك برفع:
- ملف **منهجية التقييم** بصيغة PDF  
- ملف **القوائم المالية / النسب** بصيغة Excel  
- ملفات **الحوكمة** بصيغة صور (بعدد غير محدود)  
- ملفات **المشاريع** بصيغة صور (بعدد غير محدود)  
- ملفات **التقييم بالنجوم** بصيغة صور (بعدد غير محدود)

ثم يقوم باستخراج نصوص وملخصات مبدئية تساعدك في التدقيق.  
التحليل الذكي بالذكاء الاصطناعي يمكن إضافته لاحقاً في نفس الهيكل.
"""
)

st.markdown("---")

# -----------------------------
# دوال مساعدة
# -----------------------------
def extract_text_from_pdf(uploaded_file) -> str:
    """استخراج النص من ملف PDF باستخدام pdfplumber."""
    if uploaded_file is None:
        return ""
    text_pages = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_pages.append(page_text)
    full_text = "\n".join(text_pages)
    return full_text.strip()

def read_excel_file(uploaded_file) -> pd.DataFrame:
    """قراءة ملف Excel وإرجاع DataFrame."""
    if uploaded_file is None:
        return pd.DataFrame()
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"خطأ في قراءة ملف Excel: {e}")
        return pd.DataFrame()

def count_and_preview_images(image_files):
    """عرض عدد الصور وبعض المعاينات المصغرة."""
    if not image_files:
        st.info("لم يتم رفع أي ملفات في هذا القسم حتى الآن.")
        return

    st.write(f"عدد الملفات المرفوعة: **{len(image_files)}**")
    cols = st.columns(4)
    for idx, img_file in enumerate(image_files[:8]):  # نعرض بحد أقصى 8 صور للمعاينة
        with cols[idx % 4]:
            try:
                image = Image.open(img_file)
                st.image(image, caption=img_file.name, use_column_width=True)
            except Exception as e:
                st.warning(f"تعذّر عرض الصورة: {img_file.name} - {e}")

def simple_text_summary(text: str, max_chars: int = 1200) -> str:
    """تلخيص بسيط جداً بقص النص (مكان مؤقت قبل إدخال AI)."""
    if not text:
        return "لا يوجد نص لاستخلاص ملخص منه."
    trimmed = text[:max_chars]
    if len(text) > max_chars:
        trimmed += "\n\n[تم قص النص للعرض فقط...]"
    return trimmed

# مستقبلاً: دالة تستخدم OpenAI لكتابة تقرير تدقيق كامل
# def generate_ai_audit_comment(methodology_text, financial_df, gov_text, proj_text, rating_text):
#     if not openai.api_key:
#         return "لم يتم ضبط مفتاح OpenAI API، يرجى إضافته في إعدادات Streamlit Secrets."
#     prompt = f"""
# أنت مدقق مالي. أمامك:
# - نص منهجية التقييم:
# {methodology_text[:4000]}
#
# - ملخص بيانات مالية (رؤوس الأعمدة وأول صفين):
# {financial_df.head(2).to_markdown() if not financial_df.empty else "لا توجد بيانات مالية"}
#
# - ملاحظات من ملفات الحوكمة:
# {gov_text}
#
# - ملاحظات من ملفات المشاريع:
# {proj_text}
#
# - ملاحظات من ملفات النجوم/التقييم:
# {rating_text}
#
# اكتب تقرير تدقيق مختصر (3-6 فقرات) يوضح:
# - مدى تناسق مخرجات التقييم مع المنهجية
# - أي ملاحظات عدم تطابق واضحة
# - بنود تحتاج مراجعة إضافية
# بأسلوب مهني باللغة العربية.
# """
#     response = openai.ChatCompletion.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return response.choices[0].message["content"].strip()


# -----------------------------
# واجهة رفع الملفات
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 ملف المنهجية (PDF)")
    methodology_pdf = st.file_uploader("ارفع ملف المنهجية بصيغة PDF", type=["pdf"])

    st.subheader("📊 ملف القوائم المالية / النسب (Excel)")
    financial_excel = st.file_uploader("ارفع ملف Excel للقوائم المالية / النسب", type=["xlsx", "xls"])

with col2:
    st.subheader("🏛 ملفات الحوكمة (صور)")
    governance_images = st.file_uploader(
        "ارفع ملفات الحوكمة (عدد غير محدود)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    st.subheader("🏗 ملفات المشاريع (صور)")
    project_images = st.file_uploader(
        "ارفع ملفات المشاريع (عدد غير محدود)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    st.subheader("⭐ ملفات التقييم بالنجوم (صور)")
    rating_images = st.file_uploader(
        "ارفع ملفات مخرجات النجوم / التقييم (عدد غير محدود)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

st.markdown("---")

# زر بدء التحليل
start = st.button("🚀 بدء التحليل المبدئي")

if start:
    # ---------------------------------
    # 1) معالجة ملف المنهجية PDF
    # ---------------------------------
    st.header("1️⃣ تحليل ملف المنهجية (PDF)")
    methodology_text = extract_text_from_pdf(methodology_pdf)
    if methodology_text:
        st.success("تم استخراج نص المنهجية بنجاح.")
        st.markdown("**ملخص أولي لنص المنهجية (مقتطف):**")
        st.text_area("نص المنهجية (مقتطف)", simple_text_summary(methodology_text), height=250)
    else:
        st.warning("لم يتم استخراج نص من ملف المنهجية، تأكد من رفع ملف صحيح.")

    st.markdown("---")

    # ---------------------------------
    # 2) معالجة ملف القوائم المالية Excel
    # ---------------------------------
    st.header("2️⃣ تحليل ملف القوائم المالية / النسب (Excel)")
    financial_df = read_excel_file(financial_excel)
    if not financial_df.empty:
        st.success("تم قراءة ملف Excel بنجاح.")
        st.write("**رؤوس الأعمدة:**")
        st.write(list(financial_df.columns))
        st.write("**أول 5 صفوف من البيانات:**")
        st.dataframe(financial_df.head())
    else:
        st.warning("لم يتم قراءة بيانات من ملف Excel، تأكد من رفع ملف صحيح.")

    st.markdown("---")

    # ---------------------------------
    # 3) معاينة ملفات الحوكمة / المشاريع / النجوم
    # ---------------------------------
    st.header("3️⃣ ملفات الحوكمة")
    count_and_preview_images(governance_images)

    st.markdown("---")
    st.header("4️⃣ ملفات المشاريع")
    count_and_preview_images(project_images)

    st.markdown("---")
    st.header("5️⃣ ملفات التقييم بالنجوم")
    count_and_preview_images(rating_images)

    st.markdown("---")

    # ---------------------------------
    # 4) مكان التحليل الذكي (يمكن تطويره لاحقاً)
    # ---------------------------------
    st.header("6️⃣ (اختياري لاحقاً) تقرير تدقيق آلي بالذكاء الاصطناعي")
    st.info(
        "في النسخة الحالية نعرض فقط الملخصات والمعاينات.\n"
        "يمكن في الخطوة التالية إضافة استدعاء OpenAI لكتابة تقرير تدقيق كامل "
        "يربط بين المنهجية والمدخلات والحوكمة والمشاريع والتقييم."
    )

    # مثال بسيط جداً كنص مبدئي بدون AI:
    simple_audit_comment = """
    تقرير مبدئي (يدوي):

    - تم استيراد نص المنهجية والتحضير لاستخدامه كمرجع أساسي في التقييم.
    - تم تحميل القوائم المالية / النسب، ويمكن مطابقتها مع البنود المالية في المنهجية.
    - تم تحميل ملفات الحوكمة والمشاريع والنجوم، ويمكن استخدامها كأدلة داعمة للتحقق من التقييم النهائي.
    
    في النسخ اللاحقة، سيتم:
    - استخراج البنود التفصيلية من المنهجية (شروط، نسب، نجوم).
    - مقارنة كل بند مع البيانات الفعلية من Excel والوثائق المصورة.
    - إصدار تقرير تدقيق مفصل يوضح نقاط التوافق والاختلاف.
    """
    st.text_area("تعليق تدقيقي مبدئي:", simple_audit_comment, height=220)

    # لو بتستخدم AI مستقبلاً:
    # if methodology_text or not financial_df.empty or governance_images or project_images or rating_images:
    #     gov_summary = f"عدد ملفات الحوكمة: {len(governance_images) if governance_images else 0}"
    #     proj_summary = f"عدد ملفات المشاريع: {len(project_images) if project_images else 0}"
    #     rating_summary = f"عدد ملفات النجوم: {len(rating_images) if rating_images else 0}"
    #
    #     ai_comment = generate_ai_audit_comment(
    #         methodology_text,
    #         financial_df,
    #         gov_summary,
    #         proj_summary,
    #         rating_summary
    #     )
    #     st.subheader("🔥 تقرير تدقيق آلي (باستخدام OpenAI):")
    #     st.write(ai_comment)
