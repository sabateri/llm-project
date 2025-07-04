from elasticsearch import Elasticsearch
from openai import OpenAI
from dotenv import load_dotenv
import os


load_dotenv()

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "arxiv-trends")
DOMAIN = os.getenv("DOMAIN", "cs-AI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

es = Elasticsearch("http://localhost:9200")
llm_client = OpenAI()
INDEX_NAME = "arxiv-papers"

def search_papers(query, top_k=10):
    text_query = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^0.5", "summary"],
                "type": "best_fields"
            }
        },
        "size": top_k
    }
    response = es.search(index=INDEX_NAME, body=text_query)
    return [
        {
            "score": hit["_score"],
            "id": hit["_source"]["id"],
            "title": hit["_source"]["title"],
            "summary": hit["_source"]["summary"],
            "author": hit["_source"]["author"]
        }
        for hit in response["hits"]["hits"]
    ]

def build_prompt(query, relevant_papers):
    context = "\n\n".join([
        f"id: {paper['id']}\nPaper: {paper['title']}\nSummary: {paper['summary']}"
        for paper in relevant_papers
    ])
    return f"""
    Based on the following research paper summaries, answer the question: {query}
    
    Context:
    {context}
    
    Answer:
    """

def llm(prompt, relevant_papers, model="gpt-4"):
    response = llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "llm_answer": response.choices[0].message.content,
        "sources": relevant_papers
    }

def rag(query, top_k=5, model="gpt-4"):
    relevant_papers = search_papers(query, top_k)
    prompt = build_prompt(query, relevant_papers)
    return llm(prompt, relevant_papers, model)
