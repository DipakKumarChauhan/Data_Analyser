# from groq import Groq
from langchain_groq import ChatGroq
from app.config import settings

# client = Groq(api_key=settings.GROQ_API_KEY)
llm = ChatGroq(
     model = 'llama-3.3-70b-versatile',
    api_key=settings.GROQ_API_KEY,
     temperature=0
    )

# def call_llm(prompt:str)-> str:

#     response = client.chat.completions.create(
#         model= 'llama-3.3-70b-versatile',
#         messages = [
#             {"role": "system", "content": "You are a data analysis intent parser."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0,
#     )
#     # print(response.choices[0].message.content)
#     return response.choices[0].message.content

