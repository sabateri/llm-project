import os
from dotenv import load_dotenv
from google.cloud import bigquery
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# load_dotenv() # for local development

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "arxiv-trends")
DOMAIN = os.getenv("DOMAIN", "cs-AI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS= os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

bq_client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

def get_bq_data(domain=DOMAIN):
    domain_cleaned = domain.replace("-", "_").replace(".", "_")
    sql_query = f"""
    SELECT id, title, summary, author
    FROM `arxiv-trends.arxiv_papers.arxiv_papers_2000_2025_{domain_cleaned}`
    WHERE summary IS NOT NULL
    """
    query_job = bq_client.query(sql_query)
    return query_job.result().to_dataframe()

def clean_data(df):
    return df.drop_duplicates(subset=["id"])

def create_index(es, index_name):
    index_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "title": {"type": "text"},
                "summary": {"type": "text"},
                "author": {"type": "text"}
            }
        }
    }
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=index_mapping)

def generate_docs(df, index_name):
    for _, row in df.iterrows():
        yield {
            "_index": index_name,
            "_id": row["id"],
            "_source": {
                "id": row["id"],
                "title": row["title"],
                "summary": row["summary"],
                "author": row["author"]
            }
        }

def ingest_to_elasticsearch(df, es, index_name):
    create_index(es, index_name)
    bulk(es, generate_docs(df, index_name))

def ingest_pipeline():
    df = get_bq_data()
    df = clean_data(df)
    print(f"Cleaned data: {len(df)} rows")
    #es = Elasticsearch("http://localhost:9200") # for local development
    es = Elasticsearch("http://elasticsearch:9200")
    print('Ingesting to elastic search')
    ingest_to_elasticsearch(df, es, index_name="arxiv-papers")
    print('Data ingested')
if __name__ == "__main__":
    ingest_pipeline()
