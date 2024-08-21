import tkinter as tk
from quiz_gui3 import QuizGUI
from quiz_app import QuizApp

def main():
    root = tk.Tk()
    quiz_app = QuizApp()
    app = QuizGUI(root, quiz_app)
    root.mainloop()

if __name__ == "__main__":
    main()
