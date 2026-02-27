
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


llm = ChatGroq(
    #  model = 'llama-3.3-70b-versatile',
    model = 'llama-3.1-8b-instant',
    api_key=settings.GROQ_API_KEY,
    temperature=0
    )

# llm = ChatGoogleGenerativeAI(
#     model = "gemini-2.5-flash",
#     api_key=settings.GEMINI_API_KEY,
#     temperature=0
# )