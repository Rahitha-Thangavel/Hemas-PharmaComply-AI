# 🛡️ Hemas PharmaComply AI

**The Intelligent Compliance Hub for Regulatory Excellence.**

Hemas PharmaComply AI is a state-of-the-art compliance management system designed specifically for the pharmaceutical industry. It automates the processing of **NMRA (National Medicines Regulatory Authority) gazettes**, transforming complex regulatory documents into actionable insights, risk scores, and impact reports.

---

## 🎯 Core Modules

| Module | Description | Key Capabilities |
| :--- | :--- | :--- |
| **💬 Q&A Assistant** | The primary AI interface for querying regulations. | Verified citations, **Integrated PDF Viewer**, Citation Copying. |
| **⏰ Deadline Tracker** | Automated monitoring of regulatory implementation dates. | Regex-based date extraction, Email reminders, Urgency metrics. |
| **🛡️ Risk Evaluator** | Assessment of proposed actions against current rules. | Automated risk scoring (Low/Med/High), Audit trailing, Corrective actions. |
| **📊 Impact Predictor** | Analysis of price changes on product catalogs. | Automated mapping to Hemas products, Financial impact projection. |
| **🔄 Change Detector** | Comparison between new and previous gazette versions. | Automated categorization, smart version comparison, categorization. |

---

## ✨ Advanced Capabilities

### 📄 Smart OCR Reader
The system now supports **Scanned PDF Documents**. Using advanced OCR (Optical Character Recognition), the system can extract text and data from high-quality and low-quality scans alike, ensuring no regulatory change is missed.

### 🔍 Precision Citations
Every answer provided by the AI includes a **Verified Source Card**. You can:
- **Preview the Page**: View the exact page cited directly in the sidebar without leaving the app.
- **Copy Citation**: Instantly copy a professionally formatted reference for audit reports.

---

## 🛠️ Prerequisites

- **Python**: 3.10 or higher.
- **Tesseract OCR**: Required for processing scanned documents.
    - **Windows**: Download and install from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). Add `Tesseract-OCR` to your System PATH.
    - **Linux**: `sudo apt install tesseract-ocr`
    - **macOS**: `brew install tesseract`

---

## 📥 Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Rahitha-Thangavel/Hemas-PharmaComply-AI.git
    cd Hemas-PharmaComply-AI
    ```

2.  **Initialize Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    source venv/bin/activate # Linux/macOS
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment:**
    Create a `.env` file in the root directory:
    ```ini
    GROQ_API_KEY=your_groq_key_here
    OPENAI_API_KEY=your_openai_key_here  # Optional
    ```

---

## 🏃‍♂️ How to Run

1.  **Prepare Data**:
    Place your NMRA Gazette PDFs into the `data/raw/` directory.

2.  **Launch the System**:
    ```bash
    streamlit run app/main.py
    ```

3.  **Operate**:
    - Use the **Unified Sidebar** to switch between the Chatbot, Tracker, and Evaluator.
    - Use the **Dashboard** tab in the Deadline Tracker to sync and extract dates from newly added files.

---

## 📁 Project Structure

```text
Hemas-PharmaComply-AI/
├── app/
│   ├── core/               # Chatbot logic and config loaders
│   ├── features/           # Service-layer logic (Deadline, Risk, Impact, Change Detection)
│   ├── pages/              # Streamlit page modules
│   └── main.py             # Main Entry Point
├── data/
│   ├── raw/                # Input PDFs (Gazettes)
│   ├── temp_uploads/       # Temporary storage for comparison
│   └── deadlines_db.json   # Processed deadline records
├── services/               # Shared services (Audit, Notifications, History, Change Detector)
├── utils/                  # UI Utilities (Clean Sidebar, PDF rendering)
├── config/                 # YAML Configuration
└── requirements.txt        # Project Dependencies
```

---

## 👥 Team PharmaComply

*   **T. Rahitha**  ([@Rahitha-Thangavel](https://github.com/Rahitha-Thangavel))
*   **T. Archchika** ([@archchika02](https://github.com/archchika02))
*   **L.J. Thilukshika** ([@ThilukshikaLJ](https://github.com/ThilukshikaLJ))
*   **S. Thushanthi** ([@Thushanthi124](https://github.com/Thushanthi124))

---
*© 2025 Hemas Holdings. Developed for AI-THON 2026.*
