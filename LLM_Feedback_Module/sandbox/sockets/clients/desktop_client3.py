import tkinter as tk
from tkinter import ttk

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QuizApp")
        self.root.geometry("600x400")

        # Sample data for the quiz
        self.questions = [
            {
                "question": "What is the name of the process that sends one qubit of information using two bits of classical information?",
                "options": [
                    "Super Dense Coding",
                    "Quantum Programming",
                    "Quantum Teleportation",
                    "Quantum Entanglement"
                ],
                "answer": "Quantum Teleportation"
            },
            {
                "question": "Which quantum phenomenon is used to link two particles instantaneously?",
                "options": [
                    "Quantum Superposition",
                    "Quantum Entanglement",
                    "Quantum Tunneling",
                    "Quantum Decoherence"
                ],
                "answer": "Quantum Entanglement"
            }
        ]

        self.current_question_index = 0
        self.score = 0
        self.total_time = 60  # 60 seconds for the entire quiz

        self.create_widgets()
        self.update_timer()

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root, padding=(10, 5))
        header_frame.pack(fill=tk.X)

        # Question Number and Timer
        self.question_number_label = ttk.Label(header_frame, text=f"Question No.{self.current_question_index + 1} of {len(self.questions)}", font=("Arial", 12, "bold"))
        self.question_number_label.pack(side=tk.LEFT)

        timer_frame = ttk.Frame(header_frame)
        timer_frame.pack(side=tk.RIGHT)
        self.timer_label = ttk.Label(timer_frame, text="00:01:00", font=("Arial", 12, "bold"))
        self.timer_label.pack()

        # Question
        question_frame = ttk.Frame(self.root, padding=(10, 5))
        question_frame.pack(fill=tk.X)

        self.question_label = ttk.Label(question_frame, text="", wraplength=580, font=("Arial", 12))
        self.question_label.pack(fill=tk.X, pady=10)

        # Options
        options_frame = ttk.Frame(self.root, padding=(10, 5))
        options_frame.pack(fill=tk.X)

        self.selected_option = tk.StringVar()
        self.option_buttons = []
        for _ in range(4):
            option_button = ttk.Radiobutton(options_frame, text="", value="", variable=self.selected_option)
            option_button.pack(anchor=tk.W, padx=20, pady=5)
            self.option_buttons.append(option_button)

        # Buttons Frame
        button_frame = ttk.Frame(self.root, padding=(10, 5))
        button_frame.pack(fill=tk.X, pady=20)

        self.next_button = ttk.Button(button_frame, text="Next", command=self.next_question)
        self.next_button.pack(side=tk.RIGHT, padx=20)

        self.submit_button = ttk.Button(button_frame, text="Submit", command=self.end_quiz)
        self.submit_button.pack(side=tk.RIGHT, padx=20)

        # Load the first question
        self.load_question()

    def load_question(self):
        question_data = self.questions[self.current_question_index]

        self.question_number_label.config(text=f"Question No.{self.current_question_index + 1} of {len(self.questions)}")
        self.question_label.config(text=question_data["question"])

        for i, option in enumerate(question_data["options"]):
            self.option_buttons[i].config(text=option, value=option)

    def update_timer(self):
        minutes, seconds = divmod(self.total_time, 60)
        self.timer_label.config(text=f"{minutes:02}:{seconds:02}")
        if self.total_time > 0:
            self.total_time -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.end_quiz()

    def next_question(self):
        selected_answer = self.selected_option.get()
        correct_answer = self.questions[self.current_question_index]["answer"]

        if selected_answer == correct_answer:
            self.score += 1

        self.current_question_index += 1

        if self.current_question_index < len(self.questions):
            self.load_question()
        else:
            self.end_quiz()

    def end_quiz(self):
        # Handle unanswered questions
        if self.selected_option.get() == "":
            self.current_question_index += 1

        final_score_text = f"Your final score is: {self.score}/{len(self.questions)}"
        self.question_label.config(text=final_score_text)
        for button in self.option_buttons:
            button.pack_forget()
        self.next_button.pack_forget()
        self.submit_button.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
