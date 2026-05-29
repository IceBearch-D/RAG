from retriever import AdvancedRetriever
r = AdvancedRetriever()
ctx = r.retrieve_context("Data Connector的作用是什么")
print("=== CONTEXT ===")
print(ctx)
