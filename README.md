# 🛡️ Hemas PharmaComply AI
**The Intelligent Compliance Hub for Regulatory Excellence.**

Hemas PharmaComply AI is a state-of-the-art compliance management ecosystem designed specifically for the pharmaceutical industry. It automates the ingestion and analysis of **NMRA (National Medicines Regulatory Authority) gazettes**, transforming dense legal text into actionable intelligence, priority deadlines, and risk-mitigated strategies.

---

## 🚀 The 5 Core Pillars

### 1. 💬 Q&A Assistant
*The system's primary interface for regulatory intelligence.*
- **Verified Source Cards**: Every AI response is backed by document citations.
- **Integrated PDF Viewer**: Click to view the exact page in the gazette immediately within the app.
- **Citation Copying**: One-click professional citation copying (e.g., "Source: Gazette 2341, Page 4") for reporting.
- **Smart Context Retrieval**: Uses advanced vector embeddings to find the most relevant clauses.

### 2. ⏰ Deadline Tracker
*Automated monitoring of pharmaceutical implementation timelines.*
- **Automated Extraction**: Scans new gazettes for dates and implementation deadlines.
- **Sync Dashboard**: A dedicated interface to ingest new documents and update your compliance calendar.
- **Urgency Metrics**: Visual indicators for upcoming deadlines.
- **Regex-Optimized Scanning**: Captures diverse regulatory date formats (e.g., "1st June 2026", "by 31st Dec").

### 3. 🛡️ Compliance Checker
*Assess proposed actions against current NMRA rules.*
- **Automated Risk Scoring**: Classifies actions as Low, Medium, or High Risk with logic-based audit trails.
- **Audit Trailing**: Maintains a log of all compliance checks performed.
- **Action Recommendations**: Suggests corrective measures for high-risk proposals.

### 4. 📊 Impact Predictor
*Predicting the financial and operational impact of new gazettes.*
- **Catalog Mapping**: Matches gazette price changes to Hemas product lists.
- **Price Delta Analysis**: Calculates the percentage change between current and new pricing.
- **Strategic Briefing**: Provides a summary of which products are most affected by new regulations.

### 5. 🔄 Change Detector
*Automated version comparison between new and previous price lists.*
- **Version Comparison**: Compares two uploaded documents to find additions, deletions, or modifications.
- **Contextual Categorization**: Automatically categorizes products based on their dosage forms or therapeutic classes.
- **Differential Reports**: Generates a clear summary of what has changed since the last gazette.

---

## ✨ Advanced Capabilities

### 📄 Smart OCR Reader (Tesseract Powered)
The system supports **Scanned PDF Documents**. 
- Using **pytesseract** and **pypdfium2**, it renders scanned pages into high-res images for text extraction.
- **Page-Level Accuracy**: Even in OCR mode, the system preserves page numbering for precise citations.

### 🔍 Verified Source Ingestion
- **Document Ingestion**: Automatically scans `./data/raw/` on startup.
- **Vector Storage**: Uses **ChromaDB** for lightning-fast retrieval of document chunks.
- **Persistent Memory**: Remembers your chat session for a cohesive research experience.

---

## 🛠️ Setup Guide (For ZIP Recipients)

If you have received this project as a ZIP file, follow these steps to get it running on your local machine:

### 1. Prerequisites (Mandatory)
You MUST have **Python 3.10 or higher** and **Tesseract OCR** installed.

> [!IMPORTANT]
> **Tesseract OCR Setup (Windows):**
> 1. Download the installer from: [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
> 2. Run the `.exe` and install to `C:\Program Files\Tesseract-OCR`.
> 3. **Add to PATH**: 
>    - Search for "Edit the system environment variables" in Windows Search.
>    - Click **Environment Variables** → Under 'System variables', select **Path** → **Edit** → **New**.
>    - Paste `C:\Program Files\Tesseract-OCR`.
> 4. **Restart**: Close and reopen your terminal or VS Code.

### 2. Installation Steps
1.  **Extract the ZIP**: Right-click the `.zip` file and select "Extract All...". Open the extracted folder in VS Code or Terminal.
2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration
1.  **GROQ API Key**: You need a GROQ API key to power the AI logic.
    -   Get one for free at: [console.groq.com](https://console.groq.com/).
2.  **Setup .env**: 
    -   Locate `.env.example` in the root folder.
    -   Copy it and rename it to `.env`.
    -   Open `.env` and paste your key: `GROQ_API_KEY=gsk_your_key_here`.

---

## 🏃‍♂️ Initial Operation Guide

1.  **Launch the App**:
    ```bash
    streamlit run app/main.py
    ```
2.  **Upload Gazettes**: Place any NMRA PDFs into the `data/raw/` directory.
3.  **The First Run**:
    -   The system will scan `data/raw/` and initialize the vector database (`vector_store_v2/`).
    -   Use the **Sidebar** to navigate between the 5 pillars.
    -   If you add a new file while the app is running, use the **Sync Documents** button in the **Deadline Tracker** module.

---

## 📁 Repository Blueprint

| File/Path | Purpose |
| :--- | :--- |
| `app/main.py` | Main Entry Point (Launch with `streamlit run`). |
| `app/pages/` | Housing for the 5 Feature Modules. |
| `config/config.yaml`| AI model and path configurations. |
| `data/raw/` | The "library" where your regulatory PDFs are stored. |
| `services/` | Logic for processing, chunking, and database management. |
| `utils/` | UI components and sidebar rendering. |

---

## ⚠️ Troubleshooting

- **"TesseractNotInstalled" error**: Ensure you followed the PATH setup in the Prerequisites section and restarted your terminal.
- **"GROQ_API_KEY" error**: Check that your `.env` file is named correctly (no `.txt` extension) and contains a valid key.
- **Slow Embedding**: The first time you ingest documents, it might take a moment to download the embedding model (`all-MiniLM-L6-v2`).

---

## 👥 Team PharmaComply

*   **T. Rahitha**  ([@Rahitha-Thangavel](https://github.com/Rahitha-Thangavel)) - *Architecture & Core AI*
*   **T. Archchika** ([@archchika02](https://github.com/archchika02)) - *Risk Evaluation & Audit*
*   **L.J. Thilukshika** ([@ThilukshikaLJ](https://github.com/ThilukshikaLJ)) - *Change Detection & Categorization*
*   **S. Thushanthi** ([@Thushanthi124](https://github.com/Thushanthi124)) - *Deadline Tracking & Sync*

---
*© Hemas Holdings. Developed for AI-THON 2026.*
