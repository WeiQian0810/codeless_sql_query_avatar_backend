import openai
import os
from dotenv import load_dotenv
load_dotenv()
# Set your OpenAI GPT API key
openai.api_key = os.environ.get("OPENAI_API_KEY")


# Function to correct a given sentence using ChatGPT
def correct_sentence_with_gpt(sentence):
    prompt = f"Correct the following sentence: '{sentence}'"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",  # Use the chat-based model
        messages=[
            {"role": "system", 
             "content": """You are an expert to correct the inaccurate speech to text questions from user. 
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

# Example usage:
# user_question = "what is the total carriage car at policy issue City Cebu"
# corrected_question = correct_sentence_with_gpt(user_question)

# print("Original Question:", user_question)
# print("Corrected Question:", corrected_question)