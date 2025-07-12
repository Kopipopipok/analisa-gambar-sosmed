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
