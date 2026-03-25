# Dodge AI Graph Explorer

A full-stack application for visualizing and querying enterprise Order-to-Cash (O2C) data. It allows users to view a large-scale Force-Directed Graph of Sales Orders, Deliveries, Billing Documents, and Journal Entries, and includes an intelligent Chat Agent powered by Gemini that answers analytical queries.

## 🚀 Features
- **Stunning UI**: A beautiful, modern dark-themed interface built with React and Vite.
- **Graph Visualization**: High-performance 2D force-directed canvas that renders thousands of interconnected business documents in real time.
- **LLM AI Copilot**: A conversational agent built with LangChain and Google Gemini, configured with custom tools to deeply analyze the O2C flow.
    - Example 1: `Which products are associated with the highest number of billing documents?`
    - Example 2: `Please trace the flow of Sales Order ...`
    - Example 3: `Identify sales orders that have broken flows.`
- **Guardrails**: The LLM will politely reject off-topic questions (e.g., general knowledge) per the system prompt.

## 🏗 Architecture
- **Backend (Python / FastAPI)**: 
  - Loads provided `.jsonl` data sets into a custom `NetworkX` Graph database.
  - Exposes `/api/graph` for visualizing the structural diagram.
  - Exposes `/api/chat` equipped with LangChain tools (`get_top_products_by_billing`, `trace_flow`, `get_broken_flows`).
- **Frontend (React / Vite)**: 
  - `react-force-graph-2d` for interactive 2D graph visual exploration.
  - Contextual Chat Sidebar for natural language queries.

## 🛠 Prerequisites
- Node.js (v18+)
- Python (3.9+)

## 💻 Installation & Setup

### 1. Backend Setup
Navigate to the `backend` directory, create a virtual environment, install dependencies, and start the API context:
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows (or source venv/bin/activate on macOS/Linux)

pip install fastapi uvicorn pydantic networkx pandas langchain langchain-core langchain-google-genai

# Start the uvicorn development server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
Navigate to the `frontend` directory, install packages, and spin up Vite.
```bash
cd frontend
npm install
npm run dev
```

### 3. API Keys
To use the Dodge AI Chat functionalities, set your [Google Gemini API Key](https://aistudio.google.com/app/apikey) in your terminal session before starting the backend:
```bash
$env:GEMINI_API_KEY="your_api_key_here"
```

## 📸 Screenshots & Usage
Launch your browser at `http://localhost:5173/`. You can click on specific nodes in the graph to automatically inspect their payload data in the Chat Interface, or just type a question to get AI-driven insights!
