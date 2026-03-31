# 🛡️ Hemas PharmaComply AI
**The Intelligent Compliance Hub for Regulatory Excellence.**

Hemas PharmaComply AI is a state-of-the-art compliance management ecosystem designed specifically for the pharmaceutical industry. It automates the ingestion and analysis of **NMRA (National Medicines Regulatory Authority) gazettes**, transforming dense legal text into actionable intelligence, priority deadlines, and risk-mitigated strategies.

---

## 🚀 The 5 Core Pillars

### 1. 💬 Q&A Assistant (Feature 1)
*The system's primary interface for regulatory intelligence.*
- **Verified Source Cards**: Every AI response is backed by document citations.
- **Integrated PDF Viewer**: Click to view the exact page in the gazette immediately.
- **Citation Copying**: One-click professional citation copying for reporting.
- **Smart Context Retrieval**: Uses advanced vector embeddings to find the most relevant clauses.

### 2. ⏰ Deadline Tracker (Feature 2)
*Automated monitoring of pharmaceutical implementation timelines.*
- **Automated Extraction**: Scans new gazettes for dates and implementation deadlines.
- **Sync Dashboard**: A dedicated interface to ingest new documents and update your compliance calendar.
- **Urgency Metrics**: Visual indicators for upcoming deadlines.
- **Regex-Optimized Scanning**: Captures diverse regulatory date formats (e.g., "1st June 2026", "by 31st Dec").

### 3. 🛡️ Risk Evaluator (Feature 3)
*Assess proposed actions against current NMRA rules.*
- **Automated Risk Scoring**: Classifies actions as Low, Medium, or High Risk.
- **Audit Trailing**: Maintains a log of all compliance checks performed.
- **Action Recommendations**: Suggests corrective measures for high-risk proposals.
- **Compliance Matrix**: Compares your query against vectorized regulatory constraints.

### 4. 📊 Impact Predictor (Feature 4)
*Predicting the financial and operational impact of new gazettes.*
- **Catalog Mapping**: Matches gazette price changes to Hemas product lists.
- **Price Delta Analysis**: Calculates the percentage change between current and new pricing.
- **Strategic Briefing**: Provides a summary of which products are most affected by new regulations.

### 5. 🔄 Change Detector (Feature 5)
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
- **Low-Quality Support**: Optimized to handle grainy or distorted scan textures common in official gazettes.

### 🔍 Verified Source Ingestion
- **Document Ingestion**: Automatically scans `data/raw/` on startup.
- **Vector Storage**: Uses **ChromaDB** for lightning-fast retrieval of document chunks.
- **Persistent Memory**: Remembers your chat session for a cohesive research experience.

---

## 🛠️ Prerequisites & Installation

### 1. External Dependencies (Mandatory)
To use the **OCR Reader** and **Change Detector**, you **MUST** install Tesseract OCR on your local device:

> [!IMPORTANT]
> **Tesseract OCR Setup (Windows):**
> 1. Download the installer from: [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
> 2. Run the `.exe` and install to `C:\Program Files\Tesseract-OCR`.
> 3. **Add to PATH**: Search for "Edit the system environment variables" → Environment Variables → Path → Edit → New → Add `C:\Program Files\Tesseract-OCR`.
> 4. **Restart**: Close and reopen your terminal/VS Code for the path to update.

- **Python**: 3.10+
- **Groq API Key**: Required for the LPU-accelerated AI logic.

### 2. Setup Guide
```bash
# Clone and Enter
git clone https://github.com/Rahitha-Thangavel/Hemas-PharmaComply-AI.git
cd Hemas-PharmaComply-AI

# Create Environment
python -m venv venv
.\venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

---

## 🏃‍♂️ Initial Operation Guide

1.  **Configure Environment**: Create a `.env` file in the root directory and add `GROQ_API_KEY=gsk_...`.
2.  **Add Your Gazettes**: Place any NMRA PDFs into `data/raw/`.
3.  **Launch**:
    ```bash
    streamlit run app/main.py
    ```
4.  **The First Run**:
    - The system will scan `data/raw/` and initialize the vector database (`vector_store_v2/`).
    - Use the **Unified Sidebar** on the left to navigate between the 5 pillars.
    - If you add a new file while the app is running, use the **Sync Documents** button in the **Deadline Tracker** module to process it.

---

## 📁 Repository Blueprint

| Directory/File | Purpose |
| :--- | :--- |
| `app/main.py` | Q&A Assistant entry point. |
| `app/pages/` | Housing for Dashboard, Compliance Checker, Impact Analysis, and Reports. |
| `app/core/` | The "brain" - LLM factory, embeddings, and prompt templates. |
| `data/raw/` | The "library" - Your regulatory PDFs go here. |
| `services/` | Shared logic for history management, file loading, and chunking. |
| `utils/` | UI logic for the premium sidebar and PDF rendering. |
| `config.yaml` | Application-wide settings (paths, model choice). |

---

## 👥 Team PharmaComply

*   **T. Rahitha**  ([@Rahitha-Thangavel](https://github.com/Rahitha-Thangavel)) - *Architecture & Core AI*
*   **T. Archchika** ([@archchika02](https://github.com/archchika02)) - *Risk Evaluation & Audit*
*   **L.J. Thilukshika** ([@ThilukshikaLJ](https://github.com/ThilukshikaLJ)) - *Change Detection & Categorization*
*   **S. Thushanthi** ([@Thushanthi124](https://github.com/Thushanthi124)) - *Deadline Tracking & Sync*

---
*© Hemas Holdings. Developed for AI-THON 2026.*
