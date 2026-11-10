import streamlit as st
import random
import time
import plotly.graph_objects as go
import requests

# --- PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="CogniSharp Gym", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(15, 23, 42) 0%, rgb(30, 27, 75) 90%);
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stats-bar {
        display: flex; justify-content: space-around; 
        background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(10px);
        padding: 15px; border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 30px; font-weight: bold; font-size: 1.1em;
    }
    
    div[data-testid="stButton"] button {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        color: #f1f5f9;
        padding: 20px 10px;
        width: 100%;
        height: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        font-weight: 600;
        font-size: 1.05em;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #6366f1;
        background: rgba(49, 46, 129, 0.6);
        transform: translateY(-3px);
        color: white;
    }
    
    .exp-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #6366f1;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- CLOUD DATABASE AUTO-SAVE FUNCTIONS ---
def load_cloud_db():
    try:
        url = f"https://api.jsonbin.io/v3/b/{st.secrets['BIN_ID']}/latest"
        headers = {"X-Master-Key": st.secrets['BIN_KEY']}
        res = requests.get(url, headers=headers)
        return res.json().get('record', {})
    except Exception:
        return {} # Failsafe if secrets aren't set yet

def save_cloud_db(data):
    try:
        url = f"https://api.jsonbin.io/v3/b/{st.secrets['BIN_ID']}"
        headers = {"X-Master-Key": st.secrets['BIN_KEY'], "Content-Type": "application/json"}
        requests.put(url, json=data, headers=headers)
    except Exception:
        pass

# --- SESSION STATE INITIALIZATION ---
if 'view' not in st.session_state: st.session_state.view = 'login'
if 'username' not in st.session_state: st.session_state.username = None
if 'all_profiles' not in st.session_state: st.session_state.all_profiles = {}
if 'stats' not in st.session_state: st.session_state.stats = None
if 'session_q' not in st.session_state: st.session_state.session_q = []
if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
if 'q_start_time' not in st.session_state: st.session_state.q_start_time = 0
if 'times' not in st.session_state: st.session_state.times = []
if 'answered' not in st.session_state: st.session_state.answered = False
if 'feedback_html' not in st.session_state: st.session_state.feedback_html = ""

# --- 5 PROCEDURAL GENERATORS (WITH PROGRESSIVE DIFFICULTY) ---
def gen_memory(level):
    start = random.randint(3 + level, 7 + level*2)
    mult = random.randint(2, 2 + (level//2))
    add = random.randint(2 + level, 8 + level*2)
    div = random.choice([2, 3]) if level < 3 else random.choice([3, 4])
    s1 = start * mult
    s2 = s1 + add
    if s2 % div != 0: s2 += (div - (s2 % div)) 
    ans = int(s2 / div)
    opts = [ans, ans + random.randint(1,3), ans - random.randint(1,3), ans + random.randint(4,6)]
    random.shuffle(opts)
    return {
        "cat": "Memory", "title": f"Sequential Math Chain (Level {level})",
        "q": f"Start with {start} ➔ Multiply by {mult} ➔ Add {s2-s1} ➔ Divide by {div}",
        "opts": opts, "ans": ans,
        "exp": f"1) {start} x {mult} = {s1}<br>2) {s1} + {s2-s1} = {s2}<br>3) {s2} ÷ {div} = <b>{ans}</b>"
    }

def gen_spatial(level):
    pos = ["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"]
    start_pos = random.choice(pos)
    cmap = {"Top-Left":"Top-Right", "Top-Right":"Bottom-Right", "Bottom-Right":"Bottom-Left", "Bottom-Left":"Top-Left"}
    if level <= 2:
        deg = random.choice([90, 180])
        desc, net_steps = f"{deg}° Clockwise", deg // 90
    elif level == 3:
        deg = random.choice([270, -90]) 
        desc, net_steps = ("270° Clockwise", 3) if deg == 270 else ("90° Counter-Clockwise", -1)
    else:
        s1, s2 = random.choice([90, 180]), random.choice([90, 180])
        dir1 = random.choice(["Clockwise", "Counter-Clockwise"])
        dir2 = "Counter-Clockwise" if dir1 == "Clockwise" else "Clockwise"
        desc = f"{s1}° {dir1}, THEN {s2}° {dir2}"
        step1 = s1//90 if dir1 == "Clockwise" else -(s1//90)
        step2 = s2//90 if dir2 == "Clockwise" else -(s2//90)
        net_steps = step1 + step2
        
    ans = start_pos
    for _ in range(net_steps % 4): ans = cmap[ans]
    opts = pos.copy()
    random.shuffle(opts)
    return {
        "cat": "Spatial", "title": f"Grid Rotation (Level {level})",
        "q": f"A symbol is at the <b>{start_pos}</b> of a 3x3 grid. If the grid rotates <b>{desc}</b>, where does it land?",
        "opts": opts, "ans": ans,
        "exp": f"The net movement wraps around the outer corners, shifting the position to <b>{ans}</b>."
    }

def gen_pattern(level):
    words = ["MIND", "FAST", "GRID", "PEAK", "BRAIN", "SHARP", "THINK", "SOLVE", "AGILE"]
    word = random.choice(words)
    shift_mag = random.randint(1, level + 1)
    direction = random.choice([1, -1]) if level > 2 else 1
    shift = shift_mag * direction
    def shift_word(w, s): return ''.join(chr((ord(c) - 65 + s) % 26 + 65) for c in w)
    ans = shift_word(word, shift)
    opts = list(set([ans, shift_word(word, shift+1), shift_word(word, shift-1), shift_word(word, shift+2)]))
    while len(opts) < 4: opts.append(shift_word(word, shift + random.randint(3,5)))
    random.shuffle(opts)
    dir_text = "forward" if shift > 0 else "backward"
    return {
        "cat": "Pattern", "title": f"Cipher Shift (Level {level})",
        "q": f"Rule: DATA ➔ {shift_word('DATA', shift)}<br>Target: {word} ➔ ?",
        "opts": opts, "ans": ans,
        "exp": f"The cipher shifts every letter {dir_text} by <b>{abs(shift)}</b>. Applying this to {word} gives <b>{ans}</b>."
    }

def gen_logic(level):
    logic_pool = [
        {"items": ["Ostrich", "Emu", "Penguin", "Eagle"], "odd": "Eagle", "exp": "All others are flightless birds."},
        {"items": ["Mercury", "Venus", "Mars", "Jupiter"], "odd": "Jupiter", "exp": "Jupiter is a gas giant; the rest are terrestrial."},
        {"items": ["Square", "Circle", "Triangle", "Cube"], "odd": "Cube", "exp": "Cube is 3D; all others are 2D shapes."},
        {"items": ["Copper", "Silver", "Gold", "Iron"], "odd": "Iron", "exp": "Copper, Silver, and Gold are coinage metals. Iron is not."},
        {"items": ["Python", "Java", "C++", "HTML"], "odd": "HTML", "exp": "HTML is a markup language, not a programming language."}
    ]
    d = random.choice(logic_pool)
    opts = d["items"].copy()
    random.shuffle(opts)
    return {
        "cat": "Logic", "title": f"Odd One Out (Level {level})",
        "q": f"Identify the ODD one out in this set: {', '.join(d['items'])}",
        "opts": opts, "ans": d["odd"],
        "exp": f"<b>{d['odd']}</b> is the odd one out. Reason: {d['exp']}"
    }

def gen_math(level):
    a = random.randint(5 + level*2, 12 + level*3)
    b = random.randint(5 + level, 10 + level*2)
    c = random.randint(10 + level*2, 30 + level*5)
    ans = (a * b) - c
    opts = [ans, ans+10, ans-10, ans+random.randint(2,8)]
    random.shuffle(opts)
    return {
        "cat": "Math", "title": f"Speed Number Sense (Level {level})",
        "q": f"Calculate mentally: ({a} × {b}) - {c}",
        "opts": opts, "ans": ans,
        "exp": f"First multiply: {a} × {b} = {a*b}. Then subtract: {a*b} - {c} = <b>{ans}</b>."
    }

# --- LOGIC CONTROLLERS ---
def start_workout(specific_category=None):
    st.session_state.session_q = []
    used_questions = set() 
    
    for level in range(1, 6):
        while True:
            if specific_category == "Memory": q = gen_memory(level)
            elif specific_category == "Spatial": q = gen_spatial(level)
            elif specific_category == "Pattern": q = gen_pattern(level)
            elif specific_category == "Logic": q = gen_logic(level)
            elif specific_category == "Math": q = gen_math(level)
            else:
                generators = [gen_memory, gen_spatial, gen_pattern, gen_logic, gen_math]
                q = random.choice(generators)(level)
                
            if q["q"] not in used_questions:
                used_questions.add(q["q"])
                st.session_state.session_q.append(q)
                break
                
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
        stats['xp'] += 20 + (st.session_state.q_idx * 5) 
        stats['cat'][q['cat']]['c'] += 1
        if stats['streak'] > stats['best_streak']: stats['best_streak'] = stats['streak']
        st.session_state.feedback_html = f"<h3 style='color:#34d399'>Correct!</h3>⏱️ Time: {time_taken}s<br><br>{q['exp']}"
    else:
        stats['streak'] = 0
        st.session_state.feedback_html = f"<h3 style='color:#f87171'>Incorrect</h3>⏱️ Time: {time_taken}s<br><br>Correct Answer: <b>{q['ans']}</b><br><br>{q['exp']}"

    # --- AUTOMATIC BACKGROUND SAVE TRIGGER ---
    st.session_state.all_profiles[st.session_state.username] = st.session_state.stats
    save_cloud_db(st.session_state.all_profiles)

def next_question():
    st.session_state.q_idx += 1
    st.session_state.answered = False
    if st.session_state.q_idx >= len(st.session_state.session_q):
        st.session_state.view = 'results'
    else:
        st.session_state.q_start_time = time.time()


# --- VIEWS ROUTING ---
if st.session_state.view == 'login':
    st.markdown("<center><h1 style='color:white; margin-top:10vh;'>🧠 CogniSharp Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; text-align:center;'>Enter a unique username to access your profile.</p></center>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        user_input = st.text_input("Username:", placeholder="e.g. Vinay")
        if st.button("Access Mind Gym", type="primary", use_container_width=True):
            if user_input.strip():
                with st.spinner("Syncing with cloud database..."):
                    st.session_state.username = user_input.strip()
                    st.session_state.all_profiles = load_cloud_db()
                    
                    if st.session_state.username in st.session_state.all_profiles:
                        st.session_state.stats = st.session_state.all_profiles[st.session_state.username]
                    else:
                        st.session_state.stats = {
                            'xp': 0, 'streak': 0, 'best_streak': 0, 'total_q': 0, 'total_correct': 0,
                            'cat': {'Memory': {'c': 0, 't': 0}, 'Spatial': {'c': 0, 't': 0}, 'Pattern': {'c': 0, 't': 0}, 'Logic': {'c': 0, 't': 0}, 'Math': {'c': 0, 't': 0}}
                        }
                st.session_state.view = 'dashboard'
                st.rerun()
            else:
                st.warning("Please enter a username.")

elif st.session_state.view == 'dashboard':
    acc = int((st.session_state.stats['total_correct'] / st.session_state.stats['total_q']) * 100) if st.session_state.stats['total_q'] > 0 else 0
    st.markdown(f"""
    <div class='stats-bar'>
        <span style='color:#818cf8'>👤 {st.session_state.username}</span>
        <span style='color:#fbbf24'>🔥 Streak: {st.session_state.stats['streak']}</span>
        <span style='color:#a78bfa'>⚡ XP: {st.session_state.stats['xp']}</span>
        <span style='color:#34d399'>🎯 Accuracy: {acc}%</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("▶ Start Mixed Quick Workout", on_click=start_workout, args=(None,))
    
    st.markdown("<br><h2 style='color: white;'>Target Specific Cognitive Domains</h2>", unsafe_allow_html=True)
    
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1: st.button("🔢 Working Memory\n\nSequential Math Chains", on_click=start_workout, args=("Memory",))
    with r1c2: st.button("🌀 Spatial Reasoning\n\nGrid Rotation & Orientation", on_click=start_workout, args=("Spatial",))
    with r1c3: st.button("🔐 Pattern Decoding\n\nCipher & Pattern Shifts", on_click=start_workout, args=("Pattern",))
    
    st.write("")
    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1: st.button("⚖️ Deductive Logic\n\nSemantic Categorical Matrices", on_click=start_workout, args=("Logic",))
    with r2c2: st.button("⚡ Mental Speed\n\nSpeed Number Sense", on_click=start_workout, args=("Math",))
    with r2c3: st.button("📊 View Cognitive Analytics\n\nProfile & Training Logs", on_click=lambda: st.session_state.update(view='analytics'))

elif st.session_state.view == 'game':
    q = st.session_state.session_q[st.session_state.q_idx]
    st.markdown(f"<p style='color:#818cf8; font-weight:bold; margin:0;'>{q['cat'].upper()} • Question {st.session_state.q_idx + 1} of 5</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:white; margin-top:0;'>{q['title']}</h2>", unsafe_allow_html=True)
    st.progress((st.session_state.q_idx) / 5)
    st.markdown(f"<h3 style='color:#e2e8f0; font-weight:400;'>{q['q']}</h3>", unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns(2)
    opts = q['opts']
    
    if not st.session_state.answered:
        for i, opt in enumerate(opts):
            col = c1 if i % 2 == 0 else c2
            col.button(str(opt), key=f"ans_{i}", on_click=check_answer, args=(opt,))
    else:
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
    cat_stats = st.session_state.stats['cat']
    radar_vals = []
    labels = ['Memory', 'Spatial', 'Pattern', 'Logic', 'Math']
    for label in labels:
        t = cat_stats[label]['t']
        radar_vals.append(int((cat_stats[label]['c'] / t) * 100) if t > 0 else 0)
        
    radar_vals.append(radar_vals[0])
    plot_labels = labels + [labels[0]]
    
    with sc1:
        st.markdown("### Domain Proficiency")
        fig = go.Figure(data=go.Scatterpolar(r=radar_vals, theta=plot_labels, fill='toself', line_color='#818cf8', fillcolor='rgba(129, 140, 248, 0.3)'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='#334155', tickfont=dict(color='#94a3b8')), angularaxis=dict(gridcolor='#334155', tickfont=dict(color='white'))), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
        
    with sc2:
        st.markdown("### Lifetime Metrics")
        acc = int((st.session_state.stats['total_correct'] / st.session_state.stats['total_q']) * 100) if st.session_state.stats['total_q'] > 0 else 0
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
