import tkinter as tk
from tkinter import messagebox, simpledialog
from quiz_app import QuizApp


class QuizGUI:
    def __init__(self, root: tk.Tk, quiz_app: QuizApp):
        self.root = root
        self.quiz_app = quiz_app
        self.current_question = None
        self.selected_choice = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        self.root.title("Quiz App")
        self.root.geometry("400x350")

        self.question_label = tk.Label(
            self.root, text="", wraplength=300, justify="center"
        )
        self.question_label.pack(pady=20)

        self.radio_buttons = []
        for i in range(4):
            rb = tk.Radiobutton(
                self.root,
                text="",
                variable=self.selected_choice,
                value="",
                wraplength=300,
            )
            rb.pack(anchor="w")
            self.radio_buttons.append(rb)

        self.next_button = tk.Button(self.root, text="Next", command=self.next_question)
        self.next_button.pack(pady=20)

        self.start_button = tk.Button(
            self.root, text="Start Quiz", command=self.start_quiz
        )
        self.start_button.pack(pady=10)

        self.stats_button = tk.Button(
            self.root, text="Quiz Statistics", command=self.show_statistics
        )
        self.stats_button.pack(pady=5)

        self.update_button = tk.Button(
            self.root, text="Update Quiz", command=self.update_quiz
        )
        self.update_button.pack(pady=5)

        self.delete_button = tk.Button(
            self.root, text="Delete Quiz", command=self.delete_quiz
        )
        self.delete_button.pack(pady=5)

    def start_quiz(self):
        """Starts the quiz and loads the first question."""
        quiz_id = simpledialog.askinteger("Start Quiz", "Enter the Quiz ID:")
        if quiz_id:
            self.quiz_app.start_quiz(quiz_id)
            if self.quiz_app.current_quiz:
                self.show_next_question()
            else:
                messagebox.showerror("Error", f"No quiz found with ID {quiz_id}")

    def show_next_question(self):
        """Displays the next question."""
        self.current_question = self.quiz_app.get_next_question()
        if self.current_question:
            self.question_label.config(text=self.current_question.question_text)
            choices = self.current_question.choices
            self.selected_choice.set("")  # Clear previous selection
            for rb, choice in zip(self.radio_buttons, choices):
                rb.config(text=choice, value=choice)
        else:
            self.finish_quiz()

    def next_question(self):
        """Handles the next button click."""
        if self.current_question:
            selected = self.selected_choice.get()
            if selected:
                self.quiz_app.submit_answer(self.current_question.question_id, selected)
                self.show_next_question()
            else:
                messagebox.showwarning(
                    "No selection", "Please select an answer before proceeding."
                )

    def finish_quiz(self):
        """Handles the end of the quiz."""
        self.quiz_app.save_quiz_results()
        correct, incorrect, unanswered = self.quiz_app.calculate_score()
        total = correct + incorrect + unanswered
        messagebox.showinfo("Quiz Finished", f"Your score: {correct}/{total}")

    def show_statistics(self):
        """Displays the statistics for the current quiz."""
        stats = self.quiz_app.get_quiz_statistics()
        if stats:
            total_questions, total_answers, correct_percentage = stats
            message = f"Total Questions: {total_questions}\n"
            message += f"Total Answers: {total_answers}\n"
            message += f"Correct Percentage: {correct_percentage:.2f}%"
            messagebox.showinfo("Quiz Statistics", message)
        else:
            messagebox.showinfo("Quiz Statistics", "No quiz statistics available.")

    def update_quiz(self):
        """Updates the current quiz information."""
        if self.quiz_app.current_quiz:
            new_title = simpledialog.askstring(
                "Update Quiz",
                "Enter new title:",
                initialvalue=self.quiz_app.current_quiz.title,
            )
            new_description = simpledialog.askstring(
                "Update Quiz",
                "Enter new description:",
                initialvalue=self.quiz_app.current_quiz.description,
            )
            if new_title and new_description:
                if self.quiz_app.update_current_quiz(new_title, new_description):
                    messagebox.showinfo("Success", "Quiz updated successfully.")
                else:
                    messagebox.showerror("Error", "Failed to update quiz.")
        else:
            messagebox.showinfo("Update Quiz", "No quiz is currently active.")

    def delete_quiz(self):
        """Deletes the current quiz."""
        if self.quiz_app.current_quiz:
            if messagebox.askyesno(
                "Delete Quiz", "Are you sure you want to delete this quiz?"
            ):
                if self.quiz_app.delete_current_quiz():
                    messagebox.showinfo("Success", "Quiz deleted successfully.")
                    self.reset_gui()
                else:
                    messagebox.showerror("Error", "Failed to delete quiz.")
        else:
            messagebox.showinfo("Delete Quiz", "No quiz is currently active.")

    def reset_gui(self):
        """Resets the GUI after quiz deletion."""
        self.question_label.config(text="")
        for rb in self.radio_buttons:
            rb.config(text="", value="")
        self.selected_choice.set("")


def main():
    root = tk.Tk()
    quiz_app = QuizApp()
    app = QuizGUI(root, quiz_app)
    root.mainloop()


if __name__ == "__main__":
    main()
