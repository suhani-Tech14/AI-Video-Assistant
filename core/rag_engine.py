import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from operator import itemgetter

from core.vector_store import (
    build_vector_store,
    load_vector_store,
    get_retriever,
)


def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "Groq API key not found. Add GROQ_API_KEY to your .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=api_key,
        temperature=0.3,
        max_retries=2,
    )

def format_docs(docs):
    return "\n\n".join(
        document.page_content
        for document in docs
    )


def format_chat_history(chat_history):
    if not chat_history:
        return "No previous conversation."

    return "\n\n".join(
        f"User: {message['question']}\n"
        f"Assistant: {message['answer']}"
        for message in chat_history
    )


def create_rag_chain(retriever):
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an expert video assistant.

Answer the user's question using only the transcript context below.

Use the conversation history to understand follow-up questions such as:
- "Explain that again."
- "What did he mean by this?"
- "Tell me more about the previous point."

If the answer is not present in the transcript context, say exactly:
"I could not find this information in the video transcript."

Do not invent facts.
Be concise and precise.

Conversation history:
{chat_history}

Transcript context:
{context}
""",
        ),
        ("human", "{question}"),
    ])

    return (
       
    {
        "context": itemgetter("question")
        | retriever
        | RunnableLambda(format_docs),

        "question": itemgetter("question"),

        "chat_history": RunnableLambda(
            lambda data: format_chat_history(
                data.get("chat_history", [])
            )
        ),
    }
    | prompt
    | llm
    | StrOutputParser()

    )


def build_rag_chain(transcript: str):
    vector_store = build_vector_store(transcript)
    retriever = get_retriever(vector_store, k=4)

    return create_rag_chain(retriever)


def load_rag_chain():
    vector_store = load_vector_store()
    retriever = get_retriever(vector_store, k=4)

    return create_rag_chain(retriever)


def ask_question(
    rag_chain,
    question: str,
    chat_history=None,
) -> str:
    if chat_history is None:
        chat_history = []

    print(f"Question: {question}")

    answer = rag_chain.invoke({
        "question": question,
        "chat_history": chat_history,
    })

    print(f"Answer: {answer}")

    return answer