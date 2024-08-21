import asyncio
import logging
import os
import signal
import sys

from llm_feedback import LLMFeedback
from database import Database
from socket_server import SocketServer


def signal_handler(sig, frame):
    """Handle keyboard interrupts"""
    logging.info("Received keyboard interrupt. Shutting down server...")
    sys.exit(0)


async def main():
    # Setup logging
    logging.getLogger(__file__)
    log_format = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_format)

    # Handle keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    # Load environment variables
    api_key = os.getenv("AIML_API_KEY", "54a34a43333f47119e47424176f69cf8")
    base_url = "https://api.aimlapi.com"
    model = "mistralai/Mistral-7B-Instruct-v0.2"
    system_prompt = "You are an AI assistant who knows everything about education and can provide feedback on student work."
    db_path = "data/education_feedback.db"

    # Initialize the Database
    db = Database(db_path)

    # Initialize LLMFeedback with the database
    llm_feedback = LLMFeedback(api_key, base_url, model, system_prompt, db)

    # Initialize SocketServer and register handlers
    server = SocketServer()
    server.register_handler("get_feedback", llm_feedback.get_feedback)
    server.register_handler("validate_answer", llm_feedback.validate_answer)
    server.register_handler("suggest_enhancements", llm_feedback.generate_suggested_enhancements)
    server.register_handler("peer_comparison", llm_feedback.provide_peer_comparison)
    server.register_handler("resource_links", llm_feedback.generate_resource_links)
    server.register_handler("evaluate_effort", llm_feedback.evaluate_effort)
    # server.register_handler("student_opinion", llm_feedback.get_student_opinion)

    try:
        # Start the server
        server.start()
    except KeyboardInterrupt:
        logging.error("Exiting...")
        server.stop()
        # db.close()  # Close the database connection
        exit(0)
    except Exception as e:
        logging.error(f"Error starting server: {e}")
        server.stop()
        # db.close()


if __name__ == "__main__":
    asyncio.run(main())
