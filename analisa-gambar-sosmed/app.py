import streamlit as st
from PIL import Image, ImageStat, ImageFilter
import numpy as np
import requests
import base64
import io

# --- Konfigurasi Streamlit ---
st.set_page_config(page_title="Visual Image Analyzer", layout="centered")
st.title("🖼️ Image Feature Analysis for Social Media")

# --- Masukkan API Key OCR.Space ---
OCR_API_KEY = "K85290270188957"  # Ganti dengan API key kamu

# --- Upload Gambar ---
uploaded_file = st.file_uploader("Unggah gambar untuk analisa", type=["jpg", "jpeg", "png"])

# --- Fungsi-fungsi analisis gambar ---
def get_color_diversity(img):
    img_small = img.resize((128, 128))
    pixels = np.array(img_small).reshape(-1, 3)
    unique_colors = np.unique(pixels, axis=0).shape[0]
    return round(unique_colors / 4096, 4)  # Normalisasi (64*64 = 4096)

def get_brightness(img):
    stat = ImageStat.Stat(img)
    r, g, b = stat.mean
    return round((r + g + b) / 3, 2)

def get_saturation(img):
    hsv = img.convert("HSV")
    h, s, v = hsv.split()
    return round(np.array(s).mean(), 2)

def get_edge_complexity(img):
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    arr = np.array(edges)
    return round(np.mean(arr) / 10, 4)

def get_whitespace_ratio(img):
    gray = img.convert("L")
    arr = np.array(gray)
    white_pixels = np.sum(arr > 245)
    total_pixels = arr.size
    return round(white_pixels / total_pixels, 4)

def extract_text_ocr_space(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    url = "https://api.ocr.space/parse/image"
    headers = {'apikey': OCR_API_KEY}
    data = {
        'base64Image': f'data:image/jpeg;base64,{img_base64}',
        'language': 'eng',
        'isOverlayRequired': True
    }
    response = requests.post(url, data=data, headers=headers)
    result = response.json()
    try:
        parsed = result['ParsedResults'][0]
        text = parsed['ParsedText']
        boxes = parsed.get('TextOverlay', {}).get('Lines', [])
        text_areas = [box['Words'][0]['Height'] * box['Words'][0]['Width'] for box in boxes if box['Words']]
        avg_text_area = np.mean(text_areas) if text_areas else 0
        text_density = sum(text_areas) / (image.size[0] * image.size[1]) if text_areas else 0
        return text, round(avg_text_area, 4), round(text_density, 8)
    except:
        return "", 0, 0

def generate_insight(color_div, edge_complex):
    insights = []
    if color_div > 0.7:
        insights.append("✅ This image has great color diversity")
    if edge_complex > 7:
        insights.append("✅ High visual detail and edge complexity")
    if not insights:
        insights.append("ℹ️ Consider using more color variation and sharpness")
    return insights

# --- Logika utama ---
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="📷 Gambar yang diunggah", use_container_width=True)

    with st.spinner("🔍 Menganalisis gambar..."):
        color_div = get_color_diversity(image)
        brightness = get_brightness(image)
        saturation = get_saturation(image)
        edge_complex = get_edge_complexity(image)
        whitespace = get_whitespace_ratio(image)
        text_content, avg_text_area, text_density = extract_text_ocr_space(image)
        insights = generate_insight(color_div, edge_complex)

    # --- Tampilkan hasil ---
    st.markdown("### Feature Analysis")
    st.markdown(f"**Color Diversity:** {color_div}  ")
    st.caption("Measures the variety of colors in the image. Higher values indicate a more diverse color palette.")

    st.markdown(f"**Avg Text Area:** {avg_text_area}  ")
    st.caption("Represents the average size of text regions detected in the image. Larger values suggest bigger text areas.")

    st.markdown(f"**Text Density:** {text_density}  ")
    st.caption("Indicates the proportion of text regions relative to the total image area. Higher values suggest text-heavy images.")

    st.markdown(f"**Whitespace Ratio:** {whitespace}  ")
    st.caption("Measures the proportion of white or blank space in the image. Higher values indicate more whitespace.")

    st.markdown(f"**Edge Complexity:** {edge_complex}  ")
    st.caption("Quantifies the density of edges in the image, representing visual complexity.")

    st.markdown(f"**Brightness:** {brightness}  ")
    st.caption("Represents the average brightness level of the image. Higher values indicate brighter images.")

    st.markdown(f"**Saturation:** {saturation}  ")
    st.caption("Measures the intensity of colors in the image. Higher values suggest more vibrant and saturated colors.")

    st.markdown("### Key Insights")
    for line in insights:
        if "✅" in line:
            st.success(line)
        else:
            st.info(line)
