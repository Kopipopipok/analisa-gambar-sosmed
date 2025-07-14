import streamlit as st
import numpy as np
from PIL import Image
import cv2
import requests
from sklearn.cluster import KMeans
from skimage.metrics import structural_similarity as ssim

st.set_page_config(page_title="Gambar Sosmed Analyzer", layout="centered")
st.title("📊 Gambar Sosial Media Analyzer")

uploaded_file = st.file_uploader("Unggah gambar", type=["png", "jpg", "jpeg"])

def additional_metrics(img_pil):
    analysis = {}
    img = np.array(img_pil)
    img_resized = cv2.resize(img, (300, 300))
    gray = cv2.cvtColor(img_resized, cv2.COLOR_RGB2GRAY)

    # 1. Color Spectrum
    pixels = img_resized.reshape((-1, 3))
    kmeans = KMeans(n_clusters=5, n_init=10).fit(pixels)
    color_spectrum = len(np.unique(kmeans.labels_))
    analysis["Color Spectrum"] = color_spectrum

    # 2. Luminance
    luminance = np.mean(0.2126 * img_resized[:, :, 0] + 0.7152 * img_resized[:, :, 1] + 0.0722 * img_resized[:, :, 2])
    analysis["Luminance"] = round(luminance, 2)

    # 3. Object Count
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    object_count = len(contours)
    analysis["Object Count"] = object_count

    # 4. Object Regularity
    areas = [cv2.contourArea(cnt) for cnt in contours if cv2.contourArea(cnt) > 50]
    if len(areas) > 1:
        analysis["Object Regularity"] = round(np.std(areas), 2)
    else:
        analysis["Object Regularity"] = "N/A"

    # 5. Symmetry
    h, w = gray.shape
    left = gray[:, :w // 2]
    right = cv2.flip(gray[:, w - w // 2:], 1)
    min_shape = min(left.shape[1], right.shape[1])
    symmetry_score = ssim(left[:, :min_shape], right[:, :min_shape])
    analysis["Symmetry"] = round(symmetry_score, 3)

    return analysis, color_spectrum, luminance, object_count, symmetry_score

def extract_text_ocr_space(img_pil):
    buffered = cv2.imencode(".jpg", np.array(img_pil))[1].tobytes()
    response = requests.post(
        "https://api.ocr.space/parse/image",
        data={"apikey": "K85290270188957"},
        files={"filename": buffered},
    )
    try:
        text = response.json()["ParsedResults"][0]["ParsedText"]
        return text
    except:
        return ""

def extract_text_insights(text):
    lines = text.split("\n")
    insights = []
    has_cta = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) < 5:
            continue
        if any(word in line.lower() for word in ["diskon", "gratis", "sekarang", "%", "promo"]):
            insights.append(f"✅ Call-to-Action ditemukan: '{line}'")
            has_cta = True
        else:
            insights.append(f"ℹ️ Teks umum: '{line}'")
    return insights, has_cta

def predict_engagement(color_spectrum, luminance, object_count, symmetry, has_cta):
    score = 0
    if has_cta:
        score += 1
    if 2 <= color_spectrum <= 5:
        score += 1
    if 100 < luminance < 220:
        score += 1
    if 1 <= object_count <= 5:
        score += 1
    if symmetry > 0.6:
        score += 1

    if score >= 4:
        label = "🔥 Potensi Engagement Tinggi"
    elif score >= 2:
        label = "🌟 Engagement Cukup"
    else:
        label = "⚠️ Perlu Ditingkatkan"

    return score, label

def generate_recommendations(color_spectrum, luminance, object_count, symmetry, has_cta):
    recs = []
    if not has_cta:
        recs.append("💡 Tambahkan teks call-to-action seperti 'Diskon', 'Beli sekarang', atau '% gratis'")
    if not (2 <= color_spectrum <= 5):
        recs.append("🎨 Gunakan kombinasi warna yang tidak terlalu banyak agar lebih fokus")
    if not (100 < luminance < 220):
        recs.append("💡 Atur kecerahan gambar agar tidak terlalu gelap atau terlalu terang")
    if not (1 <= object_count <= 5):
        recs.append("📷 Kurangi jumlah elemen visual agar tidak terlalu ramai")
    if symmetry <= 0.6:
        recs.append("📐 Perbaiki komposisi visual agar lebih simetris dan enak dilihat")
    return recs

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Gambar yang Diunggah", use_container_width=True)

    with st.spinner("🔍 Menganalisis gambar..."):
        analysis, color_spectrum, luminance, object_count, symmetry = additional_metrics(image)
        ocr_text = extract_text_ocr_space(image)
        insights, has_cta = extract_text_insights(ocr_text)
        score, label = predict_engagement(color_spectrum, luminance, object_count, symmetry, has_cta)
        recs = generate_recommendations(color_spectrum, luminance, object_count, symmetry, has_cta)

    st.subheader("📈 Analisis Visual Tambahan")
    for key, value in analysis.items():
        st.write(f"**{key}:** {value}")

    st.subheader("📝 Teks & Insight dari Gambar")
    if ocr_text.strip():
        for line in insights:
            if "✅" in line:
                st.success(line)
            else:
                st.info(line)
    else:
        st.warning("Tidak ada teks terdeteksi.")

    st.subheader("📊 Prediksi Engagement Rate")
    st.metric("Skor Engagement", f"{score}/5", help="Berdasarkan 5 faktor visual dan teks")
    if score >= 4:
        st.success(label)
    elif score >= 2:
        st.info(label)
else:
    st.warning(label)

    if recs:
        st.subheader("🛠️ Rekomendasi Perbaikan")
        for r in recs:
            st.write("-", r)
