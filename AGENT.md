# AI Agent Operations Manual (AGENT.md)

This file provides instructions for AI agents (like yourself) to quickly understand and execute tasks in this workspace.

---

## 🤖 Method A: Direct Browser Decryption (Primary / Recommended)

Perform font decryption dynamically inside the browser tab without any local Python dependencies by executing the code in `browser_decrypt.js`.

### Execution Flow:
1. **Get Script**: Read `browser_decrypt.js` at the root of this workspace.
2. **Execute**: Call `evaluate_script` passing the entire contents of `browser_decrypt.js` to the target page context.
3. **Outcome**: 
   - Dynamically loads `opentype.js` from CDN.
   - Automatically detects the custom font URL from the stylesheet.
   - Fetches the standard reference font `SourceHanSansSC-ExtraLight.otf` from jsDelivr CDN.
   - Converts both fonts' glyph shapes into 32x32 binary matrices.
   - Encodes each 32x32 matrix into a `Uint32Array` of length 32 (each element representing a 32-bit row of pixels).
   - Computes Jaccard similarity between custom glyphs and the 3500 standard characters in less than **300ms** using optimized bitwise operations and a popcount/Hamming weight algorithm:
     ```javascript
     const popcount = (v) => {
       v = v - ((v >> 1) & 0x55555555);
       v = (v & 0x33333333) + ((v >> 2) & 0x33333333);
       return (((v + (v >> 4)) & 0xF0F0F0F) * 0x1010101) >> 24;
     };
     const getJaccard = (v1, v2) => {
       let intersection = 0;
       let union = 0;
       for (let i = 0; i < 32; i++) {
         const a = v1[i];
         const b = v2[i];
         intersection += popcount(a & b);
         union += popcount(a | b);
       }
       return union === 0 ? 0 : intersection / union;
     };
     ```
   - Automatically replaces scrambled text DOM elements on the page.
   - Stores the generated mapping globally as `window.yktFontMapping` for subsequent automation scripts to query.

---

## 🛠️ Method B: Local Python Decryption (Secondary / Alternative)

If direct browser execution is blocked or you need to inspect decrypted payloads locally:

### 1. Environment Setup
Always run commands within a virtual environment. If not present, initialize it:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt
```

### 2. Execution Commands
Execute these commands from the root directory of the workspace:

#### Rebuild Font Mapping (`font_mapping.json`)
Requires `data/font.ttf`, `assets/SourceHanSansSC-ExtraLight.otf`, and `assets/common_chars.txt`.
```bash
python src/decrypt_font.py
```
*Output location*: `data/font_mapping.json`

#### Decrypt Yuketang Questions (`decrypted_problems.json`)
Requires `data/font_mapping.json` and `data/exercise_response.json`.
```bash
python src/decrypt_problems.py
```
*Output location*: `data/decrypted_problems.json`

#### Generate Browser Console Script (`batch_run.js`)
Requires `data/answers.json`.
```bash
python src/gen_batch_js.py
```
*Output location*: `batch_run.js`

---

## 🌐 Browser Automation Integration (DevTools MCP)

If you have access to `chrome-devtools-mcp` or a browser automation agent:

1. **Locate Tab**: Call `list_pages` to locate the Yuketang exercise tab (URL match: `https://www.yuketang.cn/v2/web/cloud/student/exercise/*`).
2. **Get Javascript Code**: Read the generated `batch_run.js` file contents.
3. **Execute**: Call `evaluate_script` with the content of `batch_run.js` as the `function` body:
   ```javascript
   // Run the IIFE from batch_run.js
   async () => {
     // Paste content of batch_run.js here
   }
   ```
4. **UEditor RichText Input (ShortAnswer Q71-Q75)**:
   Yuketang subjective questions use a UEditor iframe. The JS code inside `batch_run.js` handles it via:
   ```javascript
   const activeEd = Object.values(window.UE.instants).find(ed => ed.container && ed.container.offsetWidth > 0 && ed.container.offsetHeight > 0);
   if (activeEd) {
     activeEd.body.innerHTML = answer.replace(/\n/g, '<br>');
     activeEd.fireEvent('contentchange');
   }
   ```

---

## 📂 Key Data Schema

### `data/answers.json`
An object mapping string question indexes (`"1"` to `"75"`) to their answers.
- **SingleChoice**: `"A"`
- **MultipleChoice**: `["A", "B", "C"]`
- **Judgement**: `"true"` or `"false"` (strings)
- **ShortAnswer**: String content with newlines (`\n`).

### `data/font_mapping.json`
A flat mapping dictionary `{ "scrambled_char": "decrypted_char" }`.
