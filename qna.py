from transformers import pipeline

qa_model = pipeline("question-answering")
question = "Help me to summarize the context."
context = "The answer of question 'What is the total coverage count at policy issue City Cebu?' is [{'SUM(COVERAGE_COUNT)': 5076}]"
qa_response = qa_model(question = question, context = context)
print(qa_response)

# from transformers import pipeline

# classifier = pipeline("summarization", min_length=28, max_length=30)
# print(classifier("What is the total coverage count at policy issue City Cebu? [{'SUM(COVERAGE_COUNT)': 5076}]"))

