
from .constants import BOT_WELCOME_MESSAGE, PYTHON_QUESTION_LIST


def generate_bot_responses(message, session):
    bot_responses = []

    current_question_id = session.get("current_question_id")
    if not current_question_id:
        bot_responses.append(BOT_WELCOME_MESSAGE)

    success, error = record_current_answer(message, current_question_id, session)

    if not success:
        return [error]

    next_question, next_question_id = get_next_question(current_question_id)

    if next_question:
        bot_responses.append(next_question)
    else:
        final_response = generate_final_response(session)
        bot_responses.append(final_response)

    session["current_question_id"] = next_question_id
    session.save()

    return bot_responses


def record_current_answer(answer, current_question_id, session):
    """
    Validates and stores the answer for the current question to Django session.
    """
    if current_question_id is None:
        return False, "No current question to answer."

    # Retrieve the current question from the question list
    try:
        question = PYTHON_QUESTION_LIST[current_question_id]
    except IndexError:
        return False, "Invalid question ID."

    # Validate the answer
    if answer not in question["options"]:
        return False, f"Invalid answer. Please choose one of the following: {', '.join(question['options'])}"

    # Check if the answer is correct
    is_correct = answer == question["answer"]

    # Store the result in the session
    user_answers = session.get("user_answers", {})
    user_answers[current_question_id] = {
        "answer": answer,
        "is_correct": is_correct,
    }
    session["user_answers"] = user_answers
    session.save()

    return True, ""

def get_next_question(current_question_id):
    """
    Fetches the next question from the PYTHON_QUESTION_LIST based on the current_question_id.
    Returns the question text and its index. If there are no more questions, returns None, -1.
    """
    if current_question_id is None:
        # Start with the first question if no current question ID exists
        next_question_id = 0
    else:
        next_question_id = current_question_id + 1

    # Check if the next question ID is within the list bounds
    if next_question_id < len(PYTHON_QUESTION_LIST):
        next_question = PYTHON_QUESTION_LIST[next_question_id]
        # Format the question text with options
        formatted_question = (
            f"{next_question['question_text']}\n"
            f"Options:\n"
            + "\n".join([f"{i + 1}. {option}" for i, option in enumerate(next_question["options"])])
        )
        return formatted_question, next_question_id

    # No more questions
    return None, -1

def generate_final_response(session):
    """
    Creates a final result message including a score based on the answers
    provided by the user for questions in the PYTHON_QUESTION_LIST.
    """
    # Retrieve the user's answers from the session
    user_answers = session.get("user_answers", {})
    total_questions = len(PYTHON_QUESTION_LIST)
    correct_answers = sum(1 for answer in user_answers.values() if answer["is_correct"])

    # Generate a performance summary
    performance = f"You answered {correct_answers} out of {total_questions} questions correctly.\n"
    percentage_score = (correct_answers / total_questions) * 100
    performance += f"Your score: {percentage_score:.2f}%\n\n"

    # Provide detailed feedback
    performance += "Here's a breakdown of your answers:\n"
    for question_id, answer_data in user_answers.items():
        question = PYTHON_QUESTION_LIST[question_id]
        user_answer = answer_data["answer"]
        correct_answer = question["answer"]
        performance += (
            f"Q{question_id + 1}: {question['question_text']}\n"
            f"Your Answer: {user_answer}\n"
            f"Correct Answer: {correct_answer}\n"
        )
        if answer_data["is_correct"]:
            performance += "Result: ✅ Correct\n\n"
        else:
            performance += "Result: ❌ Incorrect\n\n"

    # Return the final performance summary
    return performance
