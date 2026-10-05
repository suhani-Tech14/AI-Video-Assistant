from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question


load_dotenv()


def run_pipeline(source: str, language: str = "english") -> dict:
    print("Starting AI Video Assistant")

    chunks = process_input(source)

    transcript = transcribe_all(chunks, language)

    print(
        "Raw transcription, first 300 characters:\n"
        f"{transcript[:300]}"
    )

    title = generate_title(transcript)
    summary = summarize(transcript)
    action_items = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)

    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


def start_question_loop(rag_chain):
    chat_history = []

    print("\n" + "=" * 60)
    print("Chat with your video")
    print("Type 'exit', 'quit', or 'q' to stop.")
    print("=" * 60)

    while True:
        question = input("\nYou: ").strip()

        if question.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break

        if not question:
            print("Please enter a question.")
            continue

        try:
            answer = ask_question(
                rag_chain=rag_chain,
                question=question,
                chat_history=chat_history,
            )

            print(f"\nAssistant: {answer}\n")

            chat_history.append({
                "question": question,
                "answer": answer,
            })

        except Exception as error:
            print(f"\nCould not answer the question: {error}\n")


if __name__ == "__main__":
    source = input(
        "Enter YouTube URL or local file path: "
    ).strip()

    language = input(
        "Language (english/hinglish): "
    ).strip() or "english"

    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"Title:\n{result['title']}")

    print(f"\nSummary:\n{result['summary']}")

    print(f"\nAction Items:\n{result['action_items']}")

    print(f"\nKey Decisions:\n{result['key_decisions']}")

    print(f"\nOpen Questions:\n{result['open_questions']}")
    print("=" * 60)

    start_question_loop(result["rag_chain"])