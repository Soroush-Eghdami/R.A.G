# t_vector.py

from rag.vectorstore import VectorStore
from rag.chunking import chunk_text

text = "Law governs society by setting rights and duties. A contract is a legally binding agreement."
chunks = chunk_text(text)

store = VectorStore()
store.add_documents(chunks)

query = "What is a contract?"
results = store.query(query)

print("\n🔍 Top Matching Chunks:")
for i, doc in enumerate(results, 1):
    print(f"{i}. {doc[:150]}...")
