import google.generativeai as genai
import os
from dotenv import load_dotenv
from app.services.embeddings import retrieve_relevant_chunks, retrieve_relevant_graph_nodes

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def ask_about_dataset(question: str, profile: dict, graph_state: dict = None) -> dict:
    retrieval = retrieve_relevant_chunks(question, top_k=3)
    context = "\n\n".join(retrieval["chunks"])

    relevant_nodes = retrieve_relevant_graph_nodes(question, graph_state) if graph_state else []
    graph_context = "\n".join(relevant_nodes)

    prompt = f"""
You are an expert data analyst assistant with memory of the analytical session.
Answer using ONLY the information below. Be specific, cite actual numbers.
Reference past findings only if directly relevant to the question.

DATASET CONTEXT:
{context}

{"RELEVANT ANALYTICAL HISTORY:" + chr(10) + graph_context if graph_context else ""}

QUESTION: {question}

ANSWER:
"""
    # print(graph_context)  # debug print to verify graph context is being retrieved
    # response = "placeholder for model response"
    response = model.generate_content(prompt)
    return {
        "answer": response.text.strip(),
        "retrieved_sections": retrieval["retrieved_sections"],
        "context_used": retrieval["chunks"],
        "graph_nodes_used": relevant_nodes
    }