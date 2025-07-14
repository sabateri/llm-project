from flask import Flask, render_template, request
from modules.rag import rag
from modules.rag_evaluator import RAGEvaluator
import psycopg2
import os
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)


# Initialize RAG evaluator
evaluator = RAGEvaluator()

# PostgreSQL connection config
POSTGRES_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "ragdb"),
    "user": os.getenv("POSTGRES_USER", "raguser"),
    "password": os.getenv("POSTGRES_PASSWORD", "ragpass"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

def log_query_to_postgres(query: str, answer: str):
    """Log user query and LLM answer to PostgreSQL, return query ID"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("INSERT INTO queries (query, answer) VALUES (%s, %s) RETURNING id;", (query, answer))
        query_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return query_id
    except Exception as e:
        print(f"[Postgres Logging Error]: {e}")
        return None

def evaluate_and_update_async(query: str, answer: str, query_id: int):
    """Asynchronously evaluate and update database"""
    try:
        evaluation = evaluator.evaluate_answer_async(query, answer)
        
        # Update database with evaluation
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE queries 
            SET relevance = %s, relevance_explanation = %s, confidence_score = %s, 
                accuracy = %s, completeness = %s, clarity = %s, evaluation_error = %s
            WHERE id = %s;
        """, (
            evaluation.relevance,
            evaluation.explanation,
            evaluation.confidence,
            evaluation.accuracy,
            evaluation.completeness,
            evaluation.clarity,
            evaluation.error,
            query_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[Evaluation Complete]: Query ID {query_id} - Relevance: {evaluation.relevance}")
        
    except Exception as e:
        print(f"[Async Evaluation Error]: {e}")

        
@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    query = ""
    
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            try:
                # Get RAG answer
                result = rag(query, top_k=5, model="o4-mini")
                answer = result["llm_answer"]
                
                # Log to database and get query ID
                query_id = log_query_to_postgres(query, answer)
                
                # Start async evaluation in background
                if query_id:
                    evaluation_thread = threading.Thread(
                        target=evaluate_and_update_async, 
                        args=(query, answer, query_id)
                    )
                    evaluation_thread.daemon = True
                    evaluation_thread.start()
                
            except Exception as e:
                answer = f"Error: {str(e)}"
                
    return render_template("index.html", answer=answer, query=query)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)