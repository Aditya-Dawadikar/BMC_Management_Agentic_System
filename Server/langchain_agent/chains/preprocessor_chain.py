import os
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

def load_preprocessor_chain():
    with open("langchain_agent/prompts/preprocessor_prompt.txt", "r") as f:
        decision_prompt = f.read()

    prompt = PromptTemplate(
        input_variables=["text", "todays_date"],
        template=decision_prompt
    )

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key = GEMINI_API_KEY,
        temperature=0.3
    )

    return LLMChain(llm=llm, prompt=prompt)
