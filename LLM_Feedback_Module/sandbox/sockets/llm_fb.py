import asyncio
import json
import logging
import os

from openai import OpenAI, OpenAIError


class LLMFeedback:

    def __init__(self, api_key, base_url, model, system_prompt):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.saved_student_works = {}

        logger = logging.getLogger(__file__)
        log_format = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=log_format)

    def get_feedback(self, content):
        student_work = content['student_work']
        assessment_type = content['assessment_type']
        prompt = f"Provide feedback on the following student work: {student_work}. The assessment type is {assessment_type}."
        return self._make_request(prompt)

    def validate_answer(self, content):
        student_answer = content['student_answer']
        correct_answer = content['correct_answer']
        prompt = f"Compare the student's answer '{student_answer}' with the correct answer '{correct_answer}'. Is the student's answer correct?"
        return self._make_request(prompt)

    def generate_suggested_enhancements(self, student_work):
        prompt = f"Suggest enhancements for the following student work: {student_work}."
        return self._make_request(prompt)

    def provide_peer_comparison(self, student_work, peer_works):
        prompt = f"Compare the following student work: {student_work} with the peer works: {peer_works}."
        return self._make_request(prompt)

    def generate_resource_links(self, topic):
        prompt = f"Provide resource links for the topic: {topic}."
        return self._make_request(prompt)

    def evaluate_effort(self, student_work):
        prompt = f"Evaluate the effort put into the following student work: {student_work}. Rate the work on a scale of 1-5, where 1 is poor and 5 is excellent."
        response = self._make_request(prompt)

        if response["response"] is None:
            return {"response": "Failed to evaluate student work."}

        try:
            rating = int(response["response"].split()[-1])
        except ValueError:
            return {"response": "Invalid rating received."}

        if rating == 1:
            feedback = "The student work is poor and lacks effort. It needs significant improvement."
        elif rating == 2:
            feedback = "The student work is below average and shows some effort. It needs improvement in several areas."
        elif rating == 3:
            feedback = "The student work is average and shows a decent amount of effort. It meets the expectations but can be improved."
        elif rating == 4:
            feedback = "The student work is good and shows a significant amount of effort. It exceeds the expectations in some areas."
        else:
            feedback = "The student work is excellent and shows an exceptional amount of effort. It far exceeds the expectations."
        return {"response": feedback}

    def get_student_opinion(self, student_work):
        prompt = f"What do you think about the following student work: {student_work}?"
        return self._make_request(prompt)

    def save_student_work(self, content):
        student_work = content['student_work']
        assessment_type = content['assessment_type']
        self.saved_student_works[student_work] = assessment_type
        return {"response": "Student work saved successfully!"}

    def load_student_work(self, content):
        assessment_type = content['assessment_type']
        student_works = [
            work for work, type in self.saved_student_works.items()
            if type == assessment_type
        ]
        return {"response": student_works}

    def load_selected_student_work(self, content):
        work_id = content['work_id']
        student_work = self.saved_student_works.get(work_id)
        if student_work:
            return {"response": student_work}
        else:
            return {"error": "Student work not found"}

    def enable_real_time_feedback(self):
        return {"response": "Real-time feedback enabled"}

    def disable_real_time_feedback(self):
        return {"response": "Real-time feedback disabled"}

    def _make_request(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],
            )
            logging.info(f"Request prompt: {prompt}")
            # logging.info(f"Response: {response}")
            return {"response": response.choices[0].message.content}
        except OpenAIError as e:
            logging.error(f"OpenAI error: {e}")
            return {"error": f"OpenAI error: {e}"}
        except Exception as e:
            logging.error(f"Error making request: {e}")
            return {"error": f"An error occurred: {e}"}


if __name__ == "__main__":
    api_key = os.getenv("AIML_API_KEY")
    base_url = "https://api.aimlapi.com"
    model = "mistralai/Mistral-7B-Instruct-v0.2"
    system_prompt = "You are an AI assistant who knows everything about education and can provide feedback on student work."
    llm_feedback = LLMFeedback(api_key, base_url, model, system_prompt)
    content = {
        "student_work":
        "Out of suffering have emerged the strongest souls; the most massive characters are seared with scars.That is why they are able to empathize with others, to understand the depths of pain and the heights of triumph. Their scars serve as a reminder of the trials they have faced and the strength they have gained from overcoming them",
        "assessment_type": "essay"
    }
    response = llm_feedback.get_feedback(content)
    print(response)
