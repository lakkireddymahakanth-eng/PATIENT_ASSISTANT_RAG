# 🏥 Patient Assistant RAG

A voice-enabled, multimodal AI health assistant powered by a local RAG (Retrieval-Augmented Generation) pipeline. Ask health questions using your **voice**, **images**, or through the **web/CLI interface** — and get intelligent answers grounded in real clinical medical documents.

> ⚠️ **Disclaimer:** This tool is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎙️ Voice Input / Output | Speak your question and hear the answer — powered by Whisper + gTTS |
| 🖼️ Image Scanning | Upload medical images for OCR-based text extraction and analysis |
| 📄 Report Analysis | Upload and analyze medical reports and PDF documents |
| 🧠 RAG Pipeline | Retrieves answers from real diabetes & clinical guideline documents |
| 🗄️ Patient Memory | Stores patient context and history across sessions |
| 🌐 Web Interface | Streamlit-based web UI |
| 💻 CLI Interface | Command-line interface for terminal users |
| 🐳 Docker Support | Fully containerized with Docker Compose |

---

## 🗂️ Project Structure

```
PATIENT_ASSISTANT_RAG/
│
├── data/
│   └── patients.json                   # Patient data store
│
├── Medical_documents/                  # Knowledge base (PDFs fed into RAG)
│   ├── 20241107_Leitlinie_IWGDF.pdf
│   ├── CPOC-DiabetesGuideline2.pdf
│   ├── dc26sint.pdf
│   ├── Fundamentals_of_Diabetes.pdf
│   └── joslin-clinical-guidelines-fo.pdf
│
├── Patient_memory/                     # Persistent patient session memory
│
├── scripts/
│   ├── generate_patients.py            # Generates patient test data
│   └── index_documents.py             # Embeds & indexes medical docs into ChromaDB
│
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                 # App configuration and env variables
│   │
│   ├── core/                           # Core RAG logic (retrieval, LLM calls)
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                   # SQLAlchemy database models
│   │   └── repository.py              # Database access layer
│   │
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── cli.py                      # CLI interface
│   │   └── web.py                      # Streamlit web interface
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_service.py            # Image OCR processing
│   │   ├── patient_service.py          # Patient data management
│   │   ├── report_analysis.py          # Medical report analysis
│   │   ├── report_service.py           # Report retrieval and handling
│   │   └── voice_service.py            # Voice input/output (Whisper + gTTS)
│   │
│   ├── __init__.py
│   └── main.py                         # Application entry point
│
├── storage/
│   ├── chroma.sqlite3                  # ChromaDB persistent vector store
│   └── d47be8c2-ac1b-4e33-adaa-.../   # ChromaDB collection data
│
├── tests/                              # Test suite
├── uploads/                            # Runtime file uploads
├── docker/                             # Docker config files
├── docs/                               # Documentation
│
├── Dockerfile
├── compose.yml
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── response.mp3                        # Latest voice response output
├── temp_audio.wav                      # Temporary voice input recording
└── .env                                # Environment variables (not committed)
```

---

## 📚 Medical Knowledge Base

The RAG pipeline is grounded in the following real clinical documents:

| Document | Topic |
|---|---|
| `20241107_Leitlinie_IWGDF.pdf` | IWGDF Guidelines — Diabetic Foot Management |
| `CPOC-DiabetesGuideline2.pdf` | Clinical Practice — Diabetes Management |
| `dc26sint.pdf` | Diabetes Care Standards |
| `Fundamentals_of_Diabetes.pdf` | Core Diabetes Education |
| `joslin-clinical-guidelines-fo.pdf` | Joslin Clinic Clinical Guidelines |

> All documents are chunked, embedded, and stored in ChromaDB via `scripts/index_documents.py`. The current knowledge base is focused on **diabetes and related clinical guidelines**.

---

## 🧰 Tech Stack

### Core
| Component | Technology |
|---|---|
| LLM (local) | [Ollama](https://ollama.com/) |
| Vector Store | [ChromaDB](https://www.trychroma.com/) `0.4.24` |
| Web UI | [Streamlit](https://streamlit.io/) |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Config | python-dotenv |

### Multimodal Services
| Component | Technology |
|---|---|
| Voice Input | [OpenAI Whisper](https://github.com/openai/whisper) + SoundDevice + SciPy |
| Voice Output | [gTTS](https://gtts.readthedocs.io/) |
| Image OCR | Pytesseract + Pillow |
| PDF / Report Parsing | PyPDF |

### Infrastructure
| Component | Technology |
|---|---|
| Containerization | Docker + Docker Compose |
| Progress Tracking | tqdm |

---

## ⚙️ Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [Ollama](https://ollama.com/) running locally with models pulled:
  ```bash
  ollama pull llama3
  ollama pull nomic-embed-text
  ```
- Tesseract OCR installed on your system:
  ```bash
  # Ubuntu / Debian
  sudo apt install tesseract-ocr

  # macOS
  brew install tesseract

  # Windows
  # Download: https://github.com/UB-Mannheim/tesseract/wiki
  ```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/lakkireddymahakanth-eng/PATIENT_ASSISTANT_RAG.git
cd PATIENT_ASSISTANT_RAG
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
EMBEDDING_MODEL=nomic-embed-text
CHROMA_PERSIST_DIR=./storage
DATABASE_URL=sqlite:///./data/patients.db
```

### 3. Index the Medical Documents

Chunks and embeds all PDFs in `Medical_documents/` into ChromaDB:

```bash
python scripts/index_documents.py
```

> Only needs to be run once, or again whenever you add new documents.

### 4a. Run with Docker Compose (Recommended)

```bash
docker compose up --build
```

Open your browser at: **http://localhost:8501**

### 4b. Run Locally (Development)

```bash
pip install -r requirements.txt
streamlit run src/main.py
```

### 4c. Run via CLI

```bash
python -m src.interfaces.cli
```

---

## 🧠 How the RAG Pipeline Works

```
User Input
(voice / text / image / PDF)
        │
        ▼
┌──────────────────────┐
│   Text Extraction    │  ← Whisper (voice) / Tesseract (image) / PyPDF (PDF)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Query Embedding    │  ← Ollama embedding model
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Vector Search      │  ← ChromaDB (chroma.sqlite3)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Context + Memory    │  ← Retrieved chunks + Patient_memory injected
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    LLM Response      │  ← Ollama (llama3)
└──────────┬───────────┘
           │
           ▼
  Answer (text + optional voice via gTTS → response.mp3)
```

---

## 🎙️ Voice Feature

- **Input**: Microphone records audio → saved as `temp_audio.wav` → transcribed by Whisper
- **Output**: LLM response is converted to speech → saved as `response.mp3` → played back

Handled by `src/services/voice_service.py`. Make sure your microphone is accessible when running locally or inside Docker.

---

## 🖼️ Image & Report Scanning

| Service | What it does |
|---|---|
| `image_service.py` | OCR text extraction from medical images via Tesseract + Pillow |
| `report_service.py` | Loads and retrieves medical report content |
| `report_analysis.py` | Analyses document content and feeds it into the RAG pipeline |

Supported formats: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.pdf`

---

## 🗄️ Patient Data & Memory

- **`data/patients.json`** — Stores patient records used for context
- **`Patient_memory/`** — Persists session memory per patient across conversations
- **`src/database/models.py`** — SQLAlchemy models for structured patient data
- **`src/services/patient_service.py`** — Handles all patient data operations
- **`scripts/generate_patients.py`** — Generates sample patient data for testing

Patient ID is used internally to load memory and personalise responses.

---

## 🐳 Docker Details

```yaml
# Services in compose.yml
app:        port 8501   # Streamlit Web UI
chromadb:   port 8002   # Vector store
```

Rebuild after code changes:

```bash
docker compose up --build --force-recreate
```

---

## 🧪 Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

---

## 🌍 Language Support

The current version is built and tested in **English only**.

Potential multilingual behaviour:
- **Whisper** (voice input) natively supports many languages and may transcribe non-English speech
- **gTTS** (voice output) supports multiple languages but is not yet configured in this version
- **LLM responses** depend on the Ollama model used — some models handle multiple languages better than others
- **Medical documents** in the knowledge base are in English, so non-English queries may return lower quality results

> Multilingual support has **not been tested** and is listed as a future enhancement.

---

## 📋 Roadmap

- [ ] Multilingual voice and text support
- [ ] Guest login + self-registration (new version in progress)
- [ ] Expanded knowledge base beyond diabetes guidelines (WHO, PubMed, MedlinePlus)
- [ ] Patient history dashboard
- [ ] Mobile-friendly UI

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

[MIT](LICENSE)
