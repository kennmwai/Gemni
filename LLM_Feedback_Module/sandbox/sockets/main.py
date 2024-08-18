import asyncio
import logging
import os
import signal
import sys

from llm_fb import LLMFeedback
from database import Database, Assignment, AssessmentContent, Student, StudentWork
from socket_server import SocketServer


def signal_handler(sig, frame):
    """Handle keyboard interrupts"""
    logging.info("Received keyboard interrupt. Shutting down server...")
    sys.exit(0)


def process_new_student_work(
    db: Database, student_id: int, assignment_id: int, student_work: str
):
    # Create a new StudentWork entry
    new_work = StudentWork(
        student_id=student_id, assignment_id=assignment_id, content=student_work
    )
    work_id = db.add_student_work(new_work)

    # if work_id is None:
    #     return {"error": "Failed to create new StudentWork entry"}

    # Fetch additional information needed for AssessmentContent
    assignment = db.get_assignment_by_id(assignment_id)
    assessment_type = db.get_assessment_type_by_id(assignment.assessment_type_id)
    correct_answer = db.get_correct_answer(assignment_id)
    peer_works = db.get_peer_works(assignment_id, work_id)
    topic = db.get_topic_by_assignment(assignment_id)

    # Create AssessmentContent
    content = AssessmentContent(
        work_id=work_id,
        student_work=student_work,
        assessment_type=assessment_type,
        correct_answer=correct_answer,
        peer_works=", ".join(peer_works),
        topic=topic,
    )

    return content


async def main():
    logger = logging.getLogger(__file__)
    log_format = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_format)

    signal.signal(signal.SIGINT, signal_handler)

    api_key = os.getenv("AIML_API_KEY", "54a34a43333f47119e47424176f69cf8")
    base_url = "https://api.aimlapi.com"
    model = "mistralai/Mistral-7B-Instruct-v0.2"
    system_prompt = "You are an AI assistant who knows everything about education and can provide feedback on student work."
    db_path = "data/education_feedback.db"

    # Initialize the Database
    db = Database(db_path)

    # Initialize LLMFeedback with the database
    llm_feedback = LLMFeedback(api_key, base_url, model, system_prompt, db)

    # Add a student
    student = Student(name="John Doe")
    student_id = db.add_student(student)

    # Add an assignment
    assessment_type_id = db.get_assessment_type_id("Essay")
    if assessment_type_id:
        assignment = Assignment(
            title="Reflection on Suffering",
            description="Write an essay reflecting on the role of suffering in personal growth.",
            assessment_type_id=assessment_type_id,
        )
        assignment_id = db.add_assignment(assignment)
    else:
        print("No assessment type found.")

    # Add student work
    work = StudentWork(
        student_id=student_id,
        assignment_id=assignment_id,
        content="Out of suffering have emerged the strongest souls...",
    )
    work_id = db.add_student_work(work)

    # Get assessment content
    assessment_content = db.get_assessment_content(work_id)

    if assessment_content:
        # Get feedback using LLMFeedback
        response = llm_feedback.get_feedback(assessment_content)
        print(response)
    else:
        print("No assessment content found.")


    # Initialize SocketServer
    server = SocketServer()

    # Register handlers
    server.register_handler("get_feedback", llm_feedback.get_feedback)
    server.register_handler("validate_answer", llm_feedback.validate_answer)
    server.register_handler(
        "suggest_enhancements", llm_feedback.generate_suggested_enhancements
    )
    server.register_handler("peer_comparison", llm_feedback.provide_peer_comparison)
    server.register_handler("resource_links", llm_feedback.generate_resource_links)
    server.register_handler("evaluate_effort", llm_feedback.evaluate_effort)
    server.register_handler("student_opinion", llm_feedback.get_student_opinion)

    try:
        # Start the server
        server.start()
    except KeyboardInterrupt:
        logging.error("Exiting...")
        exit(0)
    except Exception as e:
        logging.error(f"Error starting server: {e}")


if __name__ == "__main__":
    asyncio.run(main())
