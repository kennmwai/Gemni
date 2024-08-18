import logging
import os
from openai import OpenAI, OpenAIError
from database import (
    Database,
    AssessmentContent,
    Feedback,
    LLMRequest,
    Student,
    StudentWork,
    ResourceLink,
    Assignment,
)


class LLMFeedback:
    def __init__(self, api_key, base_url, model, system_prompt, db_path):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.db = Database(db_path)

        log_format = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
        logging.getLogger(__file__)
        logging.basicConfig(level=logging.DEBUG, format=log_format)

    def get_feedback(self, content: AssessmentContent):
        if content.work_id is None:
            return {"error": "Invalid AssessmentContent: work_id is required"}

        prompt = self._generate_prompt(content)
        response = self._make_request(prompt)

        if "response" in response:
            feedback = Feedback(
                work_id=content.work_id,
                feedback_type="AI-generated",
                content=response["response"],
            )
            feedback_id = self.db.add_feedback(feedback)

            if feedback_id is None:
                return {
                    "error": "Failed to save feedback to database",
                    "response": response["response"],
                }

        return response

    def validate_answer(self, content):
        student_answer = content.student_work
        correct_answer = content.correct_answer
        prompt = f"Compare the student's answer '{student_answer}' with the correct answer '{correct_answer}'. Is the student's answer correct?"
        return self._make_request(prompt)

    def generate_suggested_enhancements(self, content):
        prompt = f"Suggest enhancements for the following student work: {content.student_work}."
        return self._make_request(prompt)

    def provide_peer_comparison(self, content):
        prompt = f"Compare the following student work: {content.student_work} with the peer works: {content.peer_works}."
        return self._make_request(prompt)

    def generate_resource_links(self, content):
        prompt = f"Provide resource links for the topic: {content.topic}."
        response = self._make_request(prompt)

        if "response" in response:
            # Assuming the response contains a list of resource links
            links = response["response"].split("\n")
            for link in links:
                topic, url = link.split(": ")
                self.db.add_resource_link(
                    ResourceLink(topic=topic, url=url, description="")
                )

        return response

    def evaluate_effort(self, content):
        prompt = f"Evaluate the effort put into the following student work: {content.student_work}. Rate the work on a scale of 1-5, where 1 is poor and 5 is excellent."
        response = self._make_request(prompt)

        if response["response"] is None:
            return {"response": "Failed to evaluate student work."}

        try:
            rating = int(response["response"].split()[-1])
        except ValueError:
            return {"response": "Invalid rating received."}

        feedback_messages = {
            1: "The student work is poor and lacks effort. It needs significant improvement.",
            2: "The student work is below average and shows some effort. It needs improvement in several areas.",
            3: "The student work is average and shows a decent amount of effort. It meets the expectations but can be improved.",
            4: "The student work is good and shows a significant amount of effort. It exceeds the expectations in some areas.",
            5: "The student work is excellent and shows an exceptional amount of effort. It far exceeds the expectations.",
        }

        feedback_content = feedback_messages.get(
            rating, "Unable to determine feedback based on the rating."
        )

        feedback = Feedback(
            work_id=content.work_id,
            feedback_type="Effort Evaluation",
            content=feedback_content,
        )
        self.db.add_feedback(feedback)

        return {"response": feedback_content}

    def _generate_prompt(self, content: AssessmentContent, focus: str = "general"):
        prompt = f"Provide detailed feedback on the following student work. Be constructive and specific in your comments.\n\nStudent work: {content.student_work}\nAssessment type: {content.assessment_type}"

        if content.correct_answer:
            prompt += f"\n\nCorrect answer: {content.correct_answer}\nCompare the student's work to the correct answer and highlight any discrepancies."

        if content.peer_works:
            prompt += f"\n\nPeer works: {content.peer_works}\nCompare the student's work to these peer examples, noting strengths and areas for improvement relative to peers."

        if content.topic:
            prompt += f"\n\nTopic: {content.topic}\nEnsure the feedback is relevant to this specific topic."

        prompt += "\n\nBased on all this information, provide a comprehensive feedback that includes:\n1. Strengths of the work\n2. Areas for improvement\n3. Specific suggestions for enhancement\n4. An overall assessment of the work"

        if focus == "grammar":
            prompt += (
                "\nPay special attention to grammar and language use in your feedback."
            )
        elif focus == "content":
            prompt += (
                "\nFocus primarily on the content and ideas presented in the work."
            )
        elif focus == "structure":
            prompt += "\nPay particular attention to the structure and organization of the work in your feedback."

        return prompt

    def _make_request(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            logging.info(f"Request prompt: {prompt}")

            llm_request = LLMRequest(
                prompt=prompt,
                response=response.choices[0].message.content,
                model=self.model,
            )
            self.db.log_llm_request(llm_request)

            return {"response": response.choices[0].message.content}
        except OpenAIError as e:
            logging.error(f"OpenAI error: {e}")
            return {"error": f"OpenAI error: {e}"}
        except Exception as e:
            logging.error(f"Error making request: {e}")
            return {"error": f"An error occurred: {e}"}


if __name__ == "__main__":
    api_key = os.getenv("AIML_API_KEY", "")
    base_url = "https://api.aimlapi.com"
    model = "mistralai/Mistral-7B-Instruct-v0.2"
    system_prompt = "You are an AI assistant who knows everything about education and can provide feedback on student work."
    db_path = "education_feedback.db"

    # Initialize the Database
    db = Database(db_path)

    # Initialize LLMFeedback with the database
    llm_feedback = LLMFeedback(api_key, base_url, model, system_prompt, db_path)

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
