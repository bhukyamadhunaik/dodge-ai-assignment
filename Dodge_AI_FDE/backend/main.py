from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx
import os

from graph_builder import build_graph
from llm_agent import chat, set_graph

app = FastAPI(title="Dodge AI FDE Graph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load graph into memory
try:
    G = build_graph()
    set_graph(G)
    print(f"Graph loaded successfully with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
except Exception as e:
    print(f"Failed to load graph: {e}")
    G = nx.DiGraph()

class ChatRequest(BaseModel):
    query: str

@app.get("/api/graph")
def get_graph_data():
    """Return the graph in a format suitable for react-force-graph"""
    nodes = []
    edges = []
    
    for node, data in G.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node, # Display name
            "type": data.get("type", "Unknown"),
            "data": data
        })
        
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "relation": data.get("relation", "LINK")
        })
        
    return {
        "nodes": nodes,
        "links": edges
    }

@app.post("/api/chat")
def chat_with_graph(req: ChatRequest):
    """Conversational endpoint."""
    try:
        response_text = chat(req.query)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
