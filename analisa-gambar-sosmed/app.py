import streamlit as st
from PIL import Image, ImageStat
import numpy as np
import requests
import base64
import io

st.set_page_config(page_title="Analisa Gambar Sosmed", layout="centered")

# MASUKKAN API KEY KAMU DI SINI 👇
OCR_API_KEY = "K85290270188957"

st.title("📊 Analisa Gambar untuk Postingan Sosial Media")

uploaded_file = st.file_uploader("Unggah gambar postingan (JPEG/PNG)", type=["jpg", "jpeg", "png"])

def get_dominant_color(img):
    img = img.resize((100, 100))
    pixels = np.array(img).reshape(-1, 3)
    unique, counts = np.unique(pixels, axis=0, return_counts=True)
    dominant = unique[np.argmax(counts)]
    return dominant

def get_contrast_score(img):
    gray_img = img.convert("L")
    stat = ImageStat.Stat(gray_img)
    contrast = stat.stddev[0]
    return contrast

def extract_text_ocr_space(image: Image.Image) -> str:
    buffered = io.BytesIO()  # ← diubah dari st.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    url = "https://api.ocr.space/parse/image"
    headers = {
        'apikey': OCR_API_KEY,
    }
    data = {
        'base64Image': f'data:image/jpeg;base64,{img_base64}',
        'language': 'ind',
        'isOverlayRequired': False,
    }
    response = requests.post(url, data=data, headers=headers)
    result = response.json()

    try:
        return result['ParsedResults'][0]['ParsedText']
    except:
        return ""

def check_cta(text):
    cta_keywords = ["beli", "klik", "scan", "pesan", "hubungi", "diskon", "gratis"]
    found = [word for word in cta_keywords if word in text.lower()]
    return found

def calculate_simplicity(img, text):
    small_img = img.resize((50, 50))
    pixels = np.array(small_img).reshape(-1, 3)
    unique_colors = np.unique(pixels, axis=0).shape[0]
    color_score = 1 - min(unique_colors / 256, 1)  # makin banyak warna, makin kompleks
    text_score = 1 - min(len(text) / 200, 1)       # makin panjang teks, makin kompleks
    return round((color_score + text_score) / 2, 2)  # rata-rata

def estimate_engagement(cta_found, contrast, dominant_color):
    score = 0
    if cta_found:
        score += 1
    if contrast > 30:
        score += 1
    if dominant_color[0] > 150:  # warna dominan merah
        score += 1
    return round(score / 3, 2)

def calculate_complexity(img):
    gray = img.convert("L")
    histogram = gray.histogram()
    histogram = np.array(histogram) / sum(histogram)
    entropy = -np.sum(histogram * np.log2(histogram + 1e-6))
    return round(entropy / 8, 2)  # skala 0–1

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Gambar yang diunggah", use_container_width=True)

    with st.spinner("🔍 Menganalisis gambar..."):
        dominant_color = get_dominant_color(image)
        contrast = get_contrast_score(image)
        text_content = extract_text_ocr_space(image)
        cta_found = check_cta(text_content)

        st.subheader("📋 Hasil Analisis")
        st.markdown(f"**Kontras Gambar**: {contrast:.2f} → {'✅ Baik' if contrast > 20 else '⚠️ Rendah'}")
        st.markdown(f"**Teks Terdeteksi**: {text_content[:100]}{'...' if len(text_content) > 100 else ''}")
        st.markdown(f"**CTA Ditemukan**: {', '.join(cta_found) if cta_found else '❌ Tidak ditemukan'}")
        st.markdown(f"**Warna Dominan**: RGB {tuple(dominant_color)}")

        st.subheader("🧠 Rekomendasi")
        
        if contrast < 20:
            st.warning("Tingkat kontras rendah. Tingkatkan keterbacaan teks.")
        if not cta_found:
            st.info("Tidak ditemukan CTA. Tambahkan ajakan seperti 'Klik Sekarang', 'Beli', atau 'Scan'.")
        else:
            st.success("CTA ditemukan. Bagus!")
        simplicity = calculate_simplicity(image, text_content)
        engagement = estimate_engagement(cta_found, contrast, dominant_color)
        complexity = calculate_complexity(image)

        st.subheader("📊 Skor Visual Lanjutan")
        st.markdown(f"**Simplicity**: {simplicity} (1 = sangat sederhana)")
        st.markdown(f"**Complexity**: {complexity} (1 = sangat kompleks)")
        st.markdown(f"**Prediksi Engagement**: {engagement} (0–1)")

        if simplicity < 0.4:
            st.info("Desain cukup kompleks. Pertimbangkan menyederhanakan elemen visual.")
        if engagement > 0.7:
            st.success("Gambar ini berpotensi mendapat engagement tinggi.")
