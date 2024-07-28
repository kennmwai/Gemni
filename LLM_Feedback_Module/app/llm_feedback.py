import logging
from openai import OpenAI
import os


class LLMFeedback:

    def __init__(self, api_key, base_url, model, system_prompt):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        logging.basicConfig(level=logging.INFO)

    def get_llm_feedback(self, student_work, assessment_type):
        prompt = f"Provide feedback on the following student work: {student_work}. The assessment type is {assessment_type}."
        return self._make_request(prompt)

    def validate_answer(self, student_answer, correct_answer):
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
        prompt = f"Evaluate the effort put into the following student work: {student_work}."
        return self._make_request(prompt)

    def get_student_opinion(self, student_work):
        prompt = f"What do you think about the following student work: {student_work}?"
        return self._make_request(prompt)

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
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error making request: {e}")
            return f"An error occurred: {e}"


if __name__ == "__main__":
    system_prompt = "You are an AI assistant who knows everything about education and can provide feedback on student work."
    llm_feedback = LLMFeedback(
        api_key=os.getenv("AIML_API_KEY"),
        base_url="https://api.aimlapi.com",
        model="mistralai/Mistral-7B-Instruct-v0.2",
        system_prompt=system_prompt,
    )
    # Example usage
    print(
        llm_feedback.get_llm_feedback(
            student_work=
            "To be is not To Be but as a be-ing I am whom I am as I.",
            assessment_type="essay"))
