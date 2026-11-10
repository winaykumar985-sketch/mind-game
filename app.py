import streamlit as st
import random

st.set_page_config(page_title="CogniSharp Gym", page_icon="brain")

if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'
if 'questions_answered' not in st.session_state:
    st.session_state.questions_answered = 0
if 'current_q' not in st.session_state:
    st.session_state.current_q = None

def generate_math_question():
    a = random.randint(10, 25)
    b = random.randint(10, 20)
    ans = a + b
    options = [ans, ans + random.randint(1, 5), ans - random.randint(1, 5)]
    random.shuffle(options)
    return {"text": f"What is {a} + {b}?", "options": options, "answer": ans}

def generate_logic_question():
    items = ["Mercury", "Venus", "Mars", "Jupiter"]
    odd = "Jupiter"
    options = items.copy()
    random.shuffle(options)
    return {"text": "Which is the odd one out (Gas Giant)?", "options": options, "answer": odd}

def start_game():
    st.session_state.score = 0
    st.session_state.questions_answered = 0
    st.session_state.current_view = 'gameplay'
    st.session_state.current_q = generate_math_question()

def check_answer(selected):
    if selected == st.session_state.current_q["answer"]:
        st.session_state.score += 1
    st.session_state.questions_answered += 1
    
    if st.session_state.questions_answered >= 5:
        st.session_state.current_view = 'results'
    else:
        if random.choice([True, False]):
            st.session_state.current_q = generate_math_question()
        else:
            st.session_state.current_q = generate_logic_question()

def go_home():
    st.session_state.current_view = 'dashboard'

if st.session_state.current_view == 'dashboard':
    st.title("CogniSharp: Mind Agility Engine")
    st.write("Sharpen Your Cognitive Agility")
    st.button("Start Quick Workout", on_click=start_game)

elif st.session_state.current_view == 'gameplay':
    st.title("Workout in Progress")
    st.write(f"Question {st.session_state.questions_answered + 1} of 5")
    st.subheader(st.session_state.current_q["text"])
    
    for opt in st.session_state.current_q["options"]:
        st.button(str(opt), on_click=check_answer, args=(opt,))

elif st.session_state.current_view == 'results':
    st.title("Session Completed!")
    st.write(f"Your Score: {st.session_state.score} / 5")
    st.button("Main Menu", on_click=go_home)
