from flask import Flask, request, jsonify
from llama_index.core import VectorStoreIndex
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, AutoModel
from PyPDF2 import PdfReader
from flask_cors import CORS
from functools import wraps
from dotenv import load_dotenv
from waitress import serve
import re, torch, jwt, os, json

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

model_path = "/app/legal_led_model"
model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)
model.save_pretrained("./legal_led_model")
tokenizer.save_pretrained("./legal_led_model")

model_name = "BAAI/bge-base-en-v1.5"
embed_model = AutoModel.from_pretrained(model_name)
embed_tokenizer = AutoTokenizer.from_pretrained(model_name)

Settings.embed_model = HuggingFaceEmbedding(model_name=model_name)
Settings.llm = Groq(model="llama3-8b-8192", api_key=os.getenv("GROQ_API_KEY"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index_chat = "llamaindex"
pinecone_index_retrieval = "judgment-search"

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["https://jurisight.onrender.com"])


def authenticate_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("x-auth-token")
        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401     
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token["id"]
            if not user_id:
                return jsonify({"error": "Invalid token structure"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(user_id, *args, **kwargs)
    return decorated_function

SYSTEM_PROMPT = (
    "You are Jurisight, a highly knowledgeable legal chatbot. Your purpose is to assist "
    "users with questions related to legal documents, laws, judgments, and legal topics. "
    "Do not answer questions unrelated to the legal domain. Provide accurate and concise "
    "legal responses based on your training and knowledge.\n\n"
    "If the user has uploaded a document, consider only the most recently uploaded document "
    "and its generated summary in your responses. Forget any previous documents or summaries "
    "when a new one is uploaded. If no document has been uploaded, do not assume otherwise.\n\n"
    "Maintain continuity by considering the chat history. If a user follows up on a previous question, "
    "use the past interactions for context rather than responding in isolation. However, "
    "do not reference any document unless one is currently available."
)

document_text_storage = {}
summarized_content = {}
context_text = ""
chat_history = {}

def extract_entities(text):
    """Extract structured data from text using AI."""
    llm = Groq(model="llama3-8b-8192", api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""Extract structured data (key-value pairs) from the following text and return valid JSON format.
    Only return values that are explicitly mentioned in the text. Do NOT infer missing values.

    {text}
    """

    try:
        response = llm.complete(prompt)  # Get AI response
        extracted_text = response.text.strip()

        # Extract only the JSON part (in case the model adds extra text)
        json_start = extracted_text.find("{")
        json_end = extracted_text.rfind("}") + 1
        json_data = extracted_text[json_start:json_end]
        return json.loads(json_data)
    except json.JSONDecodeError:
        return {}
    except AttributeError:
        return {}

@app.route('/chat', methods=['POST'])
@authenticate_user
def chat(user_id):
    global context_text, chat_history
    try:
        if not request.json or 'message' not in request.json:
            return jsonify({"error": "Invalid request format"}), 400

        user_message = request.json['message']
        document_text = document_text_storage.get(user_id, "")
        summary_text = summarized_content.get(user_id, "")
        if document_text and "Document Context:" not in context_text:
            context_text += f"Document Context:\n{document_text}\n\n"
        if summary_text and "Summarized Content:" not in context_text:
            context_text += f"Summarized Content:\n{summary_text}\n\n"
        chat_memory = "\n".join(chat_history.get(user_id, [])[-10:])
        formatted_message = f"{SYSTEM_PROMPT}\n\nDocument Context:\n{document_text}\n\nSummarized Content:\n{summary_text}\n\nChat History:\n{chat_memory}\nUser: {user_message}\nJurisight:"
        pinecone_index = pc.Index(pinecone_index_chat)
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        query_engine = index.as_query_engine()
        response = query_engine.query(formatted_message)
        chat_history.setdefault(user_id, []).append(f"User: {user_message}")
        chat_history[user_id].append(f"Jurisight: {response}")
        response = {"response": f"{response}"}
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500
    
@app.route('/summarize', methods=['POST'])
@authenticate_user
def summarize(user_id):
    def clean_text(text):
        # Remove excessive line breaks and whitespace
        cleaned_text = re.sub(r'\s+', ' ', text).strip()  # Collapse whitespace
        return cleaned_text

    def summarize_legal_document(document_text, chunk_size=1024, max_output_length=128):
        try:
            # Split text into chunks of `chunk_size`
            chunks = [document_text[i:i+chunk_size] for i in range(0, len(document_text), chunk_size)]
            summaries = []

            for chunk in chunks:
                # Tokenize and summarize each chunk
                inputs = tokenizer(
                    chunk,
                    max_length=chunk_size,
                    padding="max_length",
                    truncation=True,
                    return_tensors="pt"
                )
                summary_ids = model.generate(
                    inputs["input_ids"],
                    num_beams=4,
                    max_length=max_output_length,
                    early_stopping=True
                )
                summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
                summaries.append(summary)

            # Combine summaries of all chunks
            return " ".join(summaries)
        except Exception as e:
            raise

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty file uploaded"}), 400

    try:
        # Extract text from PDF
        reader = PdfReader(file)
        document_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                document_text += text.strip() + " "

        # Clean and validate extracted text
        document_text = clean_text(document_text)

        if not document_text or len(document_text.split()) < 10:
            return jsonify({"error": "The document does not contain sufficient readable text."}), 400
        
        # Store the extracted text for retrieval
        document_text_storage[user_id] = document_text

        # Summarize the document
        summary = summarize_legal_document(document_text)
        summarized_content[user_id] = summary
        return jsonify({"summary": summary}), 200

    except Exception as e:
        return jsonify({"error": "Error processing the file"}), 500
    
@app.route('/retrieve-cases', methods=['POST'])
@authenticate_user
def retrieve_cases(user_id):
    def generate_embedding(text):
        inputs = embed_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            embeddings = embed_model(**inputs).last_hidden_state.mean(dim=1)
        return embeddings.squeeze().numpy()
    
    def query_pinecone(query_text, top_k=10):
        query_embedding = generate_embedding(query_text)
        retrieval_index = pc.Index(pinecone_index_retrieval)
        results = retrieval_index.query(vector=query_embedding.tolist(), top_k=top_k, include_metadata=True)
        return results
    
    if not request.json:
        return jsonify({"error": "No file or query provided"}), 400
    
    document_text = document_text_storage.get(user_id, None)
    if not document_text:
        return jsonify({"error": "No document available for retrieval"}), 400
    
    try:
        top_k = request.json.get('top_k', 10)
        results = query_pinecone(document_text, top_k=top_k)
        if not results['matches']:
            return jsonify({"error": "No relevant cases found."}), 200
        case_links = [{"score": result['score'], "url": result['metadata']['url']} for result in results['matches']]
        return jsonify({"case_links": case_links}), 200
    
    except Exception as e:
        return jsonify({"error": "Error processing the file"}), 500
    

@app.route('/fetch-form-data', methods=['GET'])
@authenticate_user
def fetch_form_data(user_id):
    """Fetch structured data from the stored document text and return it as JSON."""
    if user_id not in document_text_storage:
        return jsonify({"error": "No document found"}), 400

    extracted_data = extract_entities(document_text_storage[user_id])  # Extract structured data from PDF text

    return jsonify(extracted_data), 200
    
if __name__ == '__main__':
    serve(app, host="127.0.0.1", port=3001)
