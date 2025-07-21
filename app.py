from flask import Flask, jsonify, request
from flask_cors import CORS
from modules.rag import rag
from modules.rag_evaluator import RAGEvaluator
import psycopg2
import os
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

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

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "RAG API is running"})

@app.route("/api/query", methods=["POST"])
def process_query():
    """Process RAG query and return answer"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or not data.get("query"):
            return jsonify({"error": "Query is required"}), 400
        
        query = data.get("query").strip()
        
        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
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
        
        return jsonify({
            "success": True,
            "query": query,
            "answer": answer,
            "query_id": query_id
        })
        
    except Exception as e:
        print(f"[Query Processing Error]: {e}")
        return jsonify({
            "success": False,
            "error": f"An error occurred while processing your query: {str(e)}"
        }), 500

@app.route("/api/queries", methods=["GET"])
def get_recent_queries():
    """Get recent queries (optional endpoint for history)"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, query, answer, relevance, confidence_score, created_at
            FROM queries 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        
        rows = cur.fetchall()
        
        queries = []
        for row in rows:
            queries.append({
                "id": row[0],
                "query": row[1],
                "answer": row[2],
                "relevance": row[3],
                "confidence_score": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            })
        
        cur.close()
        conn.close()
        
        return jsonify({"queries": queries})
        
    except Exception as e:
        print(f"[Queries Fetch Error]: {e}")
        return jsonify({"error": "Failed to fetch queries"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)