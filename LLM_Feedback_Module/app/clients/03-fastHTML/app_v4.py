from datetime import timedelta
import math

import uvicorn
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse

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

# User answers storage
user_answers = {}
feedback_submissions = []

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
    question_id = question_number - 1  # Adjust for 0-based indexing
    saved_answer = user_answers.get(question_id, [])

    if option_type == "select_one":
        options_component = Div(
            *[Div(
                Label(
                    Span(f"{chr(65+i)}. {option}", cls="label-text"),
                    Input(type="radio", name=f"answer_{question_id}", value=option,
                          cls="radio checked:bg-blue-500",
                          checked=(option in saved_answer)),
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
                    Input(type="checkbox", name=f"answer_{question_id}", value=option,
                          cls="checkbox checked:bg-blue-500",
                          checked=(option in saved_answer)),
                    cls="bg-white border p-3 rounded-lg hover:bg-gray-100 label cursor-pointer"
                ),
                cls="form-control mb-2"
            ) for i, option in enumerate(options)],
            cls="mb-4"
        )
    elif option_type == "enter_text":
        options_component = Div(
            Textarea(name=f"answer_{question_id}", placeholder="Enter your answer...",
                     cls="textarea textarea-bordered",
                     value=saved_answer[0] if saved_answer else "")
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

def results_summary_component():
    return Div(
        H2("Quiz Results Summary", cls="text-2xl font-bold mb-4"),
        *[Div(
            P(f"Question {i+1}: {questions[i]['question']}", cls="font-semibold"),
            P(f"Your answer: {', '.join(user_answers.get(i, ['Not answered']))}",
              cls="ml-4 mt-1 text-gray-700"),
            cls="mb-4 p-4 bg-gray-100 rounded-lg"
        ) for i in range(len(questions))],
        cls="space-y-6"
    )

def feedback_form_component():
    return Form(
        H3("We'd love to hear your feedback!", cls="text-xl font-bold mb-4"),
        Div(
            Label("How would you rate this quiz?", for_="rating", cls="block mb-2"),
            Select(
                Option("5 - Excellent", value="5"),
                Option("4 - Good", value="4"),
                Option("3 - Average", value="3"),
                Option("2 - Below Average", value="2"),
                Option("1 - Poor", value="1"),
                name="rating",
                id="rating",
                cls="select select-bordered w-full max-w-xs"
            ),
            cls="mb-4"
        ),
        Div(
            Label("Do you have any additional comments?", for_="comments", cls="block mb-2"),
            Textarea(name="comments", id="comments", placeholder="Enter your comments here...", cls="textarea textarea-bordered w-full"),
            cls="mb-4"
        ),
        Button("Submit Feedback", cls="btn btn-primary"),
        hx_post="/feedback",
        hx_target="#feedback-response",
        cls="mt-6 p-4 bg-gray-100 rounded-lg"
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

    submit_button = Button("Submit", hx_post="/submit", hx_target="body", cls="btn btn-success mx-1") if page_number == num_pages else None

    return Form(
        *[quiz_body_component(page_number, num_questions, q["question"], q["options"], q["type"]) for q in current_questions],
        pagination_button_component("Previous" if prev_page else None, "Next" if next_page else None, prev_page, next_page),
        submit_button,
        id="quiz-form",
        hx_post=f"/save-answer/{page_number-1}"
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
async def quiz_page_with_number(page_number: int):
    return navigate_to_page(page_number)

@app.post("/save-answer/{question_id}")
async def save_answer(question_id: int, request: Request):
    form_data = await request.form()
    answer_key = f"answer_{question_id}"
    if answer_key in form_data:
        user_answers[question_id] = form_data.getlist(answer_key)

    # Determine the next page
    next_page = question_id + 2  # +2 because question_id is 0-indexed and we want the next page
    if next_page > len(questions):
        return RedirectResponse(url="/results", status_code=303)
    return navigate_to_page(next_page)

@app.get("/update-timer")
def update_timer():
    global time_left_global
    time_left_global -= timedelta(seconds=1)
    if time_left_global.total_seconds() <= 0:
        return Div("Time's up!", cls="text-red-500 font-bold text-2xl", id="timer")
    return timer_component(time_left_global.seconds // 3600,
                           (time_left_global.seconds % 3600) // 60,
                           time_left_global.seconds % 60)

@app.post("/submit")
async def submit_quiz():
    return RedirectResponse(url="/results", status_code=303)

@app.get("/results")
async def get_results():
    return Div(
        results_summary_component(),
        feedback_form_component(),
        Div(id="feedback-response"),
        Button("Restart Quiz", hx_get="/", hx_target="body", cls="btn btn-secondary mt-6"),
        cls="container mx-auto my-5 space-y-6"
    )

@app.post("/feedback")
async def submit_feedback(request: Request):
    form_data = await request.form()
    rating = form_data.get("rating")
    comments = form_data.get("comments")

    feedback_submissions.append({"rating": rating, "comments": comments})

    return Div(
        P("Thank you for your feedback!", cls="text-green-600 font-bold"),
        cls="mt-4 p-4 bg-green-100 rounded-lg"
    )


# 6. Main Application Execution
if __name__ == '__main__':
    uvicorn.run("app_v4:app", host="127.0.0.1", port=8004, reload=True)