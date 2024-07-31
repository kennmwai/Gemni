import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog
import socket
import json
import threading


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
            "get_feedback", "validate_answer", "suggest_enhancements",
            "peer_comparison", "resource_links", "evaluate_effort",
            "student_opinion"
        ]
        self.action_dropdown = ttk.Combobox(self.master,
                                            textvariable=self.action_var,
                                            values=actions)
        self.action_dropdown.set(actions[0])
        self.action_dropdown.pack(pady=5)

        # Submit button
        self.submit_button = ttk.Button(self.master,
                                        text="Submit",
                                        command=self.send_message)
        self.submit_button.pack(pady=10)

        # Output area
        ttk.Label(self.master, text="Server Response:").pack(pady=5)
        self.output = scrolledtext.ScrolledText(self.master, height=10)
        self.output.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Connection status
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected")
        self.status_label = ttk.Label(self.master,
                                      textvariable=self.status_var)
        self.status_label.pack(pady=5)

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 8765))
            self.connected = True
            self.status_var.set("Connected to server")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.status_var.set(f"Connection failed: {str(e)}")

    def send_message(self):
        if not self.connected:
            self.output.insert(tk.END, "Not connected to server\n")
            return

        action = self.action_var.get()
        student_work = self.student_work.get("1.0", tk.END).strip()

        message = {
            "action": action,
            "content": {
                "student_work": student_work,
                "assessment_type": "essay"
            }
        }

        if action == "validate_answer":
            correct_answer = simpledialog.askstring(
                "Input", "Enter the correct answer:")
            message["content"]["student_answer"] = student_work
            message["content"]["correct_answer"] = correct_answer

        try:
            if self.socket:
                self.socket.send(json.dumps(message).encode('utf-8'))
                self.output.insert(tk.END, f"Sent request: {action}\n")
        except Exception as e:
            self.output.insert(tk.END, f"Error sending message: {str(e)}\n")

    def receive_messages(self):
        while self.connected and self.socket is not None:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                response = json.loads(data)
                self.output.insert(
                    tk.END,
                    f"Received {response['action']}:\n{response['response']}\n\n"
                )
                self.output.see(tk.END)
            except Exception as e:
                self.output.insert(tk.END,
                                   f"Error receiving message: {str(e)}\n")
                break

        self.connected = False
        self.status_var.set("Disconnected from server")


if __name__ == "__main__":
    root = tk.Tk()
    client = LLMFeedbackClient(root)
    root.mainloop()
