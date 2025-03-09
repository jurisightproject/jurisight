# Jurisight - Simplifying Your Path to Justice

## Overview
Jurisight is an AI-driven legal assistant that streamlines the process of preparing and filing online petitions. By leveraging advanced AI models and vector databases, Jurisight enables lawyers and legal professionals to efficiently summarize case reports, reference previous judgments, and predict case outcomes.

## Features
- AI-powered Chatbot: Uses Retrieval Augmented Generation (RAG) with LlamaIndex, Llama-3 from Groq and Pinecone vector database.
- Document Summarization: Automatically summarizes uploaded legal documents using the Longformer Encoder Decoder (LED) model which is fined tuned using Low Rank Adaptation method.
- Case Retrieval: Retrieves similar cases from a Pinecone vector database based on cosine similarity.
- Legal Predictions: Fine-tuned Llama-3 8B model predicts the type of petition to be filed and the chance of success.
- User Authentication: Secure login and signup using JWT-based authentication.
- Interactive UI: Web-based interface for easy interaction with the chatbot and document processing features.

## Tech Stack
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Node.js, Express.js, Flask
- **Database**: MongoDB (for chat history and user authentication)
- **AI Models**:
  - Llama-3 (Groq) for legal chatbot responses
  - LED model for document summarization
  - Pinecone for case retrieval
- **Web Scraping**: BeautifulSoup for extracting legal data from Indian Kanoon

## Installation & Setup

### Prerequisites
Ensure you have the following installed:
- Node.js
- Python 3.8+
- MongoDB
- Pinecone API Key
- Groq API Key
- Google OAuth Credentials

### Steps
1. Clone the Repository:
   ```bash
   git clone https://github.com/jurisightproject/jurisight.git
   cd jurisight
   ```
2. Backend Setup:
   ```bash
   cd backend
   npm install
   .env  # Add required environment variables
   npm run dev
   ```
3. Flask API Setup:
   ```bash
   pip install -r requirements.txt
   python chatbot.py
   ```
4. Accessing app in local machine:
   Open `localhost:3000/login` in a browser.

## Usage
- Login/Register: Users must log in via email/password or Google OAuth.
- Chatbot Interaction: Enter legal queries and receive AI-generated responses.
- Document Upload: Upload case files for summarization and similar case retrieval.
- Petition Prediction: Receive AI-based recommendations for petition types and chances of success.

## File Structure
```
Jurisight/
├── index.js (Main server file)
│── middleware/
|   │── auth.js(middleware)
├── routes/
│   ├── auth.js (Authentication routes)
│   ├── chatbot.js (Chatbot API routes)
├── models/
│   ├── user.js (User Schema)
│   ├── chat.js (Chat History Schema)
│── chatbot.py (AI model logic)
│── public/
|   ├── login.html (login UI)
|   ├── login-style.css (login styles)
|   ├── signup.html (signup UI)
|   ├── signup-style.css (signup styles)
|   ├── draft.html (demo draft UI)
|   ├── draft.css (demo draft UI)
│   ├── index.html (Main page UI)
|   ├── style.css (Main page styles)
│   ├── script.js (Frontend logic)
│── .env (Environment Variables)
│── .gitignore (Files to be ignored when pushed to github)
│── Dockerfile
│── package.json (Node dependencies)
│── requirements.txt (Python dependencies)
```

## License
This project is licensed under the MIT License.

## Contact
For any issues or suggestions, reach out to **jurisightproject@gmail.com**.
