from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
    )


def build_qa_chain():
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an AI video assistant.

Answer the user's question using only the video transcript provided below.
If the answer is not available in the transcript, clearly say:
"I could not find that information in the video transcript."

The conversation history may contain previous questions and answers.
If the user asks a follow-up question such as " explain that more",
first understand what "that" refers to from the conversation history.

Give a clear and helpful answer.
Do not repeat the user's question unnecessarily.

Video transcript:
{transcript}

Conversation history:
{history}
"""
        ),
        ("human", "{question}"),
    ])

    return prompt | get_llm() | StrOutputParser()


def answer_question(
    transcript: str,
    question: str,
    chat_history: list[dict]
) -> str:
    history_text = ""

    for message in chat_history:
        history_text += (
            f"User: {message['question']}\n"
            f"Assistant: {message['answer']}\n\n"
        )

    chain = build_qa_chain()

    return chain.invoke({
        "transcript": transcript,
        "history": history_text,
        "question": question,
    })