import os

chars_path = "/Users/lbyxiaolizi/Documents/Project/SYSU/ykt-auto/assets/common_chars.txt"
output_path = "/Users/lbyxiaolizi/Documents/Project/SYSU/ykt-auto/browser_decrypt.js"

with open(chars_path, 'r', encoding='utf-8') as f:
    common_chars_str = f.read().strip()

js_template = f"""(async () => {{
  console.log("Loading opentype.js from CDN...");
  
  const loadOpentype = () => new Promise((resolve, reject) => {{
    if (window.opentype) return resolve(window.opentype);
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/opentype.js@latest/dist/opentype.min.js';
    script.onload = () => resolve(window.opentype);
    script.onerror = (e) => reject("Failed to load opentype.js: " + e);
    document.head.appendChild(script);
  }});
  
  const getCustomFontUrl = () => {{
    for (const sheet of document.styleSheets) {{
      try {{
        for (const rule of sheet.cssRules) {{
          if (rule.type === CSSRule.FONT_FACE_RULE) {{
            const src = rule.style.getPropertyValue('src');
            if (src && src.includes('exam_font') && src.includes('.ttf')) {{
              const match = src.match(/url\\("?([^"]+)"?\\)/);
              if (match) return match[1];
            }}
          }}
        }}
      }} catch (e) {{}}
    }}
    return null;
  }};
  
  try {{
    const opentype = await loadOpentype();
    const customFontUrl = getCustomFontUrl();
    if (!customFontUrl) {{
      console.error("Custom font url not found in stylesheets!");
      return;
    }}
    
    console.log("Custom font URL found:", customFontUrl);
    console.log("Fetching custom font and standard reference font (思源黑体) from CDN...");
    
    const refFontUrl = "https://cdn.jsdelivr.net/gh/adobe-fonts/source-han-sans@release/OTF/SimplifiedChinese/SourceHanSansSC-ExtraLight.otf";
    
    const [customRes, refRes] = await Promise.all([
      fetch(customFontUrl),
      fetch(refFontUrl)
    ]);
    
    if (!customRes.ok || !refRes.ok) {{
      throw new Error("Failed to fetch fonts!");
    }}
    
    const [customBuf, refBuf] = await Promise.all([
      customRes.arrayBuffer(),
      refRes.arrayBuffer()
    ]);
    
    console.log("Parsing fonts using opentype.js...");
    const customFont = opentype.parse(customBuf);
    const refFont = opentype.parse(refBuf);
    
    console.log("Fonts parsed successfully. Custom glyphs:", customFont.numGlyphs, "Reference glyphs:", refFont.numGlyphs);
    
    // Load 3500 common characters
    const commonChars = {list(common_chars_str)};
    
    // Get CJK characters present in the custom font cmap
    const customCmap = customFont.cmap.glyphIndexMap;
    const customChars = [];
    for (const code in customCmap) {{
      const char = String.fromCodePoint(code);
      if (char >= '\\u4e00' && char <= '\\u9fff') {{
        customChars.push(char);
      }}
    }}
    
    console.log(`Custom font CJK characters to decrypt: ${{customChars.length}}`);
    
    // Helper to get 32x32 binary bitmap vector (as 32 Uint32 integers)
    const getGlyphVector = (font, char, size = 32) => {{
      const canvas = document.createElement('canvas');
      canvas.width = 48;
      canvas.height = 48;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, 48, 48);
      
      const glyph = font.charToGlyph(char);
      const path = glyph.getPath(8, 38, 36);
      ctx.fillStyle = '#FFFFFF';
      path.draw(ctx);
      
      const imgData = ctx.getImageData(0, 0, 48, 48);
      let minX = 48, maxX = 0, minY = 48, maxY = 0;
      for (let y = 0; y < 48; y++) {{
        for (let x = 0; x < 48; x++) {{
          const idx = (y * 48 + x) * 4;
          const val = imgData.data[idx];
          if (val > 30) {{
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (y < minY) minY = y;
            if (y > maxY) maxY = y;
          }}
        }}
      }}
      
      const resCanvas = document.createElement('canvas');
      resCanvas.width = size;
      resCanvas.height = size;
      const resCtx = resCanvas.getContext('2d');
      resCtx.fillStyle = '#000000';
      resCtx.fillRect(0, 0, size, size);
      
      if (maxX >= minX && maxY >= minY) {{
        resCtx.drawImage(canvas, minX, minY, maxX - minX + 1, maxY - minY + 1, 0, 0, size, size);
      }}
      
      const resImg = resCtx.getImageData(0, 0, size, size);
      const vector = new Uint32Array(32);
      for (let y = 0; y < 32; y++) {{
        let val = 0;
        for (let x = 0; x < 32; x++) {{
          const idx = (y * 32 + x) * 4;
          const isWhite = resImg.data[idx] > 127;
          if (isWhite) {{
            val |= (1 << (31 - x));
          }}
        }}
        vector[y] = val;
      }}
      return vector;
    }};
    
    console.log("Rendering reference characters to bitmaps...");
    const refVectors = [];
    const refCharsOk = [];
    for (const c of commonChars) {{
      try {{
        const vec = getGlyphVector(refFont, c);
        refVectors.push(vec);
        refCharsOk.push(c);
      }} catch (e) {{
        // Character might not exist in reference font
      }}
    }}
    
    console.log(`Rendered ${{refCharsOk.length}} standard reference characters.`);
    
    console.log("Rendering scrambled custom characters to bitmaps...");
    const customVectors = [];
    for (const c of customChars) {{
      const vec = getGlyphVector(customFont, c);
      customVectors.push(vec);
    }}
    
    console.log("Matching custom characters to reference characters (Jaccard popcount)...");
    
    const popcount = (v) => {{
      v = v - ((v >> 1) & 0x55555555);
      v = (v & 0x33333333) + ((v >> 2) & 0x33333333);
      return (((v + (v >> 4)) & 0xF0F0F0F) * 0x1010101) >> 24;
    }};
    
    const getJaccard = (v1, v2) => {{
      let intersection = 0;
      let union = 0;
      for (let i = 0; i < 32; i++) {{
        const a = v1[i];
        const b = v2[i];
        intersection += popcount(a & b);
        union += popcount(a | b);
      }}
      return union === 0 ? 0 : intersection / union;
    }};
    
    const mapping = {{}};
    const t0 = performance.now();
    for (let i = 0; i < customChars.length; i++) {{
      const s_char = customChars[i];
      const s_vec = customVectors[i];
      let bestJaccard = -1;
      let bestChar = s_char;
      
      for (let j = 0; j < refCharsOk.length; j++) {{
        const c_char = refCharsOk[j];
        const c_vec = refVectors[j];
        const jac = getJaccard(s_vec, c_vec);
        if (jac > bestJaccard) {{
          bestJaccard = jac;
          bestChar = c_char;
        }}
      }}
      mapping[s_char] = bestChar;
    }}
    const t1 = performance.now();
    console.log(`Font decryption finished in ${{ (t1 - t0).toFixed(2) }}ms!`);
    console.log("Character mapping:", mapping);
    
    // Auto decrypt the page
    console.log("Decrypting the page text DOM...");
    const spans = document.querySelectorAll('.xuetangx-com-encrypted-font');
    spans.forEach(span => {{
      const text = span.innerText;
      let decrypted = '';
      for (const char of text) {{
        decrypted += mapping[char] || char;
      }}
      span.innerText = decrypted;
      span.classList.remove('xuetangx-com-encrypted-font');
    }});
    
    console.log(`Decrypted ${{spans.length}} elements successfully!`);
    window.yktFontMapping = mapping; // Store globally for other scripts to use
    
  }} catch (err) {{
    console.error("Font decryption failed:", err);
  }}
}})();
"""

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(js_template)

print("browser_decrypt.js created successfully!")
