from llm import generate_answer

chunks = [
    "Machine learning is a branch of artificial intelligence "
    "that allows computers to learn patterns from data.",
    
    "Machine learning can be used for prediction, classification, "
    "and decision-making."
]

question = "What is machine learning?"

answer = generate_answer(question, chunks)

print(answer)