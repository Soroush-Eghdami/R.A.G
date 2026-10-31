"""Framework-free RAG engine.

This package must not import Django. The Django apps own HTTP, validation and
persistence; everything about loading, chunking, embedding, retrieval and
generation lives here so it can be tested and reused from scripts.
"""
