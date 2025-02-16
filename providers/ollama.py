from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains.combine_documents import create_stuff_documents_chain
from models.index import ChatMessage

CHROMA_PATH = "./db_metadata_v5"

model = OllamaLLM(model="llama3.2:latest", temperature=0.1)
embedding_function = OllamaEmbeddings(model="mxbai-embed-large")
db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
chat_history = {}

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                [INST]Ты - консультант для абитуриентов Алтайского Государственного Университета.
                Предоставляй точные, дружелюбные и полезные ответы на русском языке, опираясь только на предоставленный контекст.
                Если информации в контексте нет, ответь: "Хм, я не уверен."
                Будь вежлив.
                Не шути и не отклоняйся от темы.
                Если вопрос неясен, задай уточняющий вопрос.
                Ответ оформляй в формате Markdown (MD).
                Завершай ответ позитивно.
                [/INST]
                [INST]Контекст: {context}[/INST]
            """
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ]
)

document_chain = create_stuff_documents_chain(llm=model, prompt=prompt_template)


