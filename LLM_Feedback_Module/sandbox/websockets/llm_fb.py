import asyncio
import json
import logging
import os
import socketserver
import threading
from http.server import SimpleHTTPRequestHandler

import websockets
from openai import OpenAI


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
            logging.info(f"Response: {response}")
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error making request: {e}")
            return f"An error occurred: {e}"

    async def handle_websocket(self, websocket, path):
        async for message in websocket:
            data = json.loads(message)
            action = data.get('action')
            content = data.get('content')

            if action == 'get_feedback':
                response = self.get_llm_feedback(content['student_work'],
                                                 content['assessment_type'])
            elif action == 'validate_answer':
                response = self.validate_answer(content['student_answer'],
                                                content['correct_answer'])
            elif action == 'suggest_enhancements':
                response = self.generate_suggested_enhancements(
                    content['student_work'])
            elif action == 'peer_comparison':
                response = self.provide_peer_comparison(
                    content['student_work'], content['peer_works'])
            elif action == 'resource_links':
                response = self.generate_resource_links(content['topic'])
            elif action == 'evaluate_effort':
                response = self.evaluate_effort(content['student_work'])
            elif action == 'student_opinion':
                response = self.get_student_opinion(content['student_work'])
            else:
                response = "Invalid action"

            await websocket.send(
                json.dumps({
                    'action': action,
                    'response': response
                }))


class HttpHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)


def run_http_server():
    with socketserver.TCPServer(("", 8000), HttpHandler) as httpd:
        print("Serving HTTP on port 8000")
        httpd.serve_forever()


async def main():
    system_prompt = "You are an AI assistant who knows everything about education and can provide feedback on student work."
    llm_feedback = LLMFeedback(
        api_key=os.getenv("AIML_API_KEY"),
        base_url="https://api.aimlapi.com",
        model="mistralai/Mistral-7B-Instruct-v0.2",
        system_prompt=system_prompt,
    )

    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    # Start WebSocket server
    async with websockets.serve(llm_feedback.handle_websocket, "localhost",
                                8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
