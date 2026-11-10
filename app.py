import streamlit as st
import random
import time
import plotly.graph_objects as go

# --- PAGE CONFIGURATION & CUSTOM CSS (Interactive BG & Theme) ---
st.set_page_config(page_title="CogniSharp Gym", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Dark Glassmorphism Theme
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(15, 23, 42) 0%, rgb(30, 27, 75) 90%);
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    /* Hide default header/footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Top Stats Bar */
    .stats-bar {
        display: flex; justify-content: space-around; 
        background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(10px);
        padding: 15px; border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 30px; font-weight: bold; font-size: 1.1em;
    }
    
    /* Custom Card Buttons */
    div[data-testid="stButton"] button {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        color: #f1f5f9;
        padding: 20px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stButton"] button:hover {
        border-color: #6366f1;
        background: rgba(49, 46, 129, 0.6);
        transform: translateY(-3px);
        color: white;
    }
    div[data-testid="stButton"] button:active {
        transform: translateY(0px);
    }
    
    /* Explanation Box */
    .exp-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #6366f1;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'xp': 0, 'streak': 0, 'best_streak': 0, 'total_q': 0, 'total_correct': 0,
        'cat': {
            'Memory': {'c': 0, 't': 0}, 'Spatial': {'c': 0, 't': 0},
            'Pattern': {'c': 0, 't': 0}, 'Logic': {'c': 0, 't': 0}, 'Math': {'c': 0, 't': 0}
        }
    }
if 'session_q' not in st.session_state:
    st.session_state.session_q = []
if 'q_idx' not in st.session_state:
    st.session_state.q_idx = 0
if 'q_start_time' not in st.session_state:
    st.session_state.q_start_time = 0
if 'times' not in st.session_state:
    st.session_state.times = []
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'feedback_html' not in st.session_state:
    st.session_state.feedback_html = ""

# --- 5 PROCEDURAL QUESTION GENERATORS ---

def gen_memory():
    start, mult, add, div = random.randint(4, 12), random.randint(2, 4), random.randint(3, 10), random.choice([2, 3])
    s1 = start * mult
    s2 = s1 + add
    if s2 % div != 0: s2 += (div - (s2 % div)) # ensure clean division
    ans = int(s2 / div)
    opts = [ans, ans + random.randint(1,3), ans - random.randint(1,2), ans + random.randint(4,5)]
    random.shuffle(opts)
    return {
        "cat": "Memory", "title": "Sequential Math Chain",
        "q": f"Start with {start} ➔ Multiply by {mult} ➔ Add {s2-s1} ➔ Divide by {div}",
        "opts": opts, "ans": ans,
        "exp": f"1) Start: {start}<br>2) {start} x {mult} = {s1}<br>3) {s1} + {s2-s1} = {s2}<br>4) {s2} ÷ {div} = <b>{ans}</b>"
    }

def gen_spatial():
    pos = ["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"]
    start_pos = random.choice(pos)
    deg = random.choice([90, 180, 270])
    # 90 deg clockwise mapping
    cmap = {"Top-Left":"Top-Right", "Top-Right":"Bottom-Right", "Bottom-Right":"Bottom-Left", "Bottom-Left":"Top-Left"}
    ans = start_pos
    for _ in range(deg // 90): ans = cmap[ans]
    opts = pos.copy()
    random.shuffle(opts)
    return {
        "cat": "Spatial", "title": "Grid Rotation",
        "q": f"A symbol is at the <b>{start_pos}</b> of a 3x3 grid. If the grid rotates <b>{deg}° Clockwise</b>, where does it land?",
        "opts": opts, "ans": ans,
        "exp": f"Rotating {deg}° clockwise means shifting {deg//90} step(s) around the corners. {start_pos} moves to <b>{ans}</b>."
    }

def gen_pattern():
    words = ["MIND", "BOLD", "FAST", "GRID", "PEAK"]
    word = random.choice(words)
    shift = random.randint(1, 3)
    def shift_word(w, s): return ''.join(chr(ord(c) + s) for c in w)
    ans = shift_word(word, shift)
    opts = [ans, shift_word(word, shift+1), shift_word(word, shift-1 if shift>1 else shift+2), shift_word(word, shift+2)]
    random.shuffle(opts)
    return {
        "cat": "Pattern", "title": "Cipher Shift",
        "q": f"Rule: BRAIN ➔ {shift_word('BRAIN', shift)}<br>Target: {word} ➔ ?",
        "opts": opts, "ans": ans,
        "exp": f"The cipher shifts every letter forward by <b>+{shift}</b>. Applying this to {word} gives <b>{ans}</b>."
    }

def gen_logic():
    datasets = [
        {"items": ["Ostrich", "Emu", "Penguin", "Eagle"], "odd": "Eagle", "exp": "All others are flightless birds."},
        {"items": ["Mercury", "Venus", "Mars", "Jupiter"], "odd": "Jupiter", "exp": "Jupiter is a gas giant; the rest are terrestrial."},
        {"items": ["Square", "Circle", "Triangle", "Cube"], "odd": "Cube", "exp": "Cube is 3D; all others are 2D shapes."}
    ]
    d = random.choice(datasets)
    opts = d["items"].copy()
    random.shuffle(opts)
    return {
        "cat": "Logic", "title": "Odd One Out",
        "q": "Identify the ODD one out in this set:",
        "opts": opts, "ans": d["odd"],
        "exp": f"<b>{d['odd']}</b> is the odd one out. Reason: {d['exp']}"
    }

def gen_math():
    a, b, c = random.randint(12, 25), random.randint(11, 19), random.randint(15, 30)
    ans = (a * b) - c
    opts = [ans, ans+10, ans-10, ans+random.randint(1,5)]
    random.shuffle(opts)
    return {
        "cat": "Math", "title": "Speed Number Sense",
        "q": f"Calculate mentally: ({a} × {b}) - {c}",
        "opts": opts, "ans": ans,
        "exp": f"First multiply: {a} × {b} = {a*b}. Then subtract: {a*b} - {c} = <b>{ans}</b>."
    }

# --- LOGIC CONTROLLERS ---

def start_workout():
    st.session_state.session_q = [gen_memory(), gen_spatial(), gen_pattern(), gen_logic(), gen_math()]
    random.shuffle(st.session_state.session_q)
    st.session_state.q_idx = 0
    st.session_state.times = []
    st.session_state.answered = False
    st.session_state.view = 'game'
    st.session_state.q_start_time = time.time()

def check_answer(opt):
    time_taken = round(time.time() - st.session_state.q_start_time, 1)
    st.session_state.times.append(time_taken)
    st.session_state.answered = True
    
    q = st.session_state.session_q[st.session_state.q_idx]
    stats = st.session_state.stats
    
    stats['total_q'] += 1
    stats['cat'][q['cat']]['t'] += 1
    
    if opt == q['ans']:
        stats['total_correct'] += 1
        stats['streak'] += 1
        stats['xp'] += 20
        stats['cat'][q['cat']]['c'] += 1
        if stats['streak'] > stats['best_streak']: stats['best_streak'] = stats['streak']
        st.session_state.feedback_html = f"<h3 style='color:#34d399'>Correct! (+20 XP)</h3>⏱️ Time: {time_taken}s<br><br>{q['exp']}"
    else:
        stats['streak'] = 0
        st.session_state.feedback_html = f"<h3 style='color:#f87171'>Incorrect</h3>⏱️ Time: {time_taken}s<br><br>Correct Answer: <b>{q['ans']}</b><br><br>{q['exp']}"

def next_question():
    st.session_state.q_idx += 1
    st.session_state.answered = False
    if st.session_state.q_idx >= len(st.session_state.session_q):
        st.session_state.view = 'results'
    else:
        st.session_state.q_start_time = time.time()

# --- TOP NAVIGATION BAR ---
acc = int((st.session_state.stats['total_correct'] / st.session_state.stats['total_q']) * 100) if st.session_state.stats['total_q'] > 0 else 0
st.markdown(f"""
<div class='stats-bar'>
    <span style='color:#818cf8'>🧠 CogniSharp</span>
    <span style='color:#fbbf24'>🔥 Streak: {st.session_state.stats['streak']}</span>
    <span style='color:#a78bfa'>⚡ XP: {st.session_state.stats['xp']}</span>
    <span style='color:#34d399'>🎯 Accuracy: {acc}%</span>
</div>
""", unsafe_allow_html=True)


# --- VIEWS ROUTING ---

if st.session_state.view == 'dashboard':
    st.markdown("<h1 style='text-align: center; color: white;'>Sharpen Your Cognitive Agility</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1; margin-bottom: 40px;'>Dynamic algorithms generate unique puzzles to stretch your mental boundaries.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("▶ Start Quick Workout (5 Questions)", on_click=start_workout)
    
    st.markdown("<br><h3 style='color: white;'>Target Specific Cognitive Domains</h3>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div style='padding:20px; background:rgba(30,41,59,0.7); border-radius:12px; border:1px solid #334155;'><b>🔢 Working Memory</b><br><span style='color:#94a3b8; font-size:14px;'>Sequential Math Chains</span></div>", unsafe_allow_html=True)
    c2.markdown("<div style='padding:20px; background:rgba(30,41,59,0.7); border-radius:12px; border:1px solid #334155;'><b>🌀 Spatial Reasoning</b><br><span style='color:#94a3b8; font-size:14px;'>Grid Rotation & Orientation</span></div>", unsafe_allow_html=True)
    c3.markdown("<div style='padding:20px; background:rgba(30,41,59,0.7); border-radius:12px; border:1px solid #334155;'><b>🔐 Pattern Decoding</b><br><span style='color:#94a3b8; font-size:14px;'>Cipher & Pattern Shifts</span></div>", unsafe_allow_html=True)
    
    st.write("")
    c4, c5, c6 = st.columns(3)
    c4.markdown("<div style='padding:20px; background:rgba(30,41,59,0.7); border-radius:12px; border:1px solid #334155;'><b>⚖️ Deductive Logic</b><br><span style='color:#94a3b8; font-size:14px;'>Semantic Categorical Matrices</span></div>", unsafe_allow_html=True)
    c5.markdown("<div style='padding:20px; background:rgba(30,41,59,0.7); border-radius:12px; border:1px solid #334155;'><b>⚡ Mental Speed</b><br><span style='color:#94a3b8; font-size:14px;'>Speed Number Sense</span></div>", unsafe_allow_html=True)
    with c6:
        st.button("📊 View Cognitive Analytics", on_click=lambda: st.session_state.update(view='analytics'))


elif st.session_state.view == 'game':
    q = st.session_state.session_q[st.session_state.q_idx]
    
    st.markdown(f"<p style='color:#818cf8; font-weight:bold; margin:0;'>{q['cat'].upper()} • Question {st.session_state.q_idx + 1} of 5</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:white; margin-top:0;'>{q['title']}</h2>", unsafe_allow_html=True)
    
    # Progress Bar visually
    progress = (st.session_state.q_idx) / 5
    st.progress(progress)
    
    st.markdown(f"<h3 style='color:#e2e8f0; font-weight:400;'>{q['q']}</h3>", unsafe_allow_html=True)
    st.write("")

    # Answer Grid
    c1, c2 = st.columns(2)
    opts = q['opts']
    
    if not st.session_state.answered:
        for i, opt in enumerate(opts):
            col = c1 if i % 2 == 0 else c2
            col.button(str(opt), key=f"ans_{i}", on_click=check_answer, args=(opt,))
    else:
        # Show disabled buttons after answering
        for i, opt in enumerate(opts):
            col = c1 if i % 2 == 0 else c2
            col.button(str(opt), key=f"ans_dis_{i}", disabled=True)
            
        st.markdown(f"<div class='exp-box'>{st.session_state.feedback_html}</div><br>", unsafe_allow_html=True)
        st.button("Next Challenge ➔", on_click=next_question, type="primary")


elif st.session_state.view == 'results':
    st.markdown("<center><h1 style='color:white;'>Session Completed!🏆</h1></center>", unsafe_allow_html=True)
    avg_t = round(sum(st.session_state.times) / len(st.session_state.times), 1) if st.session_state.times else 0
    
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Average Speed", f"{avg_t} sec")
    rc2.metric("Questions Answered", "5")
    rc3.metric("Total XP", st.session_state.stats['xp'])
    
    st.write("")
    bc1, bc2 = st.columns(2)
    bc1.button("🏠 Main Menu", on_click=lambda: st.session_state.update(view='dashboard'))
    bc2.button("📊 View Profile Analytics", on_click=lambda: st.session_state.update(view='analytics'))


elif st.session_state.view == 'analytics':
    st.markdown("<h2 style='color:white;'>Cognitive Profile & Analytics</h2>", unsafe_allow_html=True)
    st.button("← Back to Dashboard", on_click=lambda: st.session_state.update(view='dashboard'))
    
    sc1, sc2 = st.columns([1, 1])
    
    # Calculate percentages for radar chart
    cat_stats = st.session_state.stats['cat']
    radar_vals = []
    labels = ['Memory', 'Spatial', 'Pattern', 'Logic', 'Math']
    for label in labels:
        t = cat_stats[label]['t']
        radar_vals.append(int((cat_stats[label]['c'] / t) * 100) if t > 0 else 0)
        
    # Close the radar loop
    radar_vals.append(radar_vals[0])
    plot_labels = labels + [labels[0]]
    
    with sc1:
        st.markdown("### Domain Proficiency")
        fig = go.Figure(data=go.Scatterpolar(
            r=radar_vals,
            theta=plot_labels,
            fill='toself',
            line_color='#818cf8',
            fillcolor='rgba(129, 140, 248, 0.3)'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor='#334155', tickfont=dict(color='#94a3b8')),
                angularaxis=dict(gridcolor='#334155', tickfont=dict(color='white'))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with sc2:
        st.markdown("### Lifetime Metrics")
        st.markdown(f"""
        <div style='background:rgba(30,41,59,0.7); padding:20px; border-radius:12px; margin-bottom:15px; border:1px solid #334155;'>
            <div style='color:#94a3b8; font-size:12px; text-transform:uppercase;'>Total Questions Solved</div>
            <div style='color:white; font-size:32px; font-weight:bold;'>{st.session_state.stats['total_q']}</div>
        </div>
        <div style='background:rgba(30,41,59,0.7); padding:20px; border-radius:12px; margin-bottom:15px; border:1px solid #334155;'>
            <div style='color:#94a3b8; font-size:12px; text-transform:uppercase;'>Best Streak</div>
            <div style='color:#fbbf24; font-size:32px; font-weight:bold;'>🔥 {st.session_state.stats['best_streak']}</div>
        </div>
        <div style='background:rgba(30,41,59,0.7); padding:20px; border-radius:12px; border:1px solid #334155;'>
            <div style='color:#94a3b8; font-size:12px; text-transform:uppercase;'>Global Accuracy</div>
            <div style='color:#34d399; font-size:32px; font-weight:bold;'>🎯 {acc}%</div>
        </div>
        """, unsafe_allow_html=True)
