import json
import sys
import os

# Determine paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
answers_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/answers.json"))
output_path = os.path.abspath(os.path.join(SCRIPT_DIR, "../batch_run.js"))  # Output in the root of the project

if not os.path.exists(answers_path):
    print(f"Error: Answers file '{answers_path}' not found! Please place 'answers.json' in 'data/'.")
    exit(1)

with open(answers_path, 'r', encoding='utf-8') as f:
    answers = json.load(f)

# Generate JS code
js_code = f\"\"\"async () => {{
  const answers = {json.dumps(answers, ensure_ascii=False)};
  let answeredCount = 0;
  
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  
  while (true) {{
    const activeEl = document.querySelector('.subject-item.J_order.active');
    if (!activeEl) {{
      console.log('No active question element found.');
      break;
    }}
    const idxStr = activeEl.innerText.trim().split('\\\\n')[0]; // Handle cases where status labels are present
    const idx = parseInt(idxStr);
    if (isNaN(idx) || idx < 1 || idx > 75) {{
      console.log('Invalid index:', idxStr);
      break;
    }}
    
    const answer = answers[idxStr];
    if (answer === undefined) {{
      console.log('No answer found for index:', idxStr);
      break;
    }}
    
    console.log(`Answering Question ${idxStr}...`);
    
    // Mimic human reading/thinking delay
    await sleep(1500 + Math.random() * 1500);
    
    // Detect question type from DOM
    const hasTextarea = !!document.querySelector('textarea') || !!window.UE;
    const hasCheckboxes = document.querySelectorAll('.el-checkbox').length > 0;
    const hasRadios = document.querySelectorAll('.el-radio.homeworkElRadio').length > 0;
    
    if (hasTextarea && (idx >= 71 && idx <= 75)) {{
      // ShortAnswer (UEditor)
      const activeEd = Object.values(window.UE.instants).find(ed => ed.container && ed.container.offsetWidth > 0 && ed.container.offsetHeight > 0);
      if (activeEd) {{
        // Format newline with <br> for HTML rendering
        const formattedAnswer = answer.replace(/\\\\n/g, '<br>');
        activeEd.body.innerHTML = formattedAnswer;
        activeEd.fireEvent('contentchange');
        await sleep(1000);
      }} else {{
        const ta = document.querySelector('textarea');
        if (ta) {{
          ta.value = answer;
          ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
          await sleep(1000);
        }} else {{
          console.log('No editor found for subjective question.');
          break;
        }}
      }}
    }} else if (hasCheckboxes) {{
      // MultipleChoice
      const targetKeys = Array.isArray(answer) ? answer : [answer];
      const checkboxes = Array.from(document.querySelectorAll('.el-checkbox'));
      for (const key of targetKeys) {{
        const label = checkboxes.find(el => el.innerText.trim().startsWith(key));
        if (label) {{
          if (!label.classList.contains('is-checked')) {{
            label.click();
            await sleep(250 + Math.random() * 250);
          }}
        }}
      }}
    }} else if (hasRadios) {{
      // SingleChoice or Judgement
      const radios = Array.from(document.querySelectorAll('.el-radio.homeworkElRadio'));
      if (idx >= 61 && idx <= 70) {{
        // Judgement
        const targetIndex = (answer === 'true' || answer === true) ? 0 : 1;
        if (targetIndex < radios.length) {{
          radios[targetIndex].click();
          await sleep(250 + Math.random() * 250);
        }}
      }} else {{
        // SingleChoice
        const label = radios.find(el => el.innerText.trim().startsWith(answer));
        if (label) {{
          label.click();
          await sleep(250 + Math.random() * 250);
        }}
      }}
    }}
    
    // Sleep before clicking submit
    await sleep(1000 + Math.random() * 1000);
    
    // Click Submit
    const buttons = Array.from(document.querySelectorAll('button, .el-button'));
    const submitBtn = buttons.find(b => b.innerText.trim() === '提交' || b.innerText.trim() === '已提交');
    if (submitBtn) {{
      if (submitBtn.innerText.trim() === '提交') {{
        submitBtn.click();
      }}
      answeredCount++;
      
      // Wait for transition
      let changed = false;
      for (let attempt = 0; attempt < 30; attempt++) {{
        await sleep(200);
        const newActiveEl = document.querySelector('.subject-item.J_order.active');
        if (newActiveEl) {{
          const newIdxStr = newActiveEl.innerText.trim().split('\\\\n')[0];
          if (newIdxStr !== idxStr) {{
            changed = true;
            break;
          }}
        }}
      }}
      
      if (!changed) {{
        if (idx === 75) {{
          console.log('All questions answered successfully!');
        }} else {{
          console.log('Transition failed or stopped.');
        }}
        break;
      }}
    }} else {{
      console.log('Submit button not found.');
      break;
    }}
  }}
  return {{ answeredCount }};
}}()\"\"\"

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(js_code)

print(f"Batch script generated at {output_path}")
