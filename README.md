# Arxiv-llm-rag: Semantic Search & Summarization of arXiv Papers using LLMs

A Retrieval-Augmented Generation (RAG) system that allows users to query technical topics in natural language and receive high-quality summaries of the most relevant arXiv papers. This project leverages modern LLMs, vector search with Elasticsearch, and structured data from BigQuery to accelerate scientific understanding.


## Use Case Example

> **User Query:** _"What are the recent advances in fine-tuning large language models with small datasets?"_

The system:
1. Embeds the query using OpenAI
2. Retrieves semantically relevant papers from an Elasticsearch vector index
3. Uses GPT-4 to generate a concise summary based on retrieved abstracts

---

## Architecture

```
    A[User Question] --> B[Embed with OpenAI]
    B --> C[Vector Search in Elasticsearch]
    C --> D[Retrieve Top-N Abstracts]
    D --> E[Build LLM Prompt]
    E --> F[LLM (e.g. GPT-4)]
    F --> G[Return Final Summary]