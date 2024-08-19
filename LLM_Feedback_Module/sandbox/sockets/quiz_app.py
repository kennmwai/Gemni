import random
import logging
from typing import List, Optional, Tuple
from quiz_db import QuizDB, Quiz, Question, Answer

logging.basicConfig(level=logging.INFO)


class QuizApp:
    def __init__(self, db: QuizDB = QuizDB()):
        self.db = db
        self.current_question_index = 0
        self.questions: List[Question] = []
        self.answers: List[Answer] = []
        self.current_quiz: Optional[Quiz] = None

    def load_questions(self, quiz_id: int) -> None:
        """Load questions for a specific quiz from the database."""
        self.questions = self.db.get_questions_by_quiz_id(quiz_id)

    def start_quiz(self, quiz_id: int) -> None:
        """Start the quiz."""
        logging.info("Starting the quiz...")
        self.current_quiz = self.db.get_quiz_by_id(quiz_id)
        if not self.current_quiz:
            logging.error(f"No quiz found with ID {quiz_id}")
            return
        self.load_questions(quiz_id)
        random.shuffle(self.questions)
        self.current_question_index = 0
        self.answers.clear()

    def get_next_question(self) -> Optional[Question]:
        """Get the next question."""
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            self.current_question_index += 1
            return question
        return None

    def submit_answer(self, question_id: int, selected_choice: str) -> None:
        """Submit an answer for a question."""
        question = self.db.get_question_by_id(question_id)
        if question:
            is_correct = selected_choice == question.correct_answer
            answer = Answer(
                question_id=question_id,
                selected_choice=selected_choice,
                is_correct=is_correct,
            )
            self.answers.append(answer)
            logging.info(f"Submitted answer: {answer}")
        else:
            logging.error(f"No question found with ID {question_id}")

    def calculate_score(self) -> Tuple[int, int]:
        """Calculate the final score."""
        correct_answers = sum(1 for answer in self.answers if answer.is_correct)
        total_questions = len(self.questions)
        return correct_answers, total_questions

    def save_quiz_results(self) -> None:
        """Save the quiz results to the database."""
        for answer in self.answers:
            self.db.record_answer(answer)

    def display_score(self) -> None:
        """Display the final score."""
        correct, total = self.calculate_score()
        logging.info(f"Your score: {correct}/{total}")

    def get_all_quizzes(self) -> List[Quiz]:
        if self.current_quiz is None:
            return self.db.get_all_quizzes()
        return []

    def get_quiz_statistics(self) -> Optional[Tuple[int, int, float]]:
        """Get statistics for the current quiz."""
        if self.current_quiz:
            return self.db.get_quiz_statistics(self.current_quiz.quiz_id)
        return None

    def update_current_quiz(self, title: str, description: str) -> bool:
        """Update the current quiz information."""
        if self.current_quiz:
            updated_quiz = Quiz(
                quiz_id=self.current_quiz.quiz_id, title=title, description=description
            )
            return self.db.update_quiz(updated_quiz)
        return False

    def delete_current_quiz(self) -> bool:
        """Delete the current quiz and all related questions and answers."""
        if self.current_quiz:
            result = self.db.delete_quiz(self.current_quiz.quiz_id)
            if result:
                self.current_quiz = None
                self.questions.clear()
                self.answers.clear()
            return result
        return False
