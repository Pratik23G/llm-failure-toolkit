# LLM Prompt Runner & Logging Harness  
**Pet Project 1 – Foundation for LLM Failure Analysis & Debugging Toolkit**

This repository contains **Project 1** of a multi-stage capstone focused on building an **LLM Failure Analysis & Debugging Toolkit**.

The purpose of this project is to create a **reliable prompt execution engine** and a **structured logging harness** that captures everything needed for downstream analysis (latency, metadata, outputs).

---

## 🎯 Project Goal

Build a simple but robust system that:

- Runs prompts/tasks against Large Language Models (LLMs)
- Measures execution metadata (timestamps, latency, model info)
- Logs every run in a structured format (JSONL)
- Serves as the **data backbone** for later failure analysis

This project focuses on **observability and infrastructure**, not evaluation yet.

---

## 🧠 Why This Matters

To debug LLM behavior, you must first **observe it**.

This logging harness enables future capabilities such as:
- Failure detection
- Hallucination analysis
- Prompt debugging
- Model comparison
- Automated reporting

---

## 🧩 Project Components

### Prompt Runner (`run.py`)
- CLI-based prompt execution
- Sends user prompts to an LLM
- Prints model responses
- Measures:
  - request timestamp (UTC)
  - execution latency
- Passes all data to the logger

---

### LLM Client (`llm/client.py`)
- Handles communication with the LLM provider
- Uses environment variables for API keys
- Abstracted to support multiple providers later

---

### Logging Harness (`logger/run_logger.py`)
- Receives prompt, response, and metadata
- Writes **one JSON object per run**
- Uses JSON Lines (`.jsonl`) format
- Designed for append-only logging and easy ingestion

---

### Run Data (`data/runs.jsonl`)
- Stores execution logs
- One line = one prompt run
- Not committed to version control

---

## 📁 Project Structure
llm-failure-toolkit/
│
├── run.py # Main prompt runner
├── llm/
│ └── client.py # LLM client abstraction
│
├── logger/
│ └── run_logger.py # Logging harness
│
├── data/
│ └── runs.jsonl # Runtime logs (gitignored)
│
├── README.md
└── requirements.txt



---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/llm-failure-toolkit.git
cd llm-failure-toolkit


2️⃣ Create and activate a virtual environment
python -m venv llmenv


Windows
=================
llmenv\Scripts\activate


macOS / Linux
=======================
source llmenv/bin/activate

3️⃣ Install dependencies
==============================
pip install -r requirements.txt

4️⃣ Configure environment variables
===================================
Create a .env file (not committed) and add your API key:
=================================
GEMINI_API_KEY=your_api_key_here


5️⃣ Run the prompt runner
========================
python run.py

---
## ---------------------------------------------------------------------------------------------- ##
** Pet Project-2 Validator of the model **
Verify what does the model, do different and check its failed cases, understand its failure points
Store the validation results, 
Update it into my jsons file

The whole objective is to validate the outputs given by the model

## Updated 📁 Project Structure

llm-failure-toolkit/
│
├── run.py # Main prompt runner
├── llm/
│ └── client.py # LLM client abstraction
|
|___ validators/
|   └── __init__.py
|   └── base.py
|   └── basic_validators.py
|
├── logger/
│ └── run_logger.py # Logging harness
│
├── data/
│ └── runs.jsonl # Runtime logs (gitignored)
│
├── README.md
└── requirements.txt