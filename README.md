# 雨课堂作业自动答题工具 (ykt-auto)

本项目提供了一套完整的雨课堂（Yuketang）课后作业解密与自动化答题方案。针对雨课堂采用的**动态字体混淆机制**和**答题频率限制**，本项目通过字形轮廓特征比对和控制台脚本模拟，实现高精度的题目还原与全自动答题。

---

## 🤖 AI Agent 快速上手

如果你是协助操作本仓库的 AI Agent，请优先阅读 [AGENT.md](AGENT.md)。它专门为 Agent 提供了：
- 一键配置环境与运行脚本的 Shell 命令行（优先推荐使用浏览器端 JS 解密）。
- 配合 `chrome-devtools-mcp` 运行浏览器自动化与 UEditor 富文本编辑器注入控制的代码参考。
- 输入输出文件（如 `answers.json` 和 `font_mapping.json`）的 JSON Schema 规格。

---

## 🛠️ 工作原理

1. **字体解密 (Font Decryption)**:
   雨课堂网页端通过动态生成 `.ttf` 字体文件，将页面上的关键汉字替换为加密的 unicode 编码。
   本项目提供两种解密途径：
   - **方法 A（主选 / 推荐）**：使用 `browser_decrypt.js`，借助 `opentype.js` 直接在浏览器沙箱内拉取字体二进制流，使用 HTML5 Canvas 绘制字形并利用高效的**整型位运算 popcount** 计算 Jaccard 相似度，在 200ms 内完成全页乱码的一键还原。无需任何本地 Python 依赖，最快最便捷。
   - **方法 B（次选 / 备选）**：利用本地 Python 环境的 `fontTools` 等库提取字形并使用 Jaccard 相似度算法生成映射。

2. **题目解密 (Problem Decryption)**:
   提取浏览器网络请求中的题目原始 JSON 数据（其中包含未解密的 unicode 乱码），配合生成的映射字典 `data/font_mapping.json`，还原为人类可读的题目和选项。

3. **控制台自动化答题 (Console Automation)**:
   生成适用于 Chrome 开发者工具控制台的 JS 脚本，全自动识别当前题目类型（单选、多选、判断、简答），支持模拟 UEditor 编辑器富文本写入。脚本自带**防检测机制**：
   - 模拟人类阅读/思考的随机延时（设置在 3~5 秒）。
   - 自动检测并等待提交完成的页面跳转。
   - 避免直接调用 `setContent()` 引发 UEditor 的富文本过滤报错，直接操作 iframe 内部的 DOM body。

---

## 📂 项目结构

```text
ykt-auto/
├── README.md                 # 说明文档
├── AGENT.md                  # AI Agent 快速操作手册
├── browser_decrypt.js        # (推荐/主选) 纯浏览器端运行的一键字形解密还原脚本
├── batch_run.js              # (自动生成) 用于粘贴到浏览器 Console 运行的答题脚本
├── src/                      # 核心脚本 (次选流程)
│   ├── decrypt_font.py       # 字体比对与映射表生成脚本
│   ├── decrypt_problems.py   # 题目乱码还原脚本
│   └── gen_batch_js.py       # 自动化控制台脚本生成器
├── assets/                   # 静态参考资源
│   ├── SourceHanSansSC-ExtraLight.otf  # 备用参考字体（思源黑体超细体）
│   └── common_chars.txt      # 3500 常用字字表
└── data/                     # 运行时数据
    ├── font.ttf              # 从雨课堂下载的当前动态加密字体
    ├── font_mapping.json     # 生成的解密字形映射表
    ├── answers.json          # 75 道题目的标准答案键值对
    ├── decrypted_problems.json  # 解密后的题目明细
    └── exercise_response.json   # 从 Chrome Network 拦截的原始题目 JSON 数据
```

---

## 🚀 快速开始

### 📍 方法 A：纯浏览器端一秒解密（主选/首选，无需配置Python环境）
1. 打开雨课堂答题页面。
2. 按下 `F12` 或右键选择“检查”，切换到 **控制台 (Console)** 面板。
3. 复制项目根目录下 `browser_decrypt.js` 中的全部代码。
4. 粘贴进控制台并回车运行。页面上的所有乱码将在一秒内自动变为正常可读的中文，且控制台会打印出解密后的字形映射表 `window.yktFontMapping`。

---

### 📍 方法 B：本地 Python 解密（次选/备选流程）

#### 1. 环境准备
确保已安装 Python 3，并安装相关依赖库：
```bash
pip install -r requirements.txt
```

#### 2. 步骤一：获取混淆字体
下载当前题目页面加载的 `.ttf` 字体文件，放入 `data/` 目录下并命名为 `font.ttf`。

#### 3. 步骤二：生成字符映射表
在终端运行：
```bash
python src/decrypt_font.py
```
这将在 `data/` 目录下生成 `font_mapping.json`。

#### 4. 步骤三：解密网络数据（可选）
将雨课堂包含题目数据的 Response 完整保存为 `data/exercise_response.json`，运行：
```bash
python src/decrypt_problems.py
```
这将在 `data/` 目录下生成 `decrypted_problems.json`。

#### 5. 步骤四：生成并运行答题脚本
1. 检查并确认 `data/answers.json` 答案文件正确无误。
2. 运行脚本生成器：
   ```bash
   python src/gen_batch_js.py
   ```
   这将在项目根目录下生成 `batch_run.js` 文件。
3. 将 `batch_run.js` 的内容复制到控制台（Console）中并回车运行，即可自动完成答题。

---

## ⚠️ 免责声明
本工具仅供网络安全及网页数据爬取相关技术的研究与学术交流使用。请勿在实际考试或违反学校规定的场景下使用。使用本脚本带来的一切后果由使用者本人承担。
