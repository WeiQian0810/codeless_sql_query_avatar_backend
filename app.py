from collections.abc import Iterable
from flask import Flask, render_template, jsonify, request
# from flask_socketio import SocketIO
from flask_cors import CORS
import speech_recognition as sr
import text_to_speech
import threading
import openai
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS, Pinecone
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import pinecone
import os
from dotenv import load_dotenv
import snowflake.connector
import re
import say
from pydub import AudioSegment
import numpy as np
import requests
import testing
import os
from flask_socketio import SocketIO
from flask_cors import CORS
from py_mini_racer import py_mini_racer
os.environ["TOKENIZERS_PARALLELISM"] = "false"
load_dotenv()

connection_options = {
    'account': os.environ.get("sf_account"),
    'user': os.environ.get("sf_user"),
    'password': os.environ.get("sf_password"),
    'role': os.environ.get("sf_role"),
    'warehouse': os.environ.get("sf_warehouse"),
    'database': os.environ.get("sf_database"),
    'schema': os.environ.get("sf_schema"),
}


openai_key = os.environ.get("OPENAI_API_KEY")

FS_TEMPLATE = """ You are an expert SQL developer querying about insurance policy details. You have to write sql code in a Snowflake database based on a users question.
No matter what the user asks remember your job is to produce relevant SQL and only include the SQL, not the through process. So if a user asks to display something, you still should just produce SQL.
If you don't know the answer, provide what you think the sql should be but do not make up code if a column isn't available.


As an example, a user will ask "What is the ticket size for policy issued at Cebu?" The SQL to generate this would be:

select AFYP
from POLICY.dbo.policy
where LOWER(policy_issue_city) = LOWER('CEBU');


Questions about policy fields should query POLICY.dbo.policy
There are columns 
afyp = ticket size,
basic_plan_id = identifier or identification code associated with a basic insurance plan, 
coverage_count = count or number of coverages within an insurance policy, 
owner_client_id = client id, 
policy_cease_dt = date on which a policy terminates or ceases to be in effect, 
policy_issue_city = issued city of an insurance policy, 
policy_issue_date = issued date of an insurance policy, 
policy_status = current state of an insurance policy can be either inforced or lapsed, 
policy_type = type of insurance policy either traditional or vul, 
pol_app_recv_dt = policy application received date,
pol_id = policy number,
premium_mode = premium payment frequency,
premium_pay_type = premium payment type either single pay or double pay,
serving_agt_cd = serving agent code,
writing_agt_cd = writing agent code

The policy figure column names include underscores _, so if a user asks for policy issue city, make sure this is converted to POLICY_ISSUE_CITY. 
Some figures may have slightly different terminology, so find the best match to the question. For instance, if the user asks about policy number, look for something like POL_ID.
If user look for average ticket size, find total(AFYP)/count(AFYP)

Question: {question}
Context: {context}

SQL: ```sql ``` \n
 
"""
FS_PROMPT = PromptTemplate(input_variables=["question", "context"], template=FS_TEMPLATE, )


app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}, "supports_credentials": True, "allow_headers": ["Content-Type"]})
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "Content-Type"}})
socketio = SocketIO(app, cors_allowed_origins="*")
listening_flag = True
cors = CORS(app, resources={r"/socket.io/*": {"origins": "http://127.0.0.1:5000"}})


@socketio.on('connect')
def connect():
  print('connected')

def recognize_and_respond(recognizer, microphone):
    global listening_flag
    while listening_flag:
        with microphone as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)

        try:
            socketio.emit('response', {'text': 'process'})
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            socketio.emit('correct', {'question':text.replace('"','')})
            listening_flag = False

        except sr.UnknownValueError:
            socketio.emit('continueListen', 'error')
            print("Sorry, could not understand audio.")
            listening_flag = True
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            listening_flag = True

    return text  # Return None if the recognized text doesn't start with 'Hi'

@app.route('/start_listening', methods=['POST'])
def start_listening():
    print("Request received for start_listening")
    # global listening_flag
    # listening_flag = True 
    # recognizer = sr.Recognizer()
    # microphone = sr.Microphone()

    # Create a separate thread for speech recognition and text-to-speech
    # thread = threading.Thread(target=recognize_and_respond, args=(recognizer, microphone))
    # thread.start()

    # recognized_text = recognize_and_respond(recognizer, microphone)
    
    data = request.get_json()
    
    print(data)
    
    if 'question' not in data:
        return jsonify(error='Question is missing in the request payload'), 400

    recognized_text = data['question']
    
    if recognized_text and recognized_text.lower().startswith('hi'):
        print('Correcting...')
        print('Before: ', recognized_text[2:])
        corrected_question = testing.correct_sentence_with_gpt(recognized_text[2:])
        print('After: ', corrected_question)
        socketio.emit('correct', {'question':corrected_question.replace('"','')})
        print('Converting...')
        data = fs_chain1(corrected_question)
            
        # print('SQL Query: SUM(COVERAGE_COUNT)')
        # print('SUM(COVERAGE_COUNT): 5076')
        return jsonify({'message': 'Listening started successfully', 'recognized_text': corrected_question, 'tableData': data})
    else:
        return jsonify({'message': 'Listening started successfully', 'recognized_text': 'No valid greeting'})


llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.1,
    max_tokens=1000, 
    openai_api_key=openai_key
)

def sf_query(str_input):
    # Create a connection object
    connection = snowflake.connector.connect(**connection_options)
    """
    performs snowflake query with caching
    """
    try:
        # Create a cursor object
        cursor = connection.cursor()

        # Execute a query or other operations
        cursor.execute(str_input)
        
        column_headers = [desc[0] for desc in cursor.description]
        
        # print(column_headers)

        # Fetch and print results
        results = cursor.fetchall()
        
        result_dicts = [dict(zip(column_headers, row)) for row in results]

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()
    return result_dicts

def get_faiss():
    " get the loaded FAISS embeddings"
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    embeddings = HuggingFaceEmbeddings(model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs)

    # embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    return FAISS.load_local("faiss_index", embeddings)

def correct_sentence_with_gpt(sentence):
    prompt = f"Correct the following sentence: '{sentence}'"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use the chat-based model
        messages=[
            {"role": "system", 
             "content": """You are an expert to correct the inaccurate speech to text questions from user. Please help to correct the user questions into something related to the policy table.
                            The corrected question will then used to generate SQL query to get the data from the policy table.
                            Users are querying about insurance policy details. 
                            There are columns 
                            afyp = ticket size,
                            basic_plan_id = identifier or identification code associated with a basic insurance plan, 
                            coverage_count = count or number of coverages within an insurance policy, 
                            owner_client_id = client id, 
                            policy_cease_dt = date on which a policy terminates or ceases to be in effect, 
                            policy_issue_city = issued city of an insurance policy, 
                            policy_issue_date = issued date of an insurance policy, 
                            policy_status = current state of an insurance policy can be either inforced or lapsed, 
                            policy_type = type of insurance policy either traditional or vul, 
                            pol_app_recv_dt = policy application received date,
                            pol_id = policy number,
                            premium_mode = premium payment frequency,
                            premium_pay_type = premium payment type either single pay or double pay,
                            serving_agt_cd = serving agent code,
                            writing_agt_cd = writing agent code.
                            
                            As an example, a user question is "what is the total carriage car at policy issue City Cebu" with the similarity 
                            The sentence to be generated would be:
                            What is the total coverage count at policy issue City Cebu?
                        
                        """
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.7,
        n=1,
        stop=None
    )
    
    corrected_sentence = response['choices'][0]['message']['content'].strip()
    return corrected_sentence

@app.route('/query', methods=['POST'])
def fs_chain():
    """
    returns a question answer chain for faiss vectordb
    """
    data = request.get_json()
    
    if 'question' not in data:
        return jsonify(error='Question is missing in the request payload'), 400

    question = data['question']
    # print(f"You said2: {question}")
    docsearch = get_faiss()
    qa_chain = RetrievalQA.from_chain_type(llm, 
                                           retriever=docsearch.as_retriever(),
                                           chain_type_kwargs={"prompt": FS_PROMPT})
    result = qa_chain({"query": question})
    # data = sf_query(result['result'])
    data = [{'SUM(COVERAGE_COUNT)': 5076}]
    print(data)
    return data

def fs_chain1(question):
    """
    returns a question answer chain for faiss vectordb
    """
    docsearch = get_faiss()
    qa_chain = RetrievalQA.from_chain_type(llm, 
                                           retriever=docsearch.as_retriever(),
                                           chain_type_kwargs={"prompt": FS_PROMPT})
    result = qa_chain({"query": question})
    print('Question: ', question)
    print('Query: ', result['result'])
    data = sf_query(result['result'])
    for item in data:
        for key, value in item.items():
            item[key] = int(value)
    # data = [{'SUM(COVERAGE_COUNT)': 5076}]
    print(data)
    return data



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
