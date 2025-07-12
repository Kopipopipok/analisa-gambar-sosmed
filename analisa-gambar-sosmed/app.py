import streamlit as st
import numpy as np
from PIL import Image
import cv2
import requests
from sklearn.cluster import KMeans
from skimage.metrics import structural_similarity as ssim

st.set_page_config(page_title="Gambar Sosmed Analyzer", layout="centered")
st.title("📊 Sosial Media Analyzer")

uploaded_file = st.file_uploader("Unggah gambar", type=["png", "jpg", "jpeg"])

def additional_metrics(img_pil):
    analysis = {}
    img = np.array(img_pil)
    img_resized = cv2.resize(img, (300, 300))
    gray = cv2.cvtColor(img_resized, cv2.COLOR_RGB2GRAY)

    # 1. Color Spectrum
    pixels = img_resized.reshape((-1, 3))
    kmeans = KMeans(n_clusters=5, n_init=10).fit(pixels)
    analysis["Color Spectrum"] = len(np.unique(kmeans.labels_))

    # 2. Luminance
    luminance = np.mean(0.2126 * img_resized[:, :, 0] + 0.7152 * img_resized[:, :, 1] + 0.0722 * img_resized[:, :, 2])
    analysis["Luminance"] = round(luminance, 2)

    # 3. Object Count
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    analysis["Object Count"] = len(contours)

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
    score = ssim(left[:, :min_shape], right[:, :min_shape])
    analysis["Symmetry"] = round(score, 3)

    return analysis

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
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) < 5:
            continue
        if any(word in line.lower() for word in ["diskon", "gratis", "sekarang", "%", "promo"]):
            insights.append(f"✅ Call-to-Action ditemukan: '{line}'")
        else:
            insights.append(f"ℹ️ Teks umum: '{line}'")
    return insights

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Gambar yang Diunggah", use_container_width=True)

    with st.spinner("🔍 Menganalisis gambar..."):
        additional = additional_metrics(image)
        ocr_text = extract_text_ocr_space(image)
        insights = extract_text_insights(ocr_text)

    st.subheader("📈 Analisis Visual Tambahan")
    for key, value in additional.items():
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

