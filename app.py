import streamlit as st
import pdfplumber
import pandas as pd
from PIL import Image
import numpy as np
from datetime import date

# -----------------------------
# إعداد OpenAI (نسخة 0.28)
# -----------------------------
try:
    import openai
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
    else:
        OPENAI_API_KEY = None
except Exception:
    OPENAI_API_KEY = None

# -----------------------------
# إعدادات عامة للتطبيق
# -----------------------------
st.set_page_config(
    page_title="نظام تدقيق المنهجية وربط المدخلات",
    layout="wide"
)

# -----------------------------
# CSS للتنسيق الاحترافي
# -----------------------------
st.markdown(
    """
    <style>
    body {
        direction: rtl;
        text-align: right;
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main * {
        direction: rtl;
        text-align: right;
    }
    .report-card {
        background: linear-gradient(135deg, #0f172a 0%, #1d3557 40%, #0b1120 100%);
        color: #f9fafb;
        padding: 28px;
        border-radius: 20px;
        box-shadow: 0 15px 30px rgba(15, 23, 42, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.35);
        margin-top: 10px;
    }
    .report-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 18px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.4);
        padding-bottom: 12px;
    }
    .report-header-text {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .report-title {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .report-subtitle {
        font-size: 0.9rem;
        color: rgba(226, 232, 240, 0.85);
    }
    .badge {
        background-color: rgba(15, 118, 110, 0.15);
        color: #99f6e4;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        border: 1px solid rgba(34, 197, 175, 0.5);
    }
    .report-meta {
        display: grid;
        grid-template-columns: repeat(auto-fit,minmax(160px,1fr));
        gap: 8px 18px;
        font-size: 0.82rem;
        margin-bottom: 14px;
        color: rgba(226, 232, 240, 0.9);
    }
    .report-meta span.label {
        color: rgba(148, 163, 184, 0.95);
        font-weight: 500;
    }
    .report-body {
        margin-top: 12px;
        font-size: 0.94rem;
        line-height: 1.9;
        white-space: pre-wrap;
    }
    .report-footer {
        margin-top: 18px;
        padding-top: 10px;
        border-top: 1px dashed rgba(148, 163, 184, 0.6);
        font-size: 0.8rem;
        color: rgba(148, 163, 184, 0.95);
    }
    .logo-box {
        width: 72px;
        height: 72px;
        border-radius: 18px;
        background: rgba(15, 23, 42, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, 0.7);
    }
    .logo-box img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# رأس الصفحة
# -----------------------------
st.title("📊 نظام تدقيق المنهجية وربطها بالمدخلات")
st.markdown(
    """
هذا النظام يهدف إلى مساعدة **المدقق المالي** في:
- قراءة منهجية التقييم (PDF)  
- ربطها مع القوائم المالية / النسب (Excel)  
- إضافة مدخلات الحوكمة والمشاريع ونتائج التقييم بالنجوم  
- توليد **تقرير تدقيق آلي** بصياغة مهنية يمكن تقديمه للإدارة العليا.

> النسخة الحالية مبنية للتجارب الداخلية ويمكن تطويرها لاحقاً لتتكامل مع أنظمة الوزارة.
"""
)

st.markdown("---")

# -----------------------------
# دوال مساعدة
# -----------------------------
def extract_text_from_pdf(uploaded_file) -> str:
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
    if uploaded_file is None:
        return pd.DataFrame()
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"خطأ في قراءة ملف Excel: {e}")
        return pd.DataFrame()


def count_and_preview_images(image_files):
    if not image_files:
        st.info("لم يتم رفع أي ملفات في هذا القسم حتى الآن.")
        return

    st.write(f"عدد الملفات المرفوعة: **{len(image_files)}**")
    cols = st.columns(4)
    for idx, img_file in enumerate(image_files[:8]):
        with cols[idx % 4]:
            try:
                image = Image.open(img_file)
                st.image(image, caption=img_file.name, use_column_width=True)
            except Exception as e:
                st.warning(f"تعذّر عرض الصورة: {img_file.name} - {e}")


def simple_text_summary(text: str, max_chars: int = 1500) -> str:
    if not text:
        return "لا يوجد نص لاستخلاص ملخص منه."
    trimmed = text[:max_chars]
    if len(text) > max_chars:
        trimmed += "\n\n[تم قص النص للعرض فقط...]"
    return trimmed


def detect_available_years(df: pd.DataFrame):
    if df.empty:
        return []

    year_cols = []
    for c in df.columns:
        try:
            int(c)
            year_cols.append(c)
        except:
            continue

    non_zero_years = []
    for y in year_cols:
        try:
            col = df[y].replace([np.nan], 0).astype(float)
            total = col.abs().sum()
            if total != 0:
                non_zero_years.append(y)
        except Exception:
            continue

    return non_zero_years


def summarize_financials(df: pd.DataFrame, available_years) -> str:
    if df.empty:
        return "لا توجد بيانات مالية متاحة."

    rows, cols = df.shape
    summary_lines = []
    summary_lines.append(f"عدد الصفوف: {rows} صف، وعدد الأعمدة: {cols} عمود.\n")

    if len(available_years) == 0:
        summary_lines.append(
            "لم يتم التعرف على أعمدة تمثل سنوات مالية تحتوي على بيانات فعلية. "
            "قد تكون الشركة جديدة جداً أو أن الأعمدة ليست مسماة كقِيَم سنوات (مثل 2023، 2024...)."
        )
    elif len(available_years) == 1:
        summary_lines.append(
            f"تبيّن أن الشركة لديها سنة مالية واحدة متاحة وهي ({available_years[0]}). "
            "بالتالي لا يمكن احتساب مؤشرات نمو تاريخية، وسيتم الاعتماد على هذه السنة فقط."
        )
    else:
        years_sorted = sorted(available_years)
        summary_lines.append(
            "تتوفر بيانات مالية لعدة سنوات، مما يسمح بدراسة اتجاهات النمو والتغير في الأداء المالي. "
            f"أول سنة متاحة: {years_sorted[0]}، وآخر سنة متاحة: {years_sorted[-1]}."
        )

    summary_lines.append("\nأهم الأعمدة المتاحة في الملف:")
    summary_lines.append(", ".join([str(c) for c in df.columns[:10]]))

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        summary_lines.append("\n\nبعض الأعمدة العددية ومؤشراتها التقريبية:")
        for col in numeric_cols[:5]:
            try:
                col_series = df[col].dropna()
                if not col_series.empty:
                    summary_lines.append(
                        f"- {col}: متوسط {col_series.mean():,.2f}، "
                        f"أعلى قيمة {col_series.max():,.2f}، أقل قيمة {col_series.min():,.2f}"
                    )
            except Exception:
                continue

    return "\n".join(summary_lines)


def summarize_images_info(governance_images, project_images, rating_images) -> str:
    lines = []
    lines.append(f"عدد ملفات الحوكمة المرفوعة: {len(governance_images) if governance_images else 0}.")
    if governance_images:
        lines.append("أمثلة على أسماء ملفات الحوكمة:")
        for f in governance_images[:5]:
            lines.append(f"- {f.name}")

    lines.append(f"\nعدد ملفات المشاريع المرفوعة: {len(project_images) if project_images else 0}.")
    if project_images:
        lines.append("أمثلة على أسماء ملفات المشاريع:")
        for f in project_images[:5]:
            lines.append(f"- {f.name}")

    lines.append(f"\nعدد ملفات التقييم بالنجوم المرفوعة: {len(rating_images) if rating_images else 0}.")
    if rating_images:
        lines.append("أمثلة على أسماء ملفات التقييم:")
        for f in rating_images[:5]:
            lines.append(f"- {f.name}")

    lines.append(
        "\nملاحظة: في هذه النسخة يتم استخدام المعلومات الوصفية (عدد الملفات وأسماؤها)، "
        "ويمكن مستقبلاً إضافة قراءة محتوى الصور (OCR / Vision) لربط أكثر دقة."
    )

    return "\n".join(lines)


def generate_ai_audit_comment(
    methodology_text,
    financial_summary,
    images_summary,
    single_year_mode,
    base_year,
    company_name,
    company_cr,
    auditor_name,
    report_date_str,
    authority_name
) -> str:
    if not OPENAI_API_KEY:
        return (
            "لم يتم ضبط مفتاح OpenAI API في إعدادات Secrets، "
            "لذلك يعرض النظام تعليقاً مبدئياً فقط."
        )

    methodology_excerpt = methodology_text[:6000] if methodology_text else "لا يوجد نص للمنهجية."

    if single_year_mode and base_year is not None:
        years_note = (
            f"الشركة لديها سنة مالية واحدة فقط ({base_year}) ببيانات فعلية، "
            "وهو أمر معتاد في الشركات حديثة التأسيس. بناءً على ذلك، تم الاعتماد على هذه السنة "
            "في الحكم على الوضع المالي دون احتساب مؤشرات نمو تاريخية."
        )
    else:
        years_note = (
            "يتضح من البيانات المالية أن هناك أكثر من سنة متاحة، "
            "مما يسمح بدراسة اتجاهات النمو والتغير في الأداء المالي عبر الفترات."
        )

    prompt = f"""
أنت مدقق مالي يعمل في جهة رسمية للتصنيف الائتماني (مثل {authority_name}).
بيانات الشركة محل التقييم كما يلي:
- اسم الشركة: {company_name}
- الرقم الموحد: {company_cr}
- اسم المدقق المالي: {auditor_name}
- تاريخ إعداد التقرير: {report_date_str}

نص المنهجية (مقتطف رئيسي):
----------------
{methodology_excerpt}
----------------

ملخص البيانات المالية:
----------------
{financial_summary}
----------------

ملاحظة حول السنوات المالية:
----------------
{years_note}
----------------

ملخص عن ملفات الحوكمة والمشاريع والتقييم بالنجوم:
----------------
{images_summary}
----------------

المطلوب منك إعداد تقرير تدقيق ائتماني مهني باللغة العربية، بصياغة رسمية يمكن تقديمها للإدارة العليا، يتضمن:

1. **ملخص تنفيذي (Executive Summary)**:
   - يوضح الهدف من المراجعة، وحداثة الشركة من عدمها، وطبيعة البيانات المتاحة.
2. **منهجية التقييم**:
   - شرح مختصر لكيفية تطبيق المنهجية (دون نقلها حرفياً).
3. **مراجعة القوائم المالية والنسب**:
   - تعليق مهني على هيكل المركز المالي، السيولة، الربحية (إن توفرت)، ومخاطر المديونية.
4. **مراجعة الحوكمة والمشاريع**:
   - تقييم كفاية الأدلة المرفوعة حول الحوكمة والمشاريع كدعم للتصنيف.
5. **اتساق التقييم بالنجوم مع المنهجية والمدخلات**:
   - مناقشة عامة لاتساق نتيجة التقييم (النجوم) مع المعطيات المتاحة.
6. **الخلاصة والتوصيات**:
   - خلاصة واضحة عن مدى كفاية البيانات الحالية لإصدار حكم نهائي أو اعتباره تصنيفاً أولياً.
   - توصيات عملية للمحللين وللشركة لتحسين جودة البيانات مستقبلًا.

احرص أن يكون الأسلوب رسمي، واضح، ومناسب لوضعه في تقرير رسمي يرفع إلى الإدارة.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مدقق مالي محترف ومتخصص في تقييم شركات المقاولات."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
        )
        content = response.choices[0].message["content"].strip()
        return content
    except Exception as e:
        return f"تعذر توليد تقرير التدقيق الآلي بسبب خطأ في استدعاء OpenAI: {e}"


# -----------------------------
# مدخلات بيانات التقرير (رأس التقرير)
# -----------------------------
st.subheader("🧾 بيانات التقرير الأساسية")

col_a, col_b, col_c = st.columns(3)

with col_a:
    company_name = st.text_input("اسم الشركة", "")
    authority_name = st.text_input("اسم الجهة/الوزارة", "وكالة تصنيف المقاولين")

with col_b:
    company_cr = st.text_input("الرقم الموحد / السجل التجاري", "")
    auditor_name = st.text_input("اسم المدقق المالي", "")

with col_c:
    report_date_val = st.date_input("تاريخ إعداد التقرير", value=date.today())
    logo_file = st.file_uploader("شعار الوزارة / الجهة (اختياري)", type=["png", "jpg", "jpeg"])

st.markdown("---")

# -----------------------------
# واجهة رفع الملفات الفنية
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
start = st.button("🚀 توليد تقرير التدقيق الآلي")

if start:
    # ---------------------------------
    # 1) معالجة ملف المنهجية PDF
    # ---------------------------------
    st.header("1️⃣ تحليل ملف المنهجية (PDF)")
    methodology_text = extract_text_from_pdf(methodology_pdf)
    if methodology_text:
        st.success("تم استخراج نص المنهجية بنجاح.")
        st.markdown("**مقتطف من نص المنهجية:**")
        st.text_area("نص المنهجية (مقتطف)", simple_text_summary(methodology_text), height=220)
    else:
        st.warning("لم يتم استخراج نص من ملف المنهجية، تأكد من رفع ملف صحيح.")

    st.markdown("---")

    # ---------------------------------
    # 2) معالجة ملف القوائم المالية Excel
    # ---------------------------------
    st.header("2️⃣ تحليل ملف القوائم المالية / النسب (Excel)")
    financial_df = read_excel_file(financial_excel)

    available_years = detect_available_years(financial_df)
    if len(available_years) == 1:
        single_year_mode = True
        base_year = available_years[0]
    else:
        single_year_mode = False
        base_year = None

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

    st.markmarkdown("---")
    st.header("5️⃣ ملفات التقييم بالنجوم")
    count_and_preview_images(rating_images)

    st.markdown("---")

    # ---------------------------------
    # 4) تقرير تدقيق آلي بالذكاء الاصطناعي (منسق)
    # ---------------------------------
    st.header("6️⃣ تقرير التدقيق الآلي (منسق وجاهز للتقديم)")

    financial_summary = summarize_financials(financial_df, available_years)
    images_summary = summarize_images_info(governance_images, project_images, rating_images)
    report_date_str = report_date_val.strftime("%Y-%m-%d")

    with st.expander("👁️ معاينة الملخصات التي يعتمد عليها نموذج الذكاء الاصطناعي", expanded=False):
        st.subheader("ملخص البيانات المالية")
        st.text(financial_summary)
        st.subheader("ملخص ملفات الحوكمة والمشاريع والنجوم")
        st.text(images_summary)

    if OPENAI_API_KEY:
        st.info("يتم الآن استخدام OpenAI لتوليد تقرير التدقيق الآلي بناءً على المدخلات المتاحة...")
        ai_comment = generate_ai_audit_comment(
            methodology_text,
            financial_summary,
            images_summary,
            single_year_mode,
            base_year,
            company_name,
            company_cr,
            auditor_name,
            report_date_str,
            authority_name
        )

        # بناء نص التقرير الكامل مع رأس/تذييل
        header_text = f"""جهة التقييم: {authority_name}
اسم الشركة: {company_name}
الرقم الموحد / السجل التجاري: {company_cr}
تاريخ إعداد التقرير: {report_date_str}
اسم المدقق المالي: {auditor_name}
"""
        footer_text = (
            "هذا التقرير أعد لأغراض التقييم الائتماني الداخلي استناداً إلى البيانات المتاحة في تاريخ إعداده، "
            "ولا يجوز تداوله خارج الجهة إلا بعد الحصول على الموافقات النظامية المعتمدة."
        )

        final_report_text = header_text + "\n\n" + ai_comment + "\n\n" + footer_text

        # عرض التقرير داخل كارد منسق
        st.markdown('<div class="report-card">', unsafe_allow_html=True)

        # رأس التقرير داخل الكارد
        st.markdown('<div class="report-header">', unsafe_allow_html=True)

        # شعار (إن وجد)
        if logo_file is not None:
            st.markdown('<div class="logo-box">', unsafe_allow_html=True)
            st.image(logo_file, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # مربع فارغ مكان الشعار
            st.markdown(
                '<div class="logo-box"><span style="font-size:11px;color:#9ca3af;">شعار الجهة</span></div>',
                unsafe_allow_html=True
            )

        # نص الرأس
        header_html = f"""
        <div class="report-header-text">
            <div class="report-title">تقرير تدقيق ائتماني آلي</div>
            <div class="report-subtitle">{authority_name}</div>
            <div class="badge">نسخة تجريبية للاستخدام الداخلي</div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # إغلاق report-header

        # بيانات مختصرة أعلى التقرير
        meta_html = f"""
        <div class="report-meta">
            <div><span class="label">اسم الشركة:</span><br>{company_name or "غير مدخل"}</div>
            <div><span class="label">الرقم الموحد:</span><br>{company_cr or "غير مدخل"}</div>
            <div><span class="label">تاريخ التقرير:</span><br>{report_date_str}</div>
            <div><span class="label">المدقق المالي:</span><br>{auditor_name or "غير مدخل"}</div>
        </div>
        """
        st.markdown(meta_html, unsafe_allow_html=True)

        # نص التقرير
        st.markdown('<div class="report-body">', unsafe_allow_html=True)
        st.write(final_report_text)
        st.markdown('</div>', unsafe_allow_html=True)

        # تذييل
        st.markdown(f'<div class="report-footer">{footer_text}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # إغلاق report-card

        # زر تحميل التقرير كنص
        st.download_button(
            label="⬇️ تحميل التقرير كنص",
            data=final_report_text,
            file_name="credit_audit_report.txt",
            mime="text/plain"
        )

    else:
        st.warning(
            "لم يتم العثور على مفتاح OpenAI API في Secrets.\n"
            "للحصول على تقرير تدقيق آلي منسق، أضف المفتاح تحت الاسم OPENAI_API_KEY في إعدادات التطبيق."
        )
