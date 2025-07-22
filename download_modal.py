# download_model.py
from transformers import pipeline
import torch

print("Downloading AI models. This will happen only once during the Docker build.")

# Check if a GPU is available and set the device accordingly
device = 0 if torch.cuda.is_available() else -1

# 1. Summarization model
print("Downloading summarizer: sshleifer/distilbart-cnn-6-6")
pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-6-6",
    device=device
)

# 2. NER model
print("Downloading NER model: dslim/bert-base-NER")
pipeline(
    "ner",
    model="dslim/bert-base-NER",
    device=device
)

# 3. ASR (Whisper) model
print("Downloading ASR model: openai/whisper-base.en")
pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base.en",
    device=device
)

# 4. Question-Answering model
print("Downloading QA model: distilbert-base-cased-distilled-squad")
pipeline(
    "question-answering",
    model="distilbert-base-cased-distilled-squad",
    device=device
)

print("All models have been downloaded successfully.")