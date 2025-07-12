import streamlit as st
from PIL import Image
import pytesseract
import numpy as np
import cv2

st.set_page_config(page_title="Analisa Gambar Sosmed", layout="centered")

st.title("📊 Analisa Gambar untuk Postingan Sosial Media")

uploaded_file = st.file_uploader("Unggah gambar postingan (JPEG/PNG)", type=["jpg", "jpeg", "png"])

def get_dominant_color(img, k=4):
    img = img.resize((100, 100))
    arr = np.array(img)
    arr = arr.reshape((-1, 3))
    arr = arr[np.random.choice(arr.shape[0], 1000, replace=True)]
    colors, _ = np.unique(arr, axis=0, return_counts=True)
    return colors[0]

def get_contrast_score(img):
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    contrast = gray.std()
    return contrast

def extract_text(img):
    text = pytesseract.image_to_string(img)
    return text

def check_cta(text):
    cta_keywords = ["beli", "klik", "scan", "pesan", "hubungi", "diskon", "gratis"]
    found = [word for word in cta_keywords if word in text.lower()]
    return found

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Gambar yang diunggah", use_column_width=True)

    with st.spinner("🔍 Menganalisis gambar..."):
        dominant_color = get_dominant_color(image)
        contrast = get_contrast_score(image)
        text_content = extract_text(image)
        cta_found = check_cta(text_content)

        st.subheader("📋 Hasil Analisis")
        st.markdown(f"**Kontras Gambar**: {contrast:.2f} → {'✅ Baik' if contrast > 40 else '⚠️ Rendah'}")
        st.markdown(f"**Teks Terdeteksi**: {text_content[:100]}{'...' if len(text_content) > 100 else ''}")
        st.markdown(f"**CTA Ditemukan**: {', '.join(cta_found) if cta_found else '❌ Tidak ditemukan'}")
        st.markdown(f"**Warna Dominan**: RGB {tuple(dominant_color)}")

        st.subheader("🧠 Rekomendasi")
        if contrast < 40:
            st.warning("Tingkat kontras rendah. Tingkatkan keterbacaan teks.")
        if not cta_found:
            st.info("Tidak ditemukan CTA. Tambahkan ajakan seperti 'Klik Sekarang', 'Beli', atau 'Scan'.")
        else:
            st.success("CTA ditemukan. Bagus!")