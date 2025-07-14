from flask import Flask, render_template, request
from modules.rag import rag
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# PostgreSQL connection config
POSTGRES_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "ragdb"),
    "user": os.getenv("POSTGRES_USER", "raguser"),
    "password": os.getenv("POSTGRES_PASSWORD", "ragpass"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

def log_query_to_postgres(query: str, answer: str):
    """Log user query and LLM answer to PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("INSERT INTO queries (query, answer) VALUES (%s, %s);", (query, answer))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Postgres Logging Error]: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    query = ""
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            try:
                result = rag(query, top_k=5, model="o4-mini")
                answer = result["llm_answer"]
                # Log to PostgreSQL
                log_query_to_postgres(query, answer)
            except Exception as e:
                answer = f"Error: {str(e)}"
    return render_template("index.html", answer=answer, query=query)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)