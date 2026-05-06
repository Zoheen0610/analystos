import google.generativeai as genai
import os
from dotenv import load_dotenv
from app.services.embeddings import retrieve_relevant_chunks

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def ask_about_dataset(question: str, profile: dict) -> dict:
    # retrieve only relevant chunks — real RAG
    retrieval = retrieve_relevant_chunks(question, top_k=3)
    context = "\n\n".join(retrieval["chunks"])

    prompt = f"""
You are an expert data analyst assistant.
Answer the question using ONLY the dataset context provided below.
Do not reference columns or statistics not present in the context.
Be specific and cite actual numbers.

CONTEXT (retrieved sections: {[r['section'] for r in retrieval['retrieved_sections']]}):
{context}

QUESTION: {question}

ANSWER:
"""
    response = model.generate_content(prompt)

    return {
        "answer": response.text.strip(),
        "retrieved_sections": retrieval["retrieved_sections"],
        # tells you exactly what context Gemini saw
        "context_used": retrieval["chunks"]
    }