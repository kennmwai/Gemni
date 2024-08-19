import logging
import sqlite3
import json
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional, Tuple

DB_FILE = "quiz.db"

# Updated table creation SQL
QUIZZES_TABLE = """
CREATE TABLE IF NOT EXISTS Quizzes (
    quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT
);
"""

QUESTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS Questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    question_text TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    choices TEXT NOT NULL,
    is_open_ended BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (quiz_id) REFERENCES Quizzes(quiz_id)
);
"""

ANSWERS_TABLE = """
CREATE TABLE IF NOT EXISTS Answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    selected_choice TEXT,
    is_correct BOOLEAN,
    open_ended_response TEXT,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id)
);
"""


@dataclass
class Quiz:
    title: str
    description: Optional[str] = None
    quiz_id: Optional[int] = None


@dataclass
class Question:
    quiz_id: int
    question_text: str
    correct_answer: str
    choices: List[str]
    is_open_ended: bool = False
    question_id: Optional[int] = None


@dataclass
class Answer:
    question_id: int
    selected_choice: Optional[str] = None
    is_correct: Optional[bool] = None
    open_ended_response: Optional[str] = None
    answer_id: Optional[int] = None


class QuizDB:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()
        logging.basicConfig(level=logging.INFO)

    @contextmanager
    def _db_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _create_table(self, conn, table_sql):
        """Create a table from the create_table_sql statement."""
        try:
            c = conn.cursor()
            c.execute(table_sql)
        except sqlite3.Error as e:
            logging.error(f"Error creating table: {e}")

    def _init_db(self):
        """Initialize the database with all necessary tables."""
        with self._db_connection() as conn:
            self._create_table(conn, QUIZZES_TABLE)
            self._create_table(conn, QUESTIONS_TABLE)
            self._create_table(conn, ANSWERS_TABLE)

    def add_quiz(self, quiz: Quiz) -> Optional[int]:
        """Add a new quiz."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO Quizzes (title, description) VALUES (?, ?)"
            cursor.execute(sql, (quiz.title, quiz.description))
            conn.commit()
            return cursor.lastrowid

    def add_question(self, question: Question) -> Optional[int]:
        """Add a new question to a quiz."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = """INSERT INTO Questions
                     (quiz_id, question_text, correct_answer, choices, is_open_ended)
                     VALUES (?, ?, ?, ?, ?)"""
            choices_json = json.dumps(question.choices)
            cursor.execute(
                sql,
                (
                    question.quiz_id,
                    question.question_text,
                    question.correct_answer,
                    choices_json,
                    question.is_open_ended,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def add_answer(self, answer: Answer) -> Optional[int]:
        """Add a new answer for a question."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = """INSERT INTO Answers (question_id, selected_choice, is_correct, open_ended_response)
                     VALUES (?, ?, ?, ?)"""
            cursor.execute(
                sql, (answer.question_id, answer.selected_choice, answer.is_correct, answer.open_ended_response)
            )
            conn.commit()
            return cursor.lastrowid

    def get_quiz_by_id(self, quiz_id: int) -> Optional[Quiz]:
        """Retrieve a quiz by its ID."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = """SELECT title, description, quiz_id FROM Quizzes WHERE quiz_id = ?"""
            cursor.execute(sql, (quiz_id,))
            result = cursor.fetchone()
            return Quiz(*result) if result else None

    def get_all_quizzes(self) -> List[Quiz]:
        """Retrieve all quizzes."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = """SELECT title, description, quiz_id FROM Quizzes"""
            cursor.execute(sql,)
            return [Quiz(*row) for row in cursor.fetchall()]

    def get_all_questions(self) -> List[Question]:
        """Retrieve all questions."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM Questions"
            cursor.execute(sql)
            questions = []
            for row in cursor.fetchall():
                question_id, quiz_id, question_text, correct_answer, choices_json, is_open_ended = row
                choices = json.loads(choices_json)
                questions.append(
                    Question(
                        quiz_id, question_text, correct_answer, choices, is_open_ended, question_id
                    )
                )
            return questions

    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """Retrieve a question by its ID."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM Questions WHERE question_id = ?"
            cursor.execute(sql, (question_id,))
            result = cursor.fetchone()
            if result:
                question_id, quiz_id, question_text, correct_answer, choices_json, is_open_ended = result
                choices = json.loads(choices_json)
                return Question(
                    quiz_id, question_text, correct_answer, choices, is_open_ended, question_id
                )
            return None

    def get_questions_by_quiz_id(self, quiz_id: int) -> List[Question]:
        """Retrieve all questions for a given quiz."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM Questions WHERE quiz_id = ?"
            cursor.execute(sql, (quiz_id,))
            questions = []
            for row in cursor.fetchall():
                question_id, quiz_id, question_text, correct_answer, choices_json, is_open_ended = row
                choices = json.loads(choices_json)
                questions.append(
                    Question(
                        quiz_id, question_text, correct_answer, choices, is_open_ended, question_id
                    )
                )
            return questions

    def get_answers_by_question_id(self, question_id: int) -> List[Answer]:
        """Retrieve all answers for a given question."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            # Select columns in the order expected by the Answer class
            sql = """
            SELECT question_id, selected_choice, is_correct, open_ended_response, answer_id
            FROM Answers WHERE question_id = ?
            """
            cursor.execute(sql, (question_id,))
            return [Answer(*row) for row in cursor.fetchall()]

    def get_quiz_statistics(self, quiz_id: int) -> Tuple[int, int, float]:
        """
        Get statistics for a quiz.
        Returns: (total_questions, total_answers, correct_percentage)
        """
        total_questions = self.get_total_questions(quiz_id)
        total_answers, correct_answers = self.get_total_answers_and_correct_answers(quiz_id)

        correct_percentage = (
            (correct_answers / total_answers * 100) if total_answers > 0 else 0
        )

        return total_questions, total_answers, correct_percentage


    def get_total_questions(self, quiz_id: int) -> int:
        """Get the total number of questions for a given quiz."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Questions WHERE quiz_id = ?", (quiz_id,))
            return cursor.fetchone()[0]

    def get_total_answers_and_correct_answers(self, quiz_id: int) -> Tuple[int, int]:
        """Get the total number of answers and correct answers for a given quiz."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN is_correct THEN 1 ELSE 0 END)
                FROM Answers
                JOIN Questions ON Answers.question_id = Questions.question_id
                WHERE Questions.quiz_id = ?
            """,
                (quiz_id,),
            )
            total_answers, correct_answers = cursor.fetchone()
            return total_answers, correct_answers

    def record_answer(self, answer: Answer) -> Optional[int]:
        """Save the quiz results to the database."""
        return self.add_answer(answer)

    def update_quiz(self, quiz: Quiz) -> bool:
        """Update an existing quiz."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            sql = "UPDATE Quizzes SET title = ?, description = ? WHERE quiz_id = ?"
            cursor.execute(sql, (quiz.title, quiz.description, quiz.quiz_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_quiz(self, quiz_id: int) -> bool:
        """Delete a quiz and its related questions and answers."""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            try:
                # Delete related answers
                cursor.execute(
                    """
                    DELETE FROM Answers
                    WHERE question_id IN (SELECT question_id FROM Questions WHERE quiz_id = ?)
                """,
                    (quiz_id,),
                )

                # Delete related questions
                cursor.execute("DELETE FROM Questions WHERE quiz_id = ?", (quiz_id,))

                # Delete the quiz
                cursor.execute("DELETE FROM Quizzes WHERE quiz_id = ?", (quiz_id,))

                conn.commit()
                return True
            except sqlite3.Error as e:
                logging.error(f"Error deleting quiz: {e}")
                conn.rollback()
                return False


if __name__ == "__main__":
    # Example usage
    db = QuizDB(DB_FILE)

    # Add a quiz
    quiz = Quiz(title="General Knowledge Quiz", description="A simple GK quiz")
    quiz_id = db.add_quiz(quiz)
    print(f"Quiz ID: {quiz_id}")
    print("")

    # Fetch and print all quizzes
    qz = db.get_quiz_by_id(quiz_id)
    print("Fetched Quiz:\n", qz)
    quizzes = db.get_all_quizzes()
    print("All Quizzes:\n", quizzes)
    print("")

    # Add questions
    question_1 = Question(
        quiz_id=quiz_id,
        question_text="What is the capital of France?",
        correct_answer="Paris",
        choices=["Paris", "London", "Rome", "Nairobi"],
    )
    question_id_1 = db.add_question(question_1)
    print(f"Question ID 1: {question_id_1}")

    question_2 = Question(
        quiz_id=quiz_id,
        question_text="What is 2 + 2?",
        correct_answer="4",
        choices=["3", "4", "5", "8"],
    )
    question_id_2 = db.add_question(question_2)
    print(f"Question ID 2: {question_id_2}")

    question_3 = Question(
        quiz_id=quiz_id,
        question_text="What is the name of the process that sends one qubit of information using two bits of classical information?",
        correct_answer="Quantum Teleportation",
        choices=[
            "Super Dense Coding",
            "Quantum Programming",
            "Quantum Teleportation",
            "Quantum Entanglement",
        ],
    )
    question_id_3 = db.add_question(question_3)
    print(f"Question ID 3: {question_id_3}")

    question_4 = Question(
        quiz_id=quiz_id,
        question_text="Which quantum phenomenon is used to link two particles instantaneously?",
        correct_answer="Quantum Entanglement",
        choices=[
            "Quantum Superposition",
            "Quantum Entanglement",
            "Quantum Tunneling",
            "Quantum Decoherence",
        ],
    )
    question_id_4 = db.add_question(question_4)
    print(f"Question ID 4: {question_id_4}")

    # Add open-ended question
    question_5 = Question(
        quiz_id=quiz_id,
        question_text="Describe the process of quantum teleportation.",
        correct_answer="Quantum Teleportation .... ",
        choices=[],  # No choices for open-ended questions
        is_open_ended=True
    )
    question_id_5 = db.add_question(question_5)
    print(f"Question ID 5: {question_id_5}")
    print("")

    # Record a multiple-choice answer
    answer_1 = Answer(
        question_id=question_id_1, selected_choice="Paris", is_correct=True
    )
    answer_2 = Answer(question_id=question_id_2, selected_choice="4", is_correct=True)
    answer_id_1 = db.add_answer(answer_1)
    answer_id_2 = db.record_answer(answer_2)

    print(f"Answer ID 1: {answer_id_1}")
    print(f"Answer ID 2: {answer_id_2}")

    # Record an open-ended answer
    answer_5 = Answer(
        question_id=question_id_5,
        open_ended_response="Quantum teleportation involves transferring the state of a qubit using classical bits.",
        is_correct=None  # None Or set to True/False if manually graded
    )

    answer_id_5 = db.add_answer(answer_5)
    print(f"Answer ID 5: {answer_id_5}")
    print("Answer 5", answer_5)
    print("")

    # Fetch and print questions and options for a quiz
    questions = db.get_questions_by_quiz_id(quiz_id)
    for question in questions:
        print(f"Question: {question.question_text}")
        print(f"Choices: {', '.join(question.choices)}")
        print(f"Correct Answer: {question.correct_answer}\n")
    print("")

    # Get a question by ID
    question = db.get_question_by_id(question_id_1)
    print(f"Retrieved question: {question}")
    print("")

    # Fetch and print answers for the second question
    anss_2 = db.get_answers_by_question_id(question_id_2)
    print("ANS 2: ", anss_2)
    for ans in anss_2:
        print(f"Selected Choice: {ans.selected_choice}, Correct: {ans.is_correct}")

    ans_5 = db.get_answers_by_question_id(question_id_5)
    print("ANS 5: ", ans_5)
    for ans in ans_5:
        print(f"Open-Ended Response: {ans.open_ended_response}")
    print("")

    # Get quiz statistics
    stats = db.get_quiz_statistics(quiz_id)
    print(
        f"Quiz statistics: Total questions: {stats[0]}, Total answers: {stats[1]}, Correct percentage: {stats[2]:.2f}%"
    )
    print("")

    # Update a quiz
    updated_quiz = Quiz(
        quiz_id=quiz_id,
        title="Updated General Knowledge Quiz",
        description="An updated GK quiz",
    )
    if db.update_quiz(updated_quiz):
        print("Quiz updated successfully\n")

    # Delete a quiz
    # if db.delete_quiz(quiz_id):
    #     print("Quiz deleted successfully\n")
