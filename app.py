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
        return {} 

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
if 'timer_enabled' not in st.session_state: st.session_state.timer_enabled = True

# --- PROCEDURAL GENERATORS ---

def gen_statistics(level):
    stat_type = random.choice(["Mean", "Median", "Mode"])
    
    contexts = [
        ("Weekly Ad Revenue", "Day", "Revenue ($)"),
        ("Website Visitors", "Day", "Traffic"),
        ("App Downloads", "Month", "Downloads"),
        ("Store Sales", "Day", "Sales (Rs)")
    ]
    title, x_label, y_label = random.choice(contexts)
    n_items = random.choice([5, 7]) # Odd numbers make Median cleaner
    x_data = [f"{x_label} {i+1}" for i in range(n_items)]
    
    if stat_type == "Mode":
        base_val = random.randint(10 * level, 50 * level)
        data = [random.randint(10 * level, 50 * level) for _ in range(n_items)]
        # Inject the mode so it repeats
        data[0] = base_val
        data[1] = base_val
        if n_items == 7:
            data[2] = base_val
        random.shuffle(data)
        ans = base_val
        
        opts = list(set([ans, ans + random.randint(1,5), ans - random.randint(1,5), random.choice(data)]))
        while len(opts) < 4:
            new_opt = ans + random.randint(6, 15)
            if new_opt not in opts: opts.append(new_opt)
        random.shuffle(opts)
        
        exp = f"<b>Mode:</b> The value that appears most frequently.<br><b>Values:</b> {', '.join(map(str, data))}<br>The number <b>{ans}</b> appears most often."
        q_text = f"Analyze the interactive chart below. Identify the <b>Mode</b> (most frequent value) of the {title}."
        
    elif stat_type == "Median":
        data = [random.randint(10 * level, 50 * level) for _ in range(n_items)]
        sorted_data = sorted(data)
        mid_idx = n_items // 2
        ans = sorted_data[mid_idx]
        
        opts = list(set([ans, sorted_data[0], sorted_data[-1], sorted_data[mid_idx - 1]]))
        while len(opts) < 4:
            new_opt = ans + random.randint(2, 8)
            if new_opt not in opts: opts.append(new_opt)
        random.shuffle(opts)
        
        exp = f"<b>Median:</b> The middle value when arranged in order.<br><b>Original data:</b> {', '.join(map(str, data))}<br><b>Sorted (Ascending):</b> {', '.join(map(str, sorted_data))}<br>The middle value (position {mid_idx + 1}) is <b>{ans}</b>."
        q_text = f"Analyze the interactive chart below. Calculate the <b>Median</b> (middle value) of the {title}."
        
    else: # Mean
        data = [random.randint(10 * level, 50 * level) for _ in range(n_items)]
        ans = round(sum(data) / len(data), 2)
        opts = [ans, round(ans + random.uniform(1.0, 3.0), 2), round(ans - random.uniform(1.0, 3.0), 2), round(sum(data) / (len(data) - 1), 2)]
        random.shuffle(opts)
        
        exp = f"<b>Formula:</b> x̄ = ∑x / N<br><b>Sum (∑x):</b> {' + '.join(map(str, data))} = {sum(data)}<br><b>Observations (N):</b> {len(data)}<br><b>Mean:</b> {sum(data)} ÷ {len(data)} = <b>{ans}</b>"
        q_text = f"Analyze the interactive chart below. Calculate the <b>Arithmetic Mean</b> (average) of the {title}."

    return {
        "cat": "Statistics", "title": f"Data Analytics ({stat_type} - Level {level})",
        "q": q_text,
        "opts": opts, "ans": ans,
        "exp": exp,
        "chart_data": {"x": x_data, "y": data, "title": title, "y_label": y_label}
    }

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

# --- LOGIC CONTROLLERS ---
def start_workout(specific_category=None):
    st.session_state.session_q = []
    used_questions = set() 
    
    for level in range(1, 6):
        while True:
            if specific_category == "Memory": q = gen_memory(level)
            elif specific_category == "Statistics": q = gen_statistics(level)
            else:
                q = random.choice([gen_memory, gen_statistics])(level)
                
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
    if not st.session_state.timer_enabled:
        time_taken = 0 
        
    st.session_state.times.append(time_taken)
    st.session_state.answered = True
    
    q = st.session_state.session_q[st.session_state.q_idx]
    stats = st.session_state.stats
    stats['total_q'] += 1
    
    if q['cat'] not in stats['cat']:
        stats['cat'][q['cat']] = {'c': 0, 't': 0}
        
    stats['cat'][q['cat']]['t'] += 1
    
    if opt == q['ans']:
        stats['total_correct'] += 1
        stats['streak'] += 1
        
        xp_earned = 20 + (st.session_state.q_idx * 5)
        if st.session_state.timer_enabled and time_taken < 15:
            xp_earned += 10 
            
        stats['xp'] += xp_earned
        stats['cat'][q['cat']]['c'] += 1
        if stats['streak'] > stats['best_streak']: stats['best_streak'] = stats['streak']
        
        time_msg = f"⏱️ Time: {time_taken}s (+10 Speed Bonus!)" if st.session_state.timer_enabled and time_taken < 15 else (f"⏱️ Time: {time_taken}s" if st.session_state.timer_enabled else "⏳ Untimed Mode")
        st.session_state.feedback_html = f"<h3 style='color:#34d399'>Correct! (+{xp_earned} XP)</h3>{time_msg}<br><br>{q['exp']}"
    else:
        stats['streak'] = 0
        time_msg = f"⏱️ Time: {time_taken}s" if st.session_state.timer_enabled else "⏳ Untimed Mode"
        st.session_state.feedback_html = f"<h3 style='color:#f87171'>Incorrect</h3>{time_msg}<br><br>Correct Answer: <b>{q['ans']}</b><br><br>{q['exp']}"

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
                            'cat': {'Memory': {'c': 0, 't': 0}, 'Statistics': {'c': 0, 't': 0}}
                        }
                st.session_state.view = 'dashboard'
                st.rerun()

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

    t_col1, t_col2 = st.columns([3, 1])
    with t_col2:
        st.session_state.timer_enabled = st.toggle("⏱️ Enable Speed Timer Mode", value=st.session_state.timer_enabled)

    st.markdown("<br><h2 style='color: white;'>Target Specific Cognitive Domains</h2>", unsafe_allow_html=True)
    
    r1c1, r1c2 = st.columns(2)
    with r1c1: st.button("🔢 Working Memory\n\nSequential Math Chains", on_click=start_workout, args=("Memory",))
    with r1c2: st.button("📊 Business Analytics\n\nMean, Median & Mode", on_click=start_workout, args=("Statistics",))

elif st.session_state.view == 'game':
    q = st.session_state.session_q[st.session_state.q_idx]
    st.markdown(f"<p style='color:#818cf8; font-weight:bold; margin:0;'>{q['cat'].upper()} • Question {st.session_state.q_idx + 1} of 5</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:white; margin-top:0;'>{q['title']}</h2>", unsafe_allow_html=True)
    st.progress((st.session_state.q_idx) / 5)
    
    st.markdown(f"<h3 style='color:#e2e8f0; font-weight:400;'>{q['q']}</h3>", unsafe_allow_html=True)
    
    if "chart_data" in q:
        fig = go.Figure(data=[go.Bar(
            x=q['chart_data']['x'], 
            y=q['chart_data']['y'], 
            marker_color='#818cf8',
            text=q['chart_data']['y'], 
            textposition='outside',
            textfont=dict(color='white', size=14)
        )])
        fig.update_layout(
            title=q['chart_data']['title'],
            yaxis_title=q['chart_data']['y_label'],
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis=dict(range=[0, max(q['chart_data']['y']) * 1.2]) 
        )
        st.plotly_chart(fig, use_container_width=True)
    
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
    st.button("🏠 Main Menu", on_click=lambda: st.session_state.update(view='dashboard'))
