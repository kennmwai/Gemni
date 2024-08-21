import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from quiz_app import QuizApp, Question


class QuizGUI:
    def __init__(self, root: tk.Tk, quiz_app: QuizApp):
        self.root = root
        self.quiz_app = quiz_app
        self.current_question = None
        self.selected_choice = tk.StringVar()
        self.timer_value = tk.StringVar()
        self.question_number = tk.StringVar()
        self.total_time = 30
        self.remaining_time = self.total_time
        self.create_widgets()
        self.style_widgets()

    def create_widgets(self):
        self.root.title("QuizApp")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")

        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))

        self.question_number_label = ttk.Label(
            self.header_frame,
            textvariable=self.question_number,
            font=("Arial", 12, "bold"),
        )
        self.question_number_label.pack(side=tk.LEFT)

        self.timer_label = ttk.Label(
            self.header_frame, textvariable=self.timer_value, font=("Arial", 12, "bold")
        )
        self.timer_label.pack(side=tk.RIGHT)

        self.question_frame = ttk.Frame(self.main_frame)
        self.question_frame.pack(fill=tk.BOTH, expand=True)

        self.question_label = ttk.Label(
            self.question_frame,
            text="",
            wraplength=550,
            justify="left",
            font=("Arial", 12),
        )
        self.question_label.pack(pady=(0, 20))

        self.choices_frame = ttk.Frame(self.question_frame)
        self.choices_frame.pack(fill=tk.BOTH, expand=True)

        self.radio_buttons = []
        for i in range(4):
            rb = ttk.Radiobutton(
                self.choices_frame, text="", variable=self.selected_choice, value=""
            )
            rb.pack(anchor="w", pady=5)
            self.radio_buttons.append(rb)

        self.text_answer = tk.Text(self.question_frame, height=4, width=50)
        self.text_answer.pack(pady=10, fill=tk.BOTH, expand=True)

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(20, 0))

        self.next_button = ttk.Button(
            self.button_frame, text="Next", command=self.next_question
        )
        self.submit_button = ttk.Button(
            self.button_frame, text="Submit Quiz", command=self.submit_quiz
        )

        # Initially hide the next and submit buttons
        self.hide_quiz_buttons()
        self.show_existing_quizzes()

        self.start_button = ttk.Button(
            self.main_frame, text="Start Quiz", command=self.start_quiz
        )
        self.start_button.pack(pady=20)

    def style_widgets(self):
        style = ttk.Style()
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", font=("Arial", 11))
        style.configure("TRadiobutton", background="#ffffff", font=("Arial", 11))
        style.configure("TButton", font=("Arial", 11))

    def hide_quiz_buttons(self):
        # self.choices_frame.pack_forget()
        self.text_answer.pack_forget()
        self.next_button.pack_forget()
        self.submit_button.pack_forget()

    def show_existing_quizzes(self):
        self.selected_choice.set(None)
        self.choices_frame.pack(fill=tk.BOTH, expand=True)
        choices = self.quiz_app.get_all_quizzes()
        for rb, choice in zip(self.radio_buttons, choices):
            rb.config(text=choice.title, value=choice.quiz_id)

    def show_quiz_buttons(self):
        self.submit_button.pack(side=tk.LEFT)
        self.next_button.pack(side=tk.RIGHT)

    def start_quiz(self):
        self.remaining_time = self.total_time
        quiz_id = self.selected_choice.get()
        if not quiz_id:
            quiz_id = simpledialog.askinteger("Start Quiz", "Enter the Quiz ID:")

        if quiz_id:
            try:
                self.quiz_app.start_quiz(quiz_id)
                if self.quiz_app.current_quiz:
                    self.start_button.pack_forget()
                    self.show_quiz_buttons()  # Show the next and submit buttons
                    self.show_next_question()
                    self.start_timer()
                else:
                    messagebox.showerror("Error", f"No quiz found with ID {quiz_id}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    def show_next_question(self):
        self.current_question = self.quiz_app.get_next_question()
        if self.current_question:
            self.question_number.set(
                f"Question No.{self.quiz_app.current_question_index} of {len(self.quiz_app.questions)}"
            )
            self.question_label.config(text=self.current_question.question_text)
            if self.current_question.is_open_ended:
                # Clear previous selection and show the text widget
                self.selected_choice.set(None)
                self.text_answer.delete("1.0", tk.END)
                self.text_answer.pack(pady=10, fill=tk.BOTH, expand=True)
                self.choices_frame.pack_forget()
            else:
                # Clear previous text and show the radio buttons
                self.selected_choice.set(None)
                self.text_answer.pack_forget()
                self.choices_frame.pack(fill=tk.BOTH, expand=True)
                choices = self.current_question.choices
                for rb, choice in zip(self.radio_buttons, choices):
                    rb.config(text=choice, value=choice)
        else:
            self.finish_quiz()

    def next_question(self):
        if self.current_question:
            if (
                isinstance(self.current_question, Question)
                and self.current_question.is_open_ended
            ):
                answer = self.text_answer.get("1.0", tk.END).strip()
                if answer:
                    self.quiz_app.submit_answer(
                        self.current_question.question_id, answer
                    )
                    self.show_next_question()
                else:
                    messagebox.showwarning(
                        "No input", "Please provide an answer before proceeding."
                    )
            else:
                selected = self.selected_choice.get()
                if selected:
                    self.quiz_app.submit_answer(
                        self.current_question.question_id, selected
                    )
                    self.show_next_question()
                else:
                    messagebox.showwarning(
                        "No selection", "Please select an answer before proceeding."
                    )

    def start_timer(self):
        self.update_timer()

    def update_timer(self):
        if self.remaining_time > 0:
            minutes, seconds = divmod(self.remaining_time, 60)
            self.timer_value.set(f"{minutes:02d}:{seconds:02d}")
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.finish_quiz()

    def submit_quiz(self):
        if messagebox.askyesno(
            "Submit Quiz", "Are you sure you want to submit the quiz?"
        ):
            self.finish_quiz()

    def finish_quiz(self):
        self.quiz_app.save_quiz_results()
        correct, incorrect, unanswered = self.quiz_app.calculate_score()
        total = correct + incorrect + unanswered
        messagebox.showinfo("Quiz Finished", f"Your score: {correct}/{total}")
        self.root.quit()


def main():
    root = tk.Tk()
    quiz_app = QuizApp()
    app = QuizGUI(root, quiz_app)
    root.mainloop()


if __name__ == "__main__":
    main()
