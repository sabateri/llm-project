import json
import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass
import openai
import os

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Structured evaluation result"""
    relevance: str
    explanation: str
    confidence: Optional[float] = None
    accuracy: Optional[str] = None
    completeness: Optional[str] = None
    clarity: Optional[str] = None
    error: Optional[str] = None

class RAGEvaluator:
    """Real-time RAG evaluation for production use"""
    
    def __init__(self, openai_api_key: str = None):
        self.client = openai.OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
        self.template = """
You are an expert evaluator for a RAG system that retrieves and answers questions about academic papers.

Your task is to evaluate the quality of the generated answer based on multiple criteria:

1. **Relevance**: Does the answer address the question asked?
2. **Accuracy**: Is the information provided factually correct?
3. **Completeness**: Does the answer provide sufficient detail?
4. **Clarity**: Is the answer well-structured and easy to understand?

Question: {question}
Generated Answer: {answer_llm}

Please provide your evaluation in JSON format:
{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Accuracy": "INACCURATE" | "PARTLY_ACCURATE" | "ACCURATE",
  "Completeness": "INCOMPLETE" | "PARTLY_COMPLETE" | "COMPLETE",
  "Clarity": "UNCLEAR" | "PARTLY_CLEAR" | "CLEAR",
  "Overall_Score": 1-5,
  "Explanation": "[Detailed explanation of your evaluation]"
}}
""".strip()
    
    def _clean_json_response(self, response: str) -> str:
        """Clean and extract JSON from LLM response"""
        # Remove code blocks
        response = re.sub(r'```json\s*|\s*```', '', response)
        response = re.sub(r'```\s*|\s*```', '', response)
        
        # Find JSON-like content
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return response.strip()
    
    def evaluate_answer(self, question: str, answer: str) -> EvaluationResult:
        """Evaluate a single question-answer pair"""
        
        prompt = self.template.format(question=question, answer_llm=answer)
        
        try:
            # Get LLM evaluation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            raw_response = response.choices[0].message.content
            
            # Clean and parse JSON
            clean_response = self._clean_json_response(raw_response)
            evaluation_dict = json.loads(clean_response)
            
            # Extract fields
            relevance = evaluation_dict.get('Relevance', 'UNKNOWN')
            explanation = evaluation_dict.get('Explanation', 'No explanation provided')
            confidence = evaluation_dict.get('Overall_Score', None)
            accuracy = evaluation_dict.get('Accuracy', None)
            completeness = evaluation_dict.get('Completeness', None)
            clarity = evaluation_dict.get('Clarity', None)
            
            return EvaluationResult(
                relevance=relevance,
                explanation=explanation,
                confidence=confidence,
                accuracy=accuracy,
                completeness=completeness,
                clarity=clarity
            )
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing evaluation: {e}")
            return EvaluationResult(
                relevance="UNKNOWN",
                explanation="Error during evaluation",
                error=str(e)
            )
    
    def evaluate_answer_async(self, question: str, answer: str) -> EvaluationResult:
        """Lightweight evaluation for real-time use"""
        
        # Simplified template for faster evaluation
        simple_template = """
Rate the relevance of this answer to the question on a scale:
- RELEVANT: Directly answers the question
- PARTLY_RELEVANT: Partially answers or tangentially related
- NON_RELEVANT: Does not answer the question

Question: {question}
Answer: {answer}

Respond with JSON: {{"Relevance": "RELEVANT|PARTLY_RELEVANT|NON_RELEVANT", "Score": 1-5}}
"""
        
        prompt = simple_template.format(question=question, answer=answer)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            raw_response = response.choices[0].message.content
            clean_response = self._clean_json_response(raw_response)
            evaluation_dict = json.loads(clean_response)
            
            return EvaluationResult(
                relevance=evaluation_dict.get('Relevance', 'UNKNOWN'),
                explanation="Quick evaluation",
                confidence=evaluation_dict.get('Score', None)
            )
            
        except Exception as e:
            logger.error(f"Error in async evaluation: {e}")
            return EvaluationResult(
                relevance="UNKNOWN",
                explanation="Quick evaluation failed",
                error=str(e)
            )