from datetime import timedelta
import math

import uvicorn
from fasthtml.common import *

# 1. Initial Setup
tlink = Script(src="https://cdn.tailwindcss.com")
dlink = Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css")
# htmx_script = Script(src="https://unpkg.com/htmx.org@1.9.6")

app = FastHTML(hdrs=(tlink, dlink))

time_left_global = timedelta(hours=1, minutes=1, seconds=0)

questions = [
    {
        "question": "What is the name of the process that sends one qubit of information using two bits of classical information?",
        "options": ["Super Dense Coding", "Quantum Programming", "Quantum Teleportation", "Quantum Entanglement"],
        "type": "select_one"
    },
    {
        "question": "Which of the following are principles of quantum mechanics?",
        "options": ["Superposition", "Entanglement", "Quantum Teleportation", "Classical Mechanics"],
        "type": "select_multiple"
    },
    {
        "question": "What is the name of the famous physicist who developed the theory of quantum mechanics?",
        "options": [],
        "type": "enter_text"
    }
]

# 2. Utility Functions
def Fa(icon_name, size=None, cls=""):
    size_cls = f"text-{size}px" if size else ""
    return I(cls=f"fa fa-{icon_name} {size_cls} {cls}")

# 3. Components
def header_component():
    return Div(Div("QuizApp", cls="text-white font-semibold text-3xl p-4"),
               cls="bg-[#1b1c1d] h-14 flex flex-col justify-center rounded-md")

def countdown_component(label, value, id):
    return Div(
        Span(
            Span(style=f"--value:{value};", id=id),
            cls="countdown font-mono text-5xl"
        ),
        cls="bg-neutral rounded-box text-neutral-content flex flex-col p-2 items-center"
    )

def timer_component(hours: int, minutes: int, seconds: int):
    return Div(
        countdown_component("hours", hours, "hours"),
        countdown_component("min", minutes, "minutes"),
        countdown_component("sec", seconds, "seconds"),
        cls="grid auto-cols-max grid-flow-col gap-5 text-center",
        id="timer",
        hx_get="/update-timer",
        hx_trigger="every 1s",
        hx_swap="outerHTML"
    )

def pagination_button_component(prev_text, next_text, prev_page, next_page):
    prev_button = Button(prev_text,
                         hx_post=f"/page/{prev_page}" if prev_page else None,
                         hx_target="#quiz-content",
                         cls="btn btn-primary mx-1" + (" btn-disabled" if prev_page is None else ""))
    next_button = Button(next_text,
                         hx_post=f"/page/{next_page}" if next_page else None,
                         hx_target="#quiz-content",
                         cls="btn btn-primary mx-1" + (" btn-disabled" if next_page is None else ""))
    return Div(prev_button, next_button, cls="pagination-buttons mt-4")

def quiz_body_component(question_number, total_questions, question, options, option_type):
    if option_type == "select_one":
        options_component = Div(
            *[Div(
                Label(
                    Span(f"{chr(65+i)}. {option}", cls="label-text"),
                    Input(type="radio", name="answer", value=option, cls="radio checked:bg-blue-500"),
                    cls="bg-white border p-3 rounded-lg hover:bg-gray-100 label cursor-pointer"
                ),
                cls="form-control mb-2"
            ) for i, option in enumerate(options)],
            cls="mb-4"
        )
    elif option_type == "select_multiple":
        options_component = Div(
            *[Div(
                Label(
                    Span(f"{chr(65+i)}. {option}", cls="label-text"),
                    Input(type="checkbox", name="answer", value=option, cls="checkbox checked:bg-blue-500"),
                    cls="bg-white border p-3 rounded-lg hover:bg-gray-100 label cursor-pointer"
                ),
                cls="form-control mb-2"
            ) for i, option in enumerate(options)],
            cls="mb-4"
        )
    elif option_type == "enter_text":
        options_component = Div(
            Textarea(name="answer", placeholder="Enter your answer...", cls="textarea textarea-bordered")
        )
    else:
        raise ValueError("Invalid option type. Supported types are 'select_one', 'select_multiple', and 'enter_text'.")

    return Div(
        Div(
            Div(Fa("info-circle", size=40, cls="my-auto"),
                Span(f"Question No.{question_number} of {total_questions}",
                     cls="font-semibold text-3xl"),
                cls="flex border bg-[#f3f4f5] rounded gap-4 px-4 py-3"),
            timer_component(time_left_global.seconds // 3600,
                            (time_left_global.seconds % 3600) // 60,
                            time_left_global.seconds % 60),
            cls="flex justify-between"),
        Div(f"Q. {question}",
            cls="border bg-[#f3f4f5] shadow-lg my-7 rounded px-7 py-5 font-semibold text-xl"
            ),
        Div("Please choose one of the following options:" if option_type != "enter_text" else "Please enter your answer:",
            cls="text-[#666666] font-semibold text-lg"),
        options_component,
        cls="border rounded-md min-h-96 shadow-md py-6 px-4",
        id="quiz-content"
    )

# 4. Navigation and Page Generation
def navigate_to_page(page_number):
    num_questions = len(questions)
    questions_per_page = 1
    num_pages = math.ceil(num_questions / questions_per_page)

    if page_number < 1 or page_number > num_pages:
        raise ValueError("Invalid page number")

    start_index = (page_number - 1) * questions_per_page
    end_index = start_index + questions_per_page

    current_questions = questions[start_index:end_index]

    prev_page = page_number - 1 if page_number > 1 else None
    next_page = page_number + 1 if page_number < num_pages else None

    return Div(
        *[quiz_body_component(page_number, num_questions, q["question"], q["options"], q["type"]) for q in current_questions],
        pagination_button_component("Previous" if prev_page else None, "Next" if next_page else None, prev_page, next_page),
        id="quiz-content"
    )

# 5. Routes
@app.get("/")
def quiz_page():
    return Div(
        header_component(),
        navigate_to_page(1),
        cls="container mx-auto my-5"
    )

@app.post("/page/{page_number}")
def quiz_page_with_number(page_number: int):
    return navigate_to_page(page_number)

@app.get("/update-timer")
def update_timer():
    global time_left_global
    time_left_global -= timedelta(seconds=1)
    if time_left_global.total_seconds() <= 0:
        return Div("Time's up!", cls="text-red-500 font-bold text-2xl", id="timer")
    return timer_component(time_left_global.seconds // 3600,
                           (time_left_global.seconds % 3600) // 60,
                           time_left_global.seconds % 60)

# 6. Main Application Execution
if __name__ == '__main__':
    uvicorn.run("app_v3:app", host="127.0.0.1", port=8003, reload=True)