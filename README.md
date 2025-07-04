# arXiv LLM Research Assistant

A web-based research assistant that combines **semantic search**, **LLMs**, and **arXiv papers** to help you quickly explore cutting-edge research.

Built using:
- Elasticsearch for vector-based paper retrieval
- OpenAI GPT for summarization
- Flask for a web interface
- Google BigQuery for scalable scientific data ingestion

---

## What It Does

- Accepts a **natural language research question** (e.g. _"What are the latest methods for fine-tuning LLMs on small datasets?"_)
- Searches relevant arXiv papers using keyword relevance
- Builds a contextual prompt from summaries of the top papers
- Uses GPT-4 to generate a high-quality, concise answer
- Displays **citations** to the papers used in the answer

---

## Demo Screenshot

![demo screenshot](images/demo_pic.png) <!-- You can add your own screenshot here -->



## Getting Started

### 1. Prerequisites

- Python 3.11
- A running instance of Elasticsearch
- OpenAI API key
- Google Cloud credentials for BigQuery access (optional if using sample data)

---

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

### 3. Create an .env file

```
OPENAI_API_KEY=your-openai-key
GOOGLE_CLOUD_PROJECT=project-id
DOMAIN=cs-AI
```


### 4. Ingest data
Fetch paper metadata from BigQuery and index it into Elasticsearch:
```
python ingest.py
```

This will:

- Pull arXiv papers in your chosen domain from BigQuery

- Clean and deduplicate the data

- Index it into a local Elasticsearch instance under arxiv-papers

### 5. Run web app
```
python app.py
```