import json
import time
import re
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

# Determine paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
f1_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/font.ttf"))  # Scrambled font from Yuketang
f2_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../assets/SourceHanSansSC-ExtraLight.otf"))  # Standard reference
chars_list_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../assets/common_chars.txt"))
output_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/font_mapping.json"))

if not os.path.exists(f1_path):
    print(f"Error: Scrambled font file '{f1_path}' not found! Please save it in 'data/font.ttf'.")
    exit(1)
if not os.path.exists(f2_path):
    print(f"Error: Reference font file '{f2_path}' not found!")
    exit(1)
if not os.path.exists(chars_list_path):
    print(f"Error: Character list file '{chars_list_path}' not found!")
    exit(1)

# Load common Chinese characters
print("Loading common Chinese characters...")
with open(chars_list_path, 'r', encoding='utf-8') as f:
    text = f.read()

common_chars = sorted(list(set(re.findall(r'[\u4e00-\u9fff]', text))))
print("Number of common Chinese characters loaded:", len(common_chars))

f1 = TTFont(f1_path)
cmap1 = f1['cmap'].getBestCmap()
custom_chars = [chr(code) for code in cmap1.keys()]

# Filter custom_chars to CJK characters only
custom_chars = [c for c in custom_chars if '\u4e00' <= c <= '\u9fff']

font1 = ImageFont.truetype(f1_path, 48)
font2 = ImageFont.truetype(f2_path, 48)

print("Number of custom CJK characters to match:", len(custom_chars))

def get_char_img(char, font, size=32):
    img = Image.new("L", (96, 96), 0)
    draw = ImageDraw.Draw(img)
    draw.text((24, 24), char, font=font, fill=255)
    bbox = img.getbbox()
    if bbox is None:
        return None
    cropped = img.crop(bbox)
    resized = cropped.resize((size, size), Image.Resampling.BILINEAR)
    return np.array(resized)

# Pre-render all scrambled characters (inputs)
print("Rendering scrambled characters...")
scrambled_imgs = {}
for c in custom_chars:
    img_data = get_char_img(c, font1)
    if img_data is not None:
        scrambled_imgs[c] = img_data

# Pre-render common candidate characters (outputs)
print("Rendering candidate common characters...")
t_start = time.time()
candidate_imgs = {}
for c in common_chars:
    img_data = get_char_img(c, font2)
    if img_data is not None:
        candidate_imgs[c] = img_data
print(f"Rendered {len(candidate_imgs)} common candidate characters in {time.time() - t_start:.2f} seconds.")

# Convert to 2D numpy arrays
scrambled_keys = list(scrambled_imgs.keys())
candidate_keys = list(candidate_imgs.keys())

# Shape: (N, D) and (M, D) where D = 32*32 = 1024
S = np.array([scrambled_imgs[k].flatten() for k in scrambled_keys]) > 127
C = np.array([candidate_imgs[k].flatten() for k in candidate_keys]) > 127

print("Starting vectorized matching using Jaccard Similarity...")
start_time = time.time()

S_float = S.astype(float)
C_float = C.astype(float)

# intersection: (N, M)
intersection = np.dot(S_float, C_float.T)

# S_sum: (N, 1), C_sum: (1, M)
S_sum = S_float.sum(axis=1, keepdims=True)
C_sum = C_float.sum(axis=1, keepdims=True).T

# union: (N, M)
union = S_sum + C_sum - intersection

# jaccard: (N, M)
jaccard = intersection / np.maximum(union, 1)

# Find index of best candidate for each scrambled char
best_indices = np.argmax(jaccard, axis=1)

# Build mapping
mapping = {}
for i, s_char in enumerate(scrambled_keys):
    best_c_idx = best_indices[i]
    best_c_char = candidate_keys[best_c_idx]
    mapping[s_char] = best_c_char

end_time = time.time()
print(f"Matching finished in {end_time - start_time:.4f} seconds.")

# Save mapping to file
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Mapping saved to {output_path}")
