from datetime import timedelta
import math
import uuid
from fastcore.parallel import threaded
from fasthtml.common import *
import uvicorn
from starlette.requests import Request
from starlette.responses import RedirectResponse
from dataclasses import dataclass
from fastcore.utils import *
from fastlite import database


# Generate a dummy session ID at the start of the application
DUMMY_SESSION_ID = str(uuid.uuid4())

# Database setup

# @dataclass
# class Answer:
#     id: int
#     session_id: str
#     question_id: int
#     answer: str

db = database("data/qz.db")
tables = db.t

# answer = db.create(Answer, name="answers", if_not_exists=True)
# answers= db.table('answers')

answers = tables.answers
if answers not in tables:
    answers.create(session_id=str, question_id=int, answer=str, pk=('session_id', 'question_id'))
Answer = answers.dataclass()


# 1. Initial Setup
tlink = Script(src="https://cdn.tailwindcss.com")
dlink = Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css")

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
    },
    {
        "question": "Is the Great Wall of China visible from space? True or False?",
        "options": ["True", "False"],
        "correct_answer": "False",
        "type": "select_one"
    },
    {
        "question": "Which is the largest mammal in the world?",
        "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"],
        "correct_answer": "Blue Whale",
        "type": "select_one"
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

def progress_tracker_component(current_question, total_questions):
    progress_percentage = int((current_question / total_questions) * 100)
    return Div(
        f"{progress_percentage}%",
        cls="radial-progress text-primary-content",
        style=f"--value:{progress_percentage}; --size:7rem; --thickness: 0.7rem;",
        role="progressbar"
    )

def countdown_component(label, value, id):
    return Div(
        Span(
            Span(label, style=f"--value:{value};", id=id),
            cls="countdown font-mono text-5xl"
        ),
        cls="bg-neutral rounded-box text-neutral-content flex flex-col p-2 items-center"
    )

def timer_component(hours: int, minutes: int, seconds: int):
    return Div(
        countdown_component("hrs", hours, "hours"),
        countdown_component("min", minutes, "minutes"),
        countdown_component("sec", seconds, "seconds"),
        cls="grid auto-cols-max grid-flow-col gap-5 text-center"
    )

def pagination_button_component(prev_text, next_text, prev_page, next_page, show_submit):
    prev_button = Button(
        prev_text,
        hx_post=f"/page/{prev_page}" if prev_page else None,
        hx_target="#quiz-content",
        cls="join-item btn btn-outline" + (" btn-disabled" if prev_page is None else "")
    )

    next_button = Button(
        next_text,
        hx_post=f"/page/{next_page}" if next_page else None,
        hx_target="#quiz-content",
        cls="join-item btn btn-outline" + (" btn-disabled" if next_page is None else "")
    )

    submit_button = Button(
        "Submit",
        hx_post="/submit",
        hx_target="#quiz-content",
        cls="join-item btn btn-primary"
    ) if show_submit else None

    buttons = [prev_button] + ([submit_button] if show_submit else [next_button])

    return Div(*buttons, cls="justify-self-end mt-4 join grid grid-cols-2 rounded")

def quiz_body_component(question_number, total_questions, question, options, option_type):

    current_answer = get_answer(question_number - 1)

    radio_buttons = Div(
        *[
            Div(
                Label(
                    Span(f"{chr(65+i)}. {option}", cls="label-text"),
                    Input(
                        type="radio",
                        name=f"q{question_number-1}",
                        value=option,
                        checked=str(current_answer) == option,
                        cls="radio checked:bg-blue-500",
                    ),
                    cls="font-semibold text-xl border shadow-lg p-3 rounded-lg hover:bg-gray-100 label cursor-pointer",
                ),
                cls="form-control mb-2",
            )
            for i, option in enumerate(options)
        ],
        cls="mb-4",
    )

    checkboxes = Div(
        *[
            Div(
                Label(
                    Span(f"{chr(65+i)}. {option}", cls="label-text"),
                    Input(
                        type="checkbox",
                        name=f"q{question_number-1}",
                        value=option,
                        checked=option in current_answer if isinstance(current_answer, list) else False,
                        cls="checkbox checked:bg-blue-500",
                    ),
                    cls="font-semibold text-xl border shadow-lg p-3 rounded-lg hover:bg-gray-100 label cursor-pointer",
                ),
                cls="form-control mb-2",
            )
            for i, option in enumerate(options)
        ],
        cls="mb-4",
    )

    text_input = Div(
        Textarea(
            name=f"q{question_number-1}",
            placeholder="Enter your answer...",
            rows=7,
            content=current_answer,
            cls="textarea textarea-bordered textarea-lg w-full",
        )
    )

    if option_type == "select_one":
        options_component = radio_buttons
    elif option_type == "select_multiple":
        options_component = checkboxes
    elif option_type == "enter_text":
        options_component = text_input
    else:
        raise ValueError("Invalid option type. Supported types are 'select_one', 'select_multiple', and 'enter_text'.")

    return Form(
        Div(
            Div(
                Div(Fa("info-circle", size=40, cls="my-auto"),
                    Span(f"Question No.{question_number} of {total_questions}", cls="font-semibold text-3xl"),
                    cls="flex border bg-[#f3f4f5] rounded gap-4 px-4 py-3"),
                progress_tracker_component(question_number, total_questions),
                timer_component(time_left_global.seconds // 3600,
                                (time_left_global.seconds % 3600) // 60,
                                time_left_global.seconds % 60),
                id="timer",
                cls="flex justify-between items-center"
            ),
            Div(f"Q. {question}",
                cls="border bg-[#f3f4f5] shadow-lg my-7 rounded px-7 py-5 font-semibold text-xl"
            ),
            Div("Please choose one of the following options:" if option_type != "enter_text" else "Please enter your answer:",
                cls="text-[#666666] font-semibold text-lg"
            ),
            options_component,
            cls="border rounded-md min-h-96 shadow-md py-6 px-4",
            id="quiz-container"
        )
    )

# 4. JavaScript for Updating the Countdown
update_countdown_js = """
function updateCountdown() {
    let totalSeconds = %d;
    const countdownElement = document.getElementById('timer');
    const hoursElement = document.getElementById('hours');
    const minutesElement = document.getElementById('minutes');
    const secondsElement = document.getElementById('seconds');

    function update() {
        if (totalSeconds <= 0) {
            clearInterval(interval);
            countdownElement.innerHTML = "<span class='text-red-500'>Time's up!</span>";
            return;
        }

        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds %% 3600) / 60);
        const seconds = totalSeconds %% 60;

        hoursElement.style.setProperty('--value', hours);
        minutesElement.style.setProperty('--value', minutes);
        secondsElement.style.setProperty('--value', seconds);

        totalSeconds--;
    }

    update();
    const interval = setInterval(update, 1000);
}

updateCountdown();
""" % int(time_left_global.total_seconds())

# Navigation and Page Generation
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
    show_submit = next_page is None

    return Div(
        *[quiz_body_component(page_number, num_questions, q["question"], q["options"], q["type"]) for q in current_questions],
        Script(update_countdown_js),
        pagination_button_component("Previous" if prev_page else None, "Next" if next_page else None, prev_page, next_page, show_submit),
        id="quiz-content"
    )

# def store_answer(question_number, answer):
#     answers.insert(Answer(session_id=DUMMY_SESSION_ID, question_id=question_number, answer=answer))

def store_answer(question_number, answer):
    try:
        existing_answer = [row for row in answers.find(session_id=DUMMY_SESSION_ID, question_id=question_number)]
        if existing_answer:
            existing_answer[0]['answer'] = answer
            answers.update(existing_answer[0], ['answer'])
        else:
            answers.insert(dict(session_id=DUMMY_SESSION_ID, question_id=question_number, answer=answer))
    except Exception as e:
        print(f"Error: {e}")

def get_answer(question_number):
    try:
        row = [row for row in answers.find(session_id=DUMMY_SESSION_ID, question_id=question_number)]
        if row:
            return row[0]['answer']
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")

# Routes
@app.get("/")
def quiz_page():
    return Div(
        header_component(),
        navigate_to_page(1),
        cls="container mx-auto my-5 space-y-6"
    )

@app.post("/page/{page_number}")
async def quiz_page_with_number(request: Request, page_number: int):
    form_data = await request.form()

    for key, value in form_data.items():
        if key.startswith('q'):
            question_number = int(key[1:])
            store_answer(question_number, value)

    return navigate_to_page(page_number)

@app.post("/submit")
async def submit_quiz(request: Request):
    form_data = await request.form()

    for key, value in form_data.items():
        if key.startswith('q'):
            question_number = int(key[1:])
            store_answer(question_number, value)

    return RedirectResponse('/results', status_code=303)

def results_summary_component():
    user_answers = {a.question_id: a.answer for a in answers(where=f"session_id == '{DUMMY_SESSION_ID}'")}
    return Div(
        H2("Quiz Results Summary", cls="text-2xl font-bold mb-4"),
        *[Div(
            P(f"Question {i+1}: {questions[i]['question']}", cls="font-semibold"),
            P(f"Your answer: {user_answers.get(i, 'Not answered')}",
              cls="ml-4 mt-1 text-gray-700"),
            cls="mb-4 p-4 bg-gray-100 rounded-lg"
        ) for i in range(len(questions))],
        cls="space-y-6"
    )

@app.get("/results")
async def get_results():
    return Div(
        results_summary_component(),
        Button("Restart Quiz", hx_get="/", hx_target="body", cls="btn btn-primary mt-6"),
        cls="container mx-auto my-5 space-y-6"
    )

# 6. Main Application Execution
if __name__ == '__main__':
    uvicorn.run("app_v2:app", host="127.0.0.1", port=8002, reload=True)
