from dataclasses import dataclass
from random import randint
from bakery import assert_equal
from drafter import *


# These are global constants. They are settings used by the whole game.
DIFFICULTIES = ["easy", "medium", "hard"]
ROUND_OPTIONS = ["5", "10", "15", "20"]
TIMER_OPTIONS = ["10", "15", "30", "60"]
POINTS_PER_ANSWER = 10


@dataclass
class Question:
    """
    Stores one math question and the player's response.

    prompt: The math problem shown to the player.
    answer: The correct numerical answer.
    user_answer: What the player entered, or "Timed out".
    correct: Whether the player's answer was correct.
    time_used: 0 for a submitted answer; timer_limit for a timeout.
    """
    prompt: str
    answer: int
    user_answer: str
    correct: bool
    time_used: int


@dataclass
class GameRecord:
    """
    Stores the final results of one completed game for the leaderboard.
    """
    score: int
    difficulty: str
    rounds_completed: int
    accuracy: int


@dataclass
class State:
    """
    Stores information that needs to be remembered between website pages.
    """
    difficulty: str
    current_round: int
    total_rounds: int
    streak: int
    score: int
    timer_limit: int
    questions: list[Question]
    highest_streak: int
    best_score: int
    best_streak: int
    games_played: int
    game_history: list[GameRecord]
    recorded: bool


def make_question(difficulty: str) -> Question:
    """
    Make a random math question for the selected difficulty.

    Random questions are difficult to unit test because the numbers change
    each time. The question-making helper is therefore tested by playing
    the game rather than comparing it to one fixed random result.
    """
    if difficulty == "easy":
        first = randint(1, 10)
        second = randint(1, 10)
        operation = randint(1, 2)

        if operation == 1:
            prompt = str(first) + " + " + str(second)
            answer = first + second
        else:
            if first < second:
                temporary = first
                first = second
                second = temporary
            prompt = str(first) + " - " + str(second)
            answer = first - second

    elif difficulty == "medium":
        operation = randint(1, 2)

        if operation == 1:
            first = randint(10, 50)
            second = randint(10, 50)
            prompt = str(first) + " + " + str(second)
            answer = first + second
        else:
            first = randint(2, 12)
            second = randint(2, 12)
            prompt = str(first) + " × " + str(second)
            answer = first * second

    else:
        operation = randint(1, 3)

        if operation == 1:
            first = randint(100, 500)
            second = randint(100, 500)
            prompt = str(first) + " + " + str(second)
            answer = first + second
        elif operation == 2:
            first = randint(10, 25)
            second = randint(10, 25)
            prompt = str(first) + " × " + str(second)
            answer = first * second
        else:
            divisor = randint(2, 15)
            quotient = randint(2, 15)
            first = divisor * quotient
            prompt = str(first) + " ÷ " + str(divisor)
            answer = quotient

    return Question(prompt, answer, "", False, 0)


def calculate_accuracy(questions: list[Question]) -> int:
    """
    Calculate the percentage of questions answered correctly.
    """
    if len(questions) == 0:
        return 0

    correct_count = 0
    for question in questions:
        if question.correct:
            correct_count += 1

    return int(correct_count / len(questions) * 100)


def calculate_highest_streak(questions: list[Question]) -> int:
    """
    Find the longest sequence of correct answers in the question history.

    This loop meaningfully examines the list of Question dataclass instances.
    """
    current_streak = 0
    highest = 0

    for question in questions:
        if question.correct:
            current_streak += 1
            if current_streak > highest:
                highest = current_streak
        else:
            current_streak = 0

    return highest


# Unit tests for the helper functions.
test_questions = [
    Question("1 + 1", 2, "2", True, 0),
    Question("2 + 2", 4, "4", True, 0),
    Question("3 + 3", 6, "5", False, 0),
    Question("4 + 4", 8, "8", True, 0),
]
assert_equal(calculate_accuracy(test_questions), 75)
assert_equal(calculate_highest_streak(test_questions), 2)
assert_equal(calculate_accuracy([]), 0)
assert_equal(calculate_highest_streak([]), 0)


@route
def index(state: State) -> Page:
    """Show the title page and the main navigation buttons."""
    return Page(state, [
        Header("MATH RUSH"),
        "Challenge yourself with quick mental-math questions!",
        "Choose your settings, build a streak, and try to beat your best score.",
        Button("Start a Game", "settings_page"),
        Button("How to Play", "instructions_page"),
        Button("Leaderboard", "leaderboard_page"),
    ])


@route
def instructions_page(state: State) -> Page:
    """Explain the rules of Math Rush."""
    return Page(state, [
        Header("How to Play"),
        "1. Choose an easy, medium, or hard difficulty.",
        "2. Choose how many questions you want to answer.",
        "3. Choose a time allowance for each question.",
        "4. Enter your answer and press Submit Answer.",
        "5. Correct answers earn " + str(POINTS_PER_ANSWER) + " points.",
        "6. Consecutive correct answers build your streak.",
        "7. An incorrect answer or timeout resets your streak.",
        "Note: The timer setting is a time allowance. Use the timeout button "
        "when your time runs out; this version does not display an automatic "
        "countdown.",
        Button("Back Home", "index"),
        Button("Choose Settings", "settings_page"),
    ])


@route
def settings_page(state: State) -> Page:
    """Let the player choose the difficulty, number of rounds, and time limit."""
    return Page(state, [
        Header("Game Settings"),
        "Choose your game settings below.",
        "Difficulty:",
        SelectBox("difficulty", DIFFICULTIES, state.difficulty),
        "Number of questions:",
        SelectBox("rounds", ROUND_OPTIONS, str(state.total_rounds)),
        "Seconds allowed per question:",
        SelectBox("timer", TIMER_OPTIONS, str(state.timer_limit)),
        Button("Start Game", "start_game"),
        Button("Back Home", "index"),
    ])


@route
def start_game(
    state: State, difficulty: str, rounds: str, timer: str
) -> Page:
    """Save the selected settings and begin a new game."""
    if difficulty not in DIFFICULTIES:
        difficulty = "easy"

    if rounds not in ROUND_OPTIONS:
        rounds = "5"

    if timer not in TIMER_OPTIONS:
        timer = "30"

    state.difficulty = difficulty
    state.total_rounds = int(rounds)
    state.timer_limit = int(timer)
    state.current_round = 1
    state.streak = 0
    state.score = 0
    state.highest_streak = 0
    state.questions = []
    state.recorded = False

    state.questions.append(make_question(state.difficulty))
    return game_page(state)


@route
def game_page(state: State) -> Page:
    if len(state.questions) == 0:
        return settings_page(state)

    current_question = state.questions[-1]

    return Page(state, [
        Header("MATH RUSH - Round " + str(state.current_round)),
        "Difficulty: " + state.difficulty,
        "Question " + str(state.current_round) + " of "
        + str(state.total_rounds),
        Header(current_question.prompt),
        TextBox("answer", ""),
        Button("Submit Answer", "submit_answer"),
        Button("I Ran Out of Time", "timeout"),
        "Score: " + str(state.score),
        "Current streak: " + str(state.streak),
        "Time allowance: " + str(state.timer_limit) + " seconds",
        Button("Quit to Home", "index"),
    ])


@route
def submit_answer(state: State, answer: str) -> Page:
    """Check the submitted answer and update the score and streak."""
    if len(state.questions) == 0:
        return settings_page(state)

    current_question = state.questions[-1]
    cleaned_answer = answer.strip()

    # Math questions in this game have non-negative whole-number answers.
    if not cleaned_answer.isdigit():
        return Page(state, [
            Header("Please enter a number"),
            "Your answer must contain digits only.",
            Button("Try Again", "game_page"),
        ])

    current_question.user_answer = cleaned_answer
    current_question.time_used = 0

    if int(cleaned_answer) == current_question.answer:
        current_question.correct = True
        state.score += POINTS_PER_ANSWER
        state.streak += 1

        if state.streak > state.highest_streak:
            state.highest_streak = state.streak
    else:
        current_question.correct = False
        state.streak = 0

    return result_page(state)


@route
def timeout(state: State) -> Page:
    """Record that the player ran out of time on the current question."""
    if len(state.questions) == 0:
        return settings_page(state)

    current_question = state.questions[-1]
    current_question.user_answer = "Timed out"
    current_question.correct = False
    current_question.time_used = state.timer_limit
    state.streak = 0

    return result_page(state)


@route
def result_page(state: State) -> Page:
    """Show feedback for the most recently answered question."""
    if len(state.questions) == 0:
        return settings_page(state)

    current_question = state.questions[-1]

    if current_question.user_answer == "Timed out":
        message = "Time ran out! The correct answer was "
        message += str(current_question.answer) + "."
    elif current_question.correct:
        message = "Correct! Great job. You earned "
        message += str(POINTS_PER_ANSWER) + " points."
    else:
        message = "Not quite! The correct answer was "
        message += str(current_question.answer) + "."

    return Page(state, [
        Header("Round Result"),
        message,
        "Your score: " + str(state.score),
        "Your current streak: " + str(state.streak),
        Button("Continue", "next_round"),
        Button("Quit to Home", "index"),
    ])


@route
def next_round(state: State) -> Page:
    """Move to the next question or finish the game."""
    if state.current_round >= state.total_rounds:
        return summary_page(state)

    state.current_round += 1
    state.questions.append(make_question(state.difficulty))
    return game_page(state)


@route
def summary_page(state: State) -> Page:
    """Show final game statistics and save this game to the history."""
    accuracy = calculate_accuracy(state.questions)
    state.highest_streak = calculate_highest_streak(state.questions)

    # The recorded field prevents the same game being saved twice if the
    # player visits the summary page again.
    if not state.recorded:
        if state.score > state.best_score:
            state.best_score = state.score

        if state.highest_streak > state.best_streak:
            state.best_streak = state.highest_streak

        record = GameRecord(
            state.score,
            state.difficulty,
            len(state.questions),
            accuracy,
        )
        state.game_history.append(record)
        state.games_played += 1
        state.recorded = True

    return Page(state, [
        Header("Game Complete!"),
        "Final score: " + str(state.score),
        "Questions completed: " + str(len(state.questions)),
        "Accuracy: " + str(accuracy) + "%",
        "Highest streak: " + str(state.highest_streak),
        "Games played: " + str(state.games_played),
        Button("Play Again", "settings_page"),
        Button("View Leaderboard", "leaderboard_page"),
        Button("Home", "index"),
    ])


@route
def leaderboard_page(state: State) -> Page:
    content = [
        Header("Leaderboard"),
        "Best score: " + str(state.best_score),
        "Longest streak: " + str(state.best_streak),
        "Games played: " + str(state.games_played),
        Header("Previous Games"),
    ]

    if len(state.game_history) == 0:
        content.append("No completed games yet. Play a game to get started.")
    else:
        # This loop displays information from each GameRecord instance.
        for record in state.game_history:
            description = (
                "Score: " + str(record.score)
                + " | Difficulty: " + record.difficulty
                + " | Rounds: " + str(record.rounds_completed)
                + " | Accuracy: " + str(record.accuracy) + "%"
            )
            content.append(description)

    content.append(Button("Back Home", "index"))
    content.append(Button("Play a Game", "settings_page"))
    return Page(state, content)


# A few route tests use fixed state values so their results are predictable.
test_state = State(
    "easy", 1, 5, 0, 0, 30, [], 0, 0, 0, 0, [], False
)
assert_equal(index(test_state).state, test_state)
assert_equal(instructions_page(test_state).state, test_state)
assert_equal(settings_page(test_state).state, test_state)

# This test checks the answer-handling route without relying on randomness.
answer_test_state = State(
    "easy",
    1,
    1,
    0,
    0,
    30,
    [Question("2 + 2", 4, "", False, 0)],
    0,
    0,
    0,
    0,
    [],
    False,
)
answer_test_page = submit_answer(answer_test_state, "4")
assert_equal(answer_test_page.state.score, POINTS_PER_ANSWER)
assert_equal(answer_test_page.state.streak, 1)

# This test checks that a timeout resets the streak.
timeout_test_state = State(
    "easy",
    1,
    1,
    2,
    20,
    30,
    [Question("2 + 2", 4, "", False, 0)],
    2,
    0,
    0,
    0,
    [],
    False,
)
timeout_test_page = timeout(timeout_test_state)
assert_equal(timeout_test_page.state.streak, 0)
assert_equal(timeout_test_page.state.questions[-1].time_used, 30)


# The initial values are set here when the Drafter website starts.
initial_state = State(
    "easy", 1, 5, 0, 0, 30, [], 0, 0, 0, 0, [], False
)
start_server(initial_state)
