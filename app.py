from flask import Flask, render_template, request
from modules.rag import rag

app = Flask(__name__)

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
            except Exception as e:
                answer = f"Error: {str(e)}"

    return render_template("index.html", answer=answer, query=query)
    #return render_template("index.html", answer=answer, query=query, sources=result["sources"])

if __name__ == "__main__":
    app.run(debug=True)
