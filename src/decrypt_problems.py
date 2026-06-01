import json
import re
import os

# Determine paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
mapping_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/font_mapping.json"))
response_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/exercise_response.json"))  # Save raw API response here
output_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/decrypted_problems.json"))

if not os.path.exists(mapping_path):
    print(f"Error: Mapping file '{mapping_path}' not found! Run 'decrypt_font.py' first.")
    exit(1)
if not os.path.exists(response_path):
    print(f"Error: Network response file '{response_path}' not found! Please save Yuketang's exercise request response in 'data/exercise_response.json'.")
    exit(1)

with open(mapping_path, "r", encoding="utf-8") as f:
    mapping = json.load(f)

with open(response_path, "r", encoding="utf-8") as f:
    response_data = json.load(f)

def decrypt_text(text):
    if not text:
        return ""
    result = []
    for char in text:
        result.append(mapping.get(char, char))
    return "".join(result)

def decrypt_html(html):
    if not html:
        return ""
    # Replace contents inside <span class="xuetangx-com-encrypted-font">...</span>
    pattern = r'(<span class="xuetangx-com-encrypted-font">)([^<]+)(</span>)'
    def repl(match):
        return decrypt_text(match.group(2))
    decrypted_html = re.sub(pattern, repl, html)
    # Strip HTML tags for clean text
    clean_text = re.sub(r'<[^>]+>', '', decrypted_html).strip()
    # Unescape HTML entities
    import html as html_lib
    clean_text = html_lib.unescape(clean_text)
    # Replace multiple whitespaces/newlines with single space
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

problems = response_data["data"]["problems"]
decrypted_problems = []

for p in problems:
    idx = p["index"]
    prob_id = p["problem_id"]
    content = p["content"]
    q_type = content["Type"]
    
    body_raw = content.get("Body", "")
    body_decrypted = decrypt_html(body_raw)
    
    options = []
    if "Options" in content:
        for opt in content["Options"]:
            opt_key = opt.get("key", "")
            opt_val_raw = opt.get("value", "")
            opt_val_decrypted = decrypt_html(opt_val_raw)
            options.append({
                "key": opt_key,
                "value": opt_val_decrypted
            })
            
    decrypted_problems.append({
        "index": idx,
        "problem_id": prob_id,
        "type": q_type,
        "body": body_decrypted,
        "options": options
    })

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(decrypted_problems, f, ensure_ascii=False, indent=2)

print(f"Decrypted {len(decrypted_problems)} problems and saved to {output_path}")
