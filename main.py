import streamlit as st
# import openai
import json
import os
import random
import time

from openai import OpenAI

client = OpenAI(
  api_key='',
)
# Function to load lesson content
def load_lesson(lesson_number):
    with open(f'lessons/lesson_{lesson_number}.txt', 'r') as file:
        return file.read()

# Function to generate questions using GPT
def generate_questions(lesson_content):
    prompt = f"Generate 5 questions based on the following content:\n{lesson_content}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a Teacher"},
            {"role": "user", "content": prompt}
        ]
        )
    questions = response.choices[0].message.content.strip().split('\n')
    return [q for q in questions if q]

# Function to evaluate answers and provide hints
def evaluate_answer_and_provide_hint(question, answer):
    prompt = f"Evaluate the following answer:\nQuestion: {question}\nAnswer: {answer}\nIs the answer correct? (yes/no). If no, provide a hint."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a Teacher"},
            {"role": "user", "content": prompt}
        ]
        )
    evaluation = response.choices[0].message.content.strip()
    print("evaluation->",evaluation)
    if 'yes' in evaluation.lower():
        correct = True
        hint = None
    else:
        correct = False
        hint = evaluation.split('Hint:')[-1].strip() if 'Hint:' in evaluation else "Please review the related concepts."
    return correct, hint

# Function to provide explanation for correct answers
def provide_explanation(question, answer):
    prompt = f"Provide a detailed explanation for the following correct answer:\nQuestion: {question}\nAnswer: {answer}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a Teacher"},
            {"role": "user", "content": prompt}
        ]
        )
    explanation = response.choices[0].message.content.strip()
    return explanation

# Function to save student progress
def save_progress(progress):
    with open('student_progress.json', 'w') as file:
        json.dump(progress, file)

# Function to load student progress
def load_progress():
    if os.path.exists('student_progress.json'):
        with open('student_progress.json', 'r') as file:
            return json.load(file)
    else:
        return {}

# Function to check if video exists
def check_video_exists(lesson_number):
    return os.path.exists(f'videos/lesson_{lesson_number}.mp4')

# Function to generate a video (placeholder for actual implementation)
def generate_video(lesson_number, lesson_content):
    # Placeholder: Simulating video generation
    st.info(f"Generating video for Lesson {lesson_number}. This may take a few moments...")
    time.sleep(5)  # Simulate time taken to generate video
    with open(f'videos/lesson_{lesson_number}.mp4', 'w') as f:
        f.write("This is a placeholder for the generated video content.")
    st.success("Video generated successfully!")

# Main Streamlit UI
def main():
    st.set_page_config(layout="wide")  # Make the page layout wide
    st.title("Educational Tutor Chatbot")
    
    # Load student progress
    progress = load_progress()
    student_name = st.text_input("Enter your name:")
    
    if student_name:
        if student_name not in progress:
            progress[student_name] = {}

        lesson_number = st.selectbox("Select a Lesson:", [f"Lesson {i+1}" for i in range(10)])
        lesson_index = int(lesson_number.split()[1])
        lesson_content = load_lesson(lesson_index)

        mode = st.radio("Choose Mode:", ["Learning", "Assessment"])

        if mode == "Learning":
            st.subheader("Learning Stage")
            
            col1, col2 = st.columns([2, 1])  # Create two columns with different widths
            
            with col1:
                st.write(lesson_content)
                
                question = st.text_input("Have any questions?")
                if st.button("Ask"):
                    prompt=f"Explain the following concept: {question}"
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a Teacher"},
                            {"role": "user", "content": prompt}
                        ]
                        )
                    st.write(response.choices[0].message.content.strip())
                    
                if st.button("Understood"):
                    st.write("Great! You can now move on to the assessment.")

            with col2:
                if st.button("Generate Video"):
                    if check_video_exists(lesson_index):
                        st.video(f'videos/lesson_{lesson_index}.mp4')
                    else:
                        generate_video(lesson_index, lesson_content)
                        st.video(f'videos/lesson_{lesson_index}.mp4')

        elif mode == "Assessment":
            st.subheader("Assessment Stage")

            # Initialize session state for question index and score
            if 'question_index' not in st.session_state:
                st.session_state.question_index = 0
                st.session_state.score = 0
                st.session_state.attempts = 0
                st.session_state.questions = generate_questions(lesson_content)
                st.session_state.current_question = st.session_state.questions[st.session_state.question_index]
                st.session_state.hint = None

            if st.session_state.question_index < len(st.session_state.questions):
                question = st.session_state.current_question
                st.write(f"Question {st.session_state.question_index + 1}: {question}")
                answer = st.text_input("Your answer:", key="current_answer")

                if st.button("Submit Answer"):
                    correct, hint = evaluate_answer_and_provide_hint(question, answer)
                    if correct:
                        st.session_state.score += 1
                        explanation = provide_explanation(question, answer)
                        st.success("Correct!")
                        st.write(f"Explanation: {explanation}")
                        st.session_state.question_index += 1
                        if st.session_state.question_index < len(st.session_state.questions):
                            st.session_state.current_question = st.session_state.questions[st.session_state.question_index]
                            st.session_state.hint = None
                    else:
                        st.error("Incorrect.")
                        st.session_state.hint = hint

                if st.session_state.hint:
                    st.write(f"Hint: {st.session_state.hint}")
                    retry_answer = st.text_input("Retry your answer:", key="retry_answer")
                    if st.button("Submit Retry Answer"):
                        correct_retry, _ = evaluate_answer_and_provide_hint(question, retry_answer)
                        if correct_retry:
                            st.session_state.score += 1
                            explanation = provide_explanation(question, retry_answer)
                            st.success("Correct!")
                            st.write(f"Explanation: {explanation}")
                            st.session_state.question_index += 1
                            if st.session_state.question_index < len(st.session_state.questions):
                                st.session_state.current_question = st.session_state.questions[st.session_state.question_index]
                                st.session_state.hint = None
                        else:
                            st.error("Incorrect again. Please review the lesson and try again.")
                            st.session_state.question_index += 1
                            if st.session_state.question_index < len(st.session_state.questions):
                                st.session_state.current_question = st.session_state.questions[st.session_state.question_index]
                                st.session_state.hint = None

            if st.session_state.question_index >= len(st.session_state.questions):
                st.write("Assessment Completed.")
                st.write(f"Your score: {st.session_state.score}/{len(st.session_state.questions)}")
                if st.session_state.score >= 4:
                    st.success(f"You passed the assessment with a score of {st.session_state.score}/5!")
                    progress[student_name][lesson_number] = "Completed"
                else:
                    st.warning(f"You scored {st.session_state.score}/5. Please review the lesson and try again.")

        save_progress(progress)

if __name__ == "__main__":
    main()