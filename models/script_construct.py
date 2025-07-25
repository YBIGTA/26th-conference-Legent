import os
import json
from hypergraphrag import HyperGraphRAG
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

rag = HyperGraphRAG(working_dir=f"data/graph")

with open(f"graph_contexts.json", mode="r") as f:
    unique_contexts = json.load(f)
    
rag.insert(unique_contexts)