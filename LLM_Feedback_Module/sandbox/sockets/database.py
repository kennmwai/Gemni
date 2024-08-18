import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional, Tuple

DB_FILE = "data/llm_fb.db"

STUDENTS_TABLE = """
CREATE TABLE IF NOT EXISTS Students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
"""

ASSESSMENT_TYPES_TABLE = """
CREATE TABLE IF NOT EXISTS AssessmentTypes (
    assessment_type_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
"""

ASSIGNMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS Assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    assessment_type_id INTEGER,
    correct_answer TEXT,
    FOREIGN KEY (assessment_type_id) REFERENCES AssessmentTypes(assessment_type_id)
);
"""

STUDENT_WORK_TABLE = """
CREATE TABLE IF NOT EXISTS StudentWork (
    work_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    assignment_id INTEGER,
    content TEXT NOT NULL,
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    FOREIGN KEY (assignment_id) REFERENCES Assignments(assignment_id)
);
"""

FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS Feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER,
    feedback_type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES StudentWork(work_id)
);
"""

RESOURCE_LINKS_TABLE = """
CREATE TABLE IF NOT EXISTS ResourceLinks (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT
);
"""
LLM_REQUESTS_TABLE = """
    CREATE TABLE IF NOT EXISTS LLMRequests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT NOT NULL,
        response TEXT,
        model TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""


@dataclass
class Student:
    name: str
    student_id: Optional[int] = None


@dataclass
class AssessmentType:
    name: str
    assessment_type_id: int


@dataclass
class Assignment:
    title: str
    description: str
    assessment_type_id: int
    correct_answer: Optional[str] = None
    assignment_id: Optional[int] = None


@dataclass
class StudentWork:
    student_id: int
    assignment_id: int
    content: str
    work_id: Optional[int] = None
    submission_date: Optional[str] = None


@dataclass
class Feedback:
    work_id: int
    feedback_type: str
    content: str
    feedback_id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class ResourceLink:
    topic: str
    url: str
    description: str
    link_id: Optional[int] = None


@dataclass
class LLMRequest:
    prompt: str
    response: str
    model: str
    request_id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class AssessmentContent:
    student_work: str
    assessment_type: str
    correct_answer: Optional[str] = None
    peer_works: Optional[str] = None
    topic: Optional[str] = None
    work_id: Optional[int] = None


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        self._init_assessment_types()
        logging.basicConfig(level=logging.INFO)

    @contextmanager
    def _db_connection(self, db_file):
        """Context manager for database connections."""
        conn = sqlite3.connect(db_file)
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
        with self._db_connection(self.db_path) as conn:
            self._create_table(conn, STUDENTS_TABLE)
            self._create_table(conn, ASSESSMENT_TYPES_TABLE)
            self._create_table(conn, ASSIGNMENTS_TABLE)
            self._create_table(conn, STUDENT_WORK_TABLE)
            self._create_table(conn, FEEDBACK_TABLE)
            self._create_table(conn, RESOURCE_LINKS_TABLE)
            self._create_table(conn, LLM_REQUESTS_TABLE)

    def _init_assessment_types(self):
        """Initialize assessment types if they don't exist."""
        assessment_types = [
            (1, "Essay"),
            (2, "Short Answer"),
            (3, "Multiple Choice"),
            (4, "True/False"),
        ]
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
                INSERT OR IGNORE INTO AssessmentTypes (assessment_type_id, name)
                VALUES (?, ?)
            """
            cursor.executemany(sql, assessment_types)
            conn.commit()

    def add_student(self, student: Student) -> Optional[int]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO Students (name) VALUES (?)"
            cursor.execute(sql, (student.name,))
            conn.commit()
            return cursor.lastrowid

    def get_student(self, student_id: int) -> Optional[Student]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM Students WHERE student_id = ?"
            cursor.execute(sql, (student_id,))
            result = cursor.fetchone()
            return Student(*result) if result else None

    def add_assignment(self, assignment: Assignment) -> Optional[int]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO Assignments (title, description, assessment_type_id, correct_answer) VALUES (?, ?, ?, ?)"
            cursor.execute(
                sql,
                (
                    assignment.title,
                    assignment.description,
                    assignment.assessment_type_id,
                    assignment.correct_answer,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def add_multiple_assignments(
        self, assignments_data: List[Tuple[str, str, str]]
    ) -> List[int]:
        inserted_ids = []
        for title, description, assessment_type in assignments_data:
            assessment_type_id = self.get_assessment_type_id(assessment_type)
            if assessment_type_id is None:
                logging.warning(
                    f"Assessment type '{assessment_type}' not found. Skipping this assignment."
                )
                continue

            assignment = Assignment(
                title=title,
                description=description,
                assessment_type_id=assessment_type_id,
            )
            assignment_id = self.add_assignment(assignment)
            inserted_ids.append(assignment_id)

        return inserted_ids

    def get_assessment_type_id(self, assessment_type_name: str) -> Optional[int]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT assessment_type_id FROM AssessmentTypes WHERE name = ?",
                (assessment_type_name,),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_assessment_type_by_id(self, assessment_type_id: int) -> Optional[str]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM AssessmentTypes WHERE assessment_type_id = ?",
                (assessment_type_id,),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_assignment_by_id(self, assignment_id: int) -> Optional[Assignment]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
                SELECT a.assignment_id, a.title, a.description, a.assessment_type_id, a.correct_answer, at.name
                FROM Assignments a
                JOIN AssessmentTypes at ON a.assessment_type_id = at.assessment_type_id
                WHERE a.assignment_id = ?
            """
            cursor.execute(sql, (assignment_id,))
            row = cursor.fetchone()
            if row:
                return Assignment(
                    assignment_id=row[0],
                    title=row[1],
                    description=row[2],
                    assessment_type_id=row[3],
                    correct_answer=row[4],
                )
            return None

    def get_all_assignments(self) -> List[Assignment]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Assignments")
            return [Assignment(*row) for row in cursor.fetchall()]

    def add_student_work(self, work: StudentWork) -> Optional[int]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO StudentWork (student_id, assignment_id, content) VALUES (?, ?, ?)"
            cursor.execute(sql, (work.student_id, work.assignment_id, work.content))
            conn.commit()
            return cursor.lastrowid

    def get_student_work_by_id(self, work_id: int) -> Optional[StudentWork]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
                SELECT student_id, assignment_id, content, work_id, submission_date
                FROM StudentWork
                WHERE work_id = ?
            """
            cursor.execute(sql, (work_id,))
            row = cursor.fetchone()
            return StudentWork(*row) if row else None

    def get_all_student_work(self) -> List[StudentWork]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM StudentWork")
            return [StudentWork(*row) for row in cursor.fetchall()]

    def add_feedback(self, feedback: Feedback) -> Optional[int]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO Feedback (work_id, feedback_type, content) VALUES (?, ?, ?)"
            cursor.execute(
                sql, (feedback.work_id, feedback.feedback_type, feedback.content)
            )
            conn.commit()
            return cursor.lastrowid

    def get_feedback(
        self, work_id: int, feedback_type: Optional[str] = None
    ) -> List[Feedback]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if feedback_type:
                sql = "SELECT * FROM Feedback WHERE work_id = ? AND feedback_type = ?"
                cursor.execute(sql, (work_id, feedback_type))
            else:
                sql = "SELECT * FROM Feedback WHERE work_id = ?"
                cursor.execute(sql, (work_id,))
            return [Feedback(*row) for row in cursor.fetchall()]

    def get_all_feedback_paginated(
        self, work_id: int, page: int = 1, page_size: int = 10
    ) -> List[Feedback]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM Feedback WHERE work_id = ? LIMIT ? OFFSET ?"
            cursor.execute(sql, (work_id, page_size, (page - 1) * page_size))
            return [Feedback(*row) for row in cursor.fetchall()]

    def add_resource_link(self, resource: ResourceLink) -> Optional[int]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO ResourceLinks (topic, url, description) VALUES (?, ?, ?)"
            cursor.execute(sql, (resource.topic, resource.url, resource.description))
            conn.commit()
            return cursor.lastrowid

    def get_resource_links_by_topic(self, topic: str) -> List[ResourceLink]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ResourceLinks WHERE topic = ?", (topic,))
            return [ResourceLink(*row) for row in cursor.fetchall()]

    def log_llm_request(self, request: LLMRequest) -> Optional[int]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO LLMRequests (prompt, response, model) VALUES (?, ?, ?)"
            cursor.execute(sql, (request.prompt, request.response, request.model))
            conn.commit()
            return cursor.lastrowid

    def get_llm_request_by_id(self, request_id: int) -> Optional[LLMRequest]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM LLMRequests WHERE request_id = ?"
            cursor.execute(sql, (request_id,))
            result = cursor.fetchone()
            return LLMRequest(*result) if result else None

    def get_all_llm_requests(self) -> List[LLMRequest]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM LLMRequests")
            return [LLMRequest(*row) for row in cursor.fetchall()]

    def get_correct_answer(self, assignment_id: int) -> Optional[str]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
                SELECT correct_answer FROM Assignments WHERE assignment_id = ?
            """
            cursor.execute(sql, (assignment_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_peer_works(self, assignment_id: int, exclude_work_id: int) -> List[str]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
                SELECT content FROM StudentWork
                WHERE assignment_id = ? AND work_id != ?
            """
            cursor.execute(sql, (assignment_id, exclude_work_id))
            return [row[0] for row in cursor.fetchall()]

    def get_topic_by_assignment(self, assignment_id: int) -> Optional[str]:
        with self._db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
                SELECT topic FROM ResourceLinks
                JOIN Assignments ON Assignments.title = ResourceLinks.topic
                WHERE assignment_id = ?
            """
            cursor.execute(sql, (assignment_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_assessment_content(self, work_id: int) -> Optional[AssessmentContent]:
        student_work = self.get_student_work_by_id(work_id)
        if not student_work:
            return None

        assignment = self.get_assignment_by_id(student_work.assignment_id)
        if not assignment:
            return None

        assessment_type = self.get_assessment_type_by_id(assignment.assessment_type_id)
        peer_works = self.get_peer_works(assignment.assignment_id, work_id)

        # Prepare assessment content
        assessment_content = AssessmentContent(
            student_work=student_work.content,
            assessment_type=assessment_type,
            correct_answer=self.get_correct_answer(assignment.assignment_id),
            peer_works=", ".join(peer_works),
            topic=self.get_topic_by_assignment(assignment.assignment_id),
            work_id=student_work.work_id,
        )

        return assessment_content


if __name__ == "__main__":
    db = Database("data/temp.db")

    # Add a student
    student = Student(name="John Doe")
    student_id = db.add_student(student)
    print(f"Std ID:{student_id}")

    # Add an assignment
    assessment_type_id = db.get_assessment_type_id("Essay")
    assignment = Assignment(
        title="Essay on Shakespeare",
        description="Write about...",
        assessment_type_id=assessment_type_id,
    )
    assignment_id = db.add_assignment(assignment)
    print(f"Ass ID:{assignment_id}")

    assignments = [
        ("Essay on Shakespeare", "Write an essay about a Shakespeare play", "Essay"),
        ("Math Problems", "Solve 10 algebra problems", "Short Answer"),
        (
            "History Quiz",
            "Multiple choice questions about World War II",
            "Multiple Choice",
        ),
        (
            "Science Facts",
            "True/False questions about basic science concepts",
            "True/False",
        ),
    ]

    assignments_ids = db.add_multiple_assignments(assignments)
    print(f"Inserted assignment IDs: {assignments_ids}")

    # Add student work
    work = StudentWork(
        student_id=student_id,
        assignment_id=assignment_id,
        content="To be or not to be...",
    )
    work_id = db.add_student_work(work)
    print(f"Wrk ID:{work_id}")

    student_work = db.get_student_work_by_id(work_id)
    print(f"Retrieved StudentWork: {student_work}")


    # Add feedback
    feedback = Feedback(
        work_id=work_id, feedback_type="general", content="Good effort, but..."
    )
    db.add_feedback(feedback)
    print(f"fb:{feedback}")

    # Retrieve feedback
    feedbacks = db.get_feedback(work_id)
    print(f"fbs:{feedbacks}")

    # Add a resource link
    resource = ResourceLink(
        topic="Artificial Intelligence",
        url="https://example.com/ai",
        description="A comprehensive guide to AI.",
    )
    resource_2 = ResourceLink(
        topic="Education",
        url="https://example.com/education",
        description="A comprehensive guide to Education.",
    )
    link_id = db.add_resource_link(resource)
    link_id = db.add_resource_link(resource_2)

    # Fetch resource links by topic
    resource_links = db.get_resource_links_by_topic(topic="Education")
    print(resource_links)

    assessment_content = db.get_assessment_content(work_id)
    print(assessment_content)
