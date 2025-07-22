# LexiScribe: AI-Powered Legal Analysis Suite ⚖️

![Python Version](https://img.shields.io/badge/python-3.9+-blue?style=for-the-badge&logo=python)
![Backend](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi)
![Frontend](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow?style=for-the-badge)

An intelligent paralegal that ingests legal documents (text or audio) and automatically generates a rich, interactive analysis.

[**► View Live Demo on Hugging Face Spaces**](https://huggingface.co/spaces/yogeshbawankar03/lexiscribe-frontend)

---

<img width="1919" height="1079" alt="Screenshot 2025-07-22 212222" src="https://github.com/user-attachments/assets/b5bcf492-2c12-4e0e-8c79-bc319ff9d127" />
<img width="1919" height="1079" alt="Screenshot 2025-07-22 212234" src="https://github.com/user-attachments/assets/fcebb4de-d33b-484a-ae43-f9839b246425" />

## The Problem 🏛️

The legal discovery process is a notorious bottleneck in litigation. It involves countless hours of manual transcription, document review, and entity collation—a workflow that is inefficient, expensive, and prone to human error. **LexiScribe** is engineered to dismantle this multi-billion-dollar inefficiency by automating the entire analysis pipeline.

---

## ✨ Key Features

* 🗣️ **Multimodal Analysis:** Upload raw text or audio recordings for a complete, end-to-end analysis.
* 🎙️ **Automatic Speech Recognition:** High-accuracy audio transcription with word-level timestamps, powered by OpenAI's Whisper.
* ✍️ **Abstractive Summarization:** Get concise, AI-generated summaries of complex legal documents, saving hours of reading time.
* 🔍 **Key Entity Recognition:** Automatically identify and extract key entities like **Organizations**, **Persons**, and **Locations**.
* 🖱️ **Interactive Analysis:** Click any recognized entity to instantly highlight all its mentions throughout the document.
* 📚 **Legal Citation Lookup:** Automatically detects legal citations and provides their full text in an expandable view.
* 💬 **Question-Answering System:** Ask specific questions about the document in plain English and get instant, context-aware answers.
* 🔐 **User Accounts & History:** Secure user authentication with persistent analysis history for every user.

---

## 🛠️ Technology Stack & Architecture

LexiScribe is built on a modern, robust stack designed for high-performance AI applications.

| Component | Technology | Justification |
|---|---|---|
| **🧠 AI Core** | Hugging Face Transformers | Unified access to state-of-the-art, pre-trained models. |
| **⚙️ Backend** | FastAPI | High-performance, asynchronous REST API for serving ML models. |
| **🎨 Frontend** | Streamlit | Rapid development of rich, interactive UIs using only Python. |
| **💾 Database** | SQLite | Simple, serverless, file-based database perfect for this scale. |
| **🔒 Security** | Passlib & Bcrypt | Robust, industry-standard password hashing for user authentication. |
| **🚀 Deployment** | Hugging Face Spaces | Free, seamless, and integrated hosting for ML applications. |

### The AI Cognitive Chain ⛓️

When a file is uploaded, it's processed through a chain of Hugging Face transformer models:

1.  **Input:** User Uploads Audio/Text File.
2.  **ASR:** `whisper-base.en` transcribes audio to text (if applicable).
3.  **Parallel Processing:** The text is fed simultaneously to:
    * **Summarization Model:** `distilbart-cnn-6-6`
    * **NER Model:** `bert-base-NER`
4.  **Interactive QA:** A `distilbert-base-cased-squad` model is used on-demand for the question-answering feature.
5.  **Output:** Rich, Interactive Analysis in the UI.

---

## 🚀 Getting Started Locally

Follow these steps to get your own local copy of LexiScribe up and running.

1. Clone the Repository

```bash
git clone https://github.com/yogeshbawankar/Lexi-Synth-Pro.git
cd Lexi-Synth-Pro
```

2. Set Up a Virtual Environment
For Windows:

```
python -m venv venv
.\venv\Scripts\activate
```
For macOS/Linux:
Bash
```
python3 -m venv venv
source venv/bin/activate
```
3. Install Dependencies
Bash
```
pip install -r requirements.txt
```
4. Run the Application
You'll need two separate terminals to run the backend and frontend servers.

  Terminal 1: Start the Backend API
  Bash
```
uvicorn main:app --reload
```
The backend will be live at http://127.0.0.1:8000.

Note: On the first run, it will download the necessary AI models and create the lexisynth.db database. This may take a few minutes.

  Terminal 2: Start the Frontend UI
  Bash
```
streamlit run streamlit_app.py
```
Navigate to the URL provided by Streamlit (usually http://localhost:8501) in your browser to start using the app!
