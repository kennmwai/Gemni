import json
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk
from dataclasses import dataclass
from typing import Optional


@dataclass
class AssessmentContent:
    student_work: str
    assessment_type: str
    correct_answer: Optional[str] = None
    peer_works: Optional[str] = None
    topic: Optional[str] = None
    work_id: Optional[int] = None

class LLMFeedbackClient:
    def __init__(self, master):
        self.master = master
        master.title("LLM Feedback Client")
        master.geometry("600x500")

        self.socket = None
        self.connected = False

        self.create_widgets()
        self.connect_to_server()

    def create_widgets(self):
        # Student work input
        ttk.Label(self.master, text="Enter student work:").pack(pady=5)
        self.student_work = scrolledtext.ScrolledText(self.master, height=5)
        self.student_work.pack(padx=10, pady=5, fill=tk.X)

        # Action selection
        ttk.Label(self.master, text="Select action:").pack(pady=5)
        self.action_var = tk.StringVar()
        actions = [
            "get_feedback",
            "validate_answer",
            "peer_comparison",
            "resource_links",
            "evaluate_effort",
            "student_opinion",
        ]
        self.action_dropdown = ttk.Combobox(
            self.master, textvariable=self.action_var, values=actions
        )
        self.action_dropdown.set(actions[0])
        self.action_dropdown.pack(pady=5)

        # Submit button
        self.submit_button = ttk.Button(
            self.master, text="Submit", command=self.send_message
        )
        self.submit_button.pack(pady=10)

        # Output area
        ttk.Label(self.master, text="Server Response:").pack(pady=5)
        self.output = scrolledtext.ScrolledText(self.master, height=10)
        self.output.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Connection status
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected")
        self.status_label = ttk.Label(self.master, textvariable=self.status_var)
        self.status_label.pack(pady=5)

        # Reconnect button
        self.reconnect_button = ttk.Button(
            self.master, text="Reconnect", command=self.reconnect_to_server
        )
        self.update_reconnect_button()

    def update_reconnect_button(self):
        if self.connected:
            self.reconnect_button.pack_forget()
        else:
            self.reconnect_button.pack()
        self.master.after(100, self.update_reconnect_button)

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(("localhost", 8765))
            self.connected = True
            self.status_var.set("Connected to server")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.status_var.set(f"Connection failed: {str(e)}")

    def reconnect_to_server(self):
        self.connect_to_server()

    def send_message(self):
        if not self.connected:
            self.output.insert(tk.END, "Not connected to server\n")
            return

        action = self.action_var.get()
        student_work = self.student_work.get("1.0", tk.END).strip()

        assessment_content = AssessmentContent(
            student_work=student_work,
            assessment_type="essay",
            work_id=1 # Will implement a way to get or generate this
        )

        if action == "validate_answer":
            correct_answer = simpledialog.askstring("Input", "Enter the correct answer:")
            assessment_content.correct_answer = correct_answer

        if action == "peer_comparison":
            peer_works = simpledialog.askstring("Input", "Enter peer works (comma-separated):")
            assessment_content.peer_works = peer_works

        if action == "resource_links":
            topic = simpledialog.askstring("Input", "Enter the topic:")
            assessment_content.topic = topic

        message = {
            "action": action,
            "content": assessment_content.__dict__
        }

        try:
            self.socket.send(json.dumps(message).encode("utf-8"))
            self.output.insert(tk.END, f"Sent request: {action}\n")
        except Exception as e:
            self.output.insert(tk.END, f"Error sending message: {str(e)}\n")

    def receive_messages(self):
        while self.connected:
            try:
                data = b""
                while True:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    try:
                        response = json.loads(data.decode('utf-8'))
                        break
                    except json.JSONDecodeError:
                        continue  # Keep receiving data if it's not complete JSON yet

                if not data:
                    break

                if 'action' in response and 'response' in response:
                    self.output.insert(
                        tk.END,
                        f"Received {response['action']}:\n{response['response']}\n\n",
                    )
                    self.output.see(tk.END)
                else:
                    self.output.insert(tk.END, f"Received unexpected response format: {response}\n\n")
            except Exception as e:
                self.output.insert(tk.END, f"Error receiving message: {str(e)}\n")
                break

        self.connected = False
        self.status_var.set("Disconnected from server")


if __name__ == "__main__":
    root = tk.Tk()
    client = LLMFeedbackClient(root)
    root.mainloop()
