import streamlit as st
from groq import Groq
import time
import os
from dotenv import load_dotenv

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Student Success Roadmap",
    page_icon="🎓",
    layout="wide"
)

# =========================================================
# GROQ API KEY (SILENT & SECURE LOGIC)
# =========================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")

# Safe load to catch and correct Windows encoding discrepancies silently
try:
    load_dotenv(dotenv_path=env_path)
except UnicodeDecodeError:
    if os.path.exists(env_path):
        for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
            try:
                with open(env_path, 'r', encoding=enc) as f:
                    for line in f:
                        if "GROQ_API_KEY" in line and "=" in line:
                            key_val = line.split("=")[1].strip()
                            os.environ["GROQ_API_KEY"] = key_val.replace('"', '').replace("'", "")
                break
            except Exception:
                continue

API_KEY = ""

# 1. Look in Streamlit secrets
try:
    if "GROQ_API_KEY" in st.secrets:
        API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# 2. Look in local environment variables
if not API_KEY:
    API_KEY = os.environ.get("GROQ_API_KEY", "")

# 3. Final structural assignment
client = Groq(api_key=API_KEY if API_KEY else "MISSING_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"

# =========================================================
# SESSION STATE INITIALIZATION (PREVENTS ALL KEYERRORS)
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "home"
if "courses" not in st.session_state:
    st.session_state.courses = []
if "uni" not in st.session_state:
    st.session_state.uni = ""
if "program" not in st.session_state:
    st.session_state.program = ""
if "roadmap" not in st.session_state:
    st.session_state.roadmap = []
if "ossd_grades" not in st.session_state:
    st.session_state.ossd_grades = {}
if "nd_stream" not in st.session_state:
    st.session_state.nd_stream = None
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "active_sprint_minutes" not in st.session_state:
    st.session_state["active_sprint_minutes"] = 25

# =========================================================
# ACADEMIC STRUCTURES
# =========================================================
IB_GROUPS = {
    "Group 1: Language & Literature": [
        "English A: Literature SL", 
        "English A: Literature HL", 
        "English A: Language & Literature SL", 
        "English A: Language & Literature HL"
    ],
    "Group 2: Language Acquisition": [
        "Language B SL", 
        "Language B HL", 
        "Ab Initio SL", 
        "Classical Languages SL",
        "Spanish B SL",
        "Spanish B HL",
        "French B SL",
        "French B HL"
    ],
    "Group 3: Individuals & Societies": [
        "Economics SL", 
        "Economics HL", 
        "Business Management SL", 
        "Business Management HL", 
        "History SL", 
        "History HL", 
        "Psychology SL", 
        "Psychology HL", 
        "Geography SL", 
        "Geography HL",
        "Global Politics SL",
        "Global Politics HL"
    ],
    "Group 4: Sciences": [
        "Biology SL", 
        "Biology HL", 
        "Chemistry SL", 
        "Chemistry HL", 
        "Physics SL", 
        "Physics HL", 
        "Computer Science SL", 
        "Computer Science HL",
        "Environmental Systems and Societies SL"
    ],
    "Group 5: Mathematics": [
        "Math AA SL", 
        "Math AA HL", 
        "Math AI SL", 
        "Math AI HL"
    ],
    "Group 6: The Arts": [
        "Visual Arts SL", 
        "Visual Arts HL", 
        "Music SL", 
        "Music HL", 
        "Theatre SL", 
        "Theatre HL",
        "Film SL",
        "Film HL"
    ]
}

OSSD_CATEGORIES = {
    "English & Languages": [
        "ENG4U (Grade 12 English)", 
        "EWC4U (Writer's Craft)", 
        "FSF4U (Core French)",
        "OLC4O (Ontario Secondary School Literacy Course)"
    ],
    "Mathematics": [
        "MHF4U (Advanced Functions)", 
        "MCV4U (Calculus & Vectors)", 
        "MDM4U (Data Management)"
    ],
    "Sciences": [
        "SPH4U (Physics)", 
        "SCH4U (Chemistry)", 
        "SBI4U (Biology)", 
        "ICS4U (Computer Science)"
    ],
    "Social Sciences & Humanities": [
        "CIA4U (Analyzing Current Economic Issues)", 
        "CHY4U (World History)", 
        "HSB4U (Challenge & Change in Society)",
        "HZT4U (Philosophy)",
        "CGW4U (World Issues: A Geographic Analysis)"
    ],
    "Business & Arts": [
        "BAT4M (Financial Accounting)", 
        "BBB4M (International Business)", 
        "AVI4M (Visual Arts)",
        "BOH4M (Business Leadership)",
        "AMU4M (Music)"
    ]
}

# =========================================================
# GROQ HELPERS (WITH ADVANCED RESEARCH PROMPTING)
# =========================================================
def call_ai(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def generate_ai_report(university, program, courses, stream_type="IB"):
    prompt = f"""
You are an expert admissions advisor for global universities, specializing in Canadian and international metrics.
Student Academic Stream: {stream_type}
Student Profile/Courses: {courses}
Target University: {university}
Target Program: {program}

Generate a FULL admissions breakdown:
1. Exact admission average range required for OSSD (in percentages) or IB (total points out of 45) to be competitive.
2. Competitiveness level and the EXACT estimated yearly intake. Cross-reference real-time historic data for {university} {program} to ensure this number is accurate. If the exact intake is a strict range, provide it (e.g., 150-200 seats). Do not guess.
3. For EACH of the student's courses: Assess alignment with prerequisites. Crucially, state the SPECIFIC minimum grade, percentage, or IB component score (e.g., IB Grade 6 or 7, or 93%+) the student needs in that exact course to have a competitive advantage for {program} at {university}.
4. EC roadmap WITH actionable external clickable web resource links formatted in clean markdown (e.g., [GitHub](https://github.com), [Kaggle](https://www.kaggle.com), [CEMC Math Contests](https://www.cemc.uwaterloo.ca), etc.)
5. Weakness analysis (explicitly highlighting if a course level like SL vs HL doesn't meet the requirement).
6. Program advice.
"""
    return call_ai(prompt)

def generate_roadmap(university, program, courses):
    prompt = f"""
Create a step-by-step admission roadmap milestone progression for a student targeting university.
University: {university}
Program: {program}
Courses: {courses}

Rules:
- Give exactly 6 to 8 concise milestone items.
- CRITICAL: For EVERY single milestone item, you MUST include a context-appropriate, highly relevant clickable markdown web link to help the student execute that task. Examples:
  - If recommending programming ECs, provide: [GitHub Platform](https://github.com) or [Kaggle Competitions](https://www.kaggle.com)
  - If recommending math preparation, provide: [Waterloo CEMC Contests](https://www.cemc.uwaterloo.ca)
  - If recommending general university research, provide: [OUAC Info Portal](https://www.ontariouniversitiesinfo.ca)
  - If recommending science activities, provide: [Zooniverse Research Projects](https://www.zooniverse.org)
- Ensure every milestone contains a functional link matching the template: [Anchor Text](https://url-address.com)
- Start each milestone directly with the text without using bullets, numbers, or asterisks.
"""
    text = call_ai(prompt)
    return [line.replace("*", "").replace("-", "").strip() for line in text.split("\n") if line.strip() and not line.lower().startswith("checkpoint")]

def generate_autism_roadmap(profile_data):
    prompt = f"""
You are an expert neurodivergent task strategist and behavioral analyst (BCBA).
Create a structured, predictable, step-by-step executive roadmap for an autistic student based on this profile configuration:
{profile_data}

Rules:
- Provide exactly 7 clear, actionable milestones.
- CRITICAL: Provide an actionable markdown hyperlinked web resource for every step (e.g., [Google Calendar Integration](https://calendar.google.com), [PomoFocus Timer System](https://pomofocus.io), [Trello Workflow Visualizer](https://trello.com)).
- CRITICAL TIMELINE FORMATTING:
  - If the mode is "Immediate Task Execution Support", break the task down into immediate microscopic physical steps to clear task initiation blockages (e.g., Step 1: Stand up and walk to sink). Do NOT mention weeks or long-term schedules.
  - If the mode is "Long-Term Skill Acquisition & Teaching", break the roadmap down into progressive instructional phases across days or weeks (e.g., Phase 1: Overcoming sensory texture resistance).
- Keep text highly literal, clear, and explicit. Avoid vague or figurative language.
- Do not use asterisks, numbers, or bullet prefixes.
"""
    text = call_ai(prompt)
    return [line.replace("*", "").replace("-", "").strip() for line in text.split("\n") if line.strip() and not line.lower().startswith("checkpoint")]

def generate_adhd_roadmap(profile_data):
    prompt = f"""
You are an expert ADHD productivity coach and behavioral designer.
Create a high-stimulation, dopamine-optimized, gamified task execution framework based on this profile configuration:
{profile_data}

Rules:
- Provide exactly 7 clear, actionable wins or levels.
- CRITICAL: Provide an actionable markdown hyperlinked tool, site, or game link for every single level (e.g., [Habitica Gamified Task Tracking](https://habitica.com), [Forest App Deep Work Optimization](https://forestapp.cc), [Brain.fm Focus Tracks](https://brain.fm)).
- CRITICAL TIMELINE FORMATTING:
  - If the mode is "Immediate Task Execution Support", create ultra-low friction micro-steps to defeat executive dysfunction instantly (e.g., Step 1: Put on background tracks). Keep focus solely on initiation right now.
  - If the mode is "Long-Term Skill Acquisition & Teaching", construct an interactive tracking loop with built-in novelty buffers over days or weeks to guard against boredom.
- Keep text motivating, punchy, direct, and structured. 
- Do not use asterisks, numbers, or bullet prefixes.
"""
    text = call_ai(prompt)
    return [line.replace("*", "").replace("-", "").strip() for line in text.split("\n") if line.strip() and not line.lower().startswith("checkpoint")]

def generate_ia_feedback(subject, rq, strategy):
    prompt = f"""
You are an official International Baccalaureate (IB) Senior Examiner and Academic Advisor.
Analyze the following student's Internal Assessment (IA) outline/draft parameters:
- **IB Course Subject**: {subject}
- **Proposed Research Question (RQ)**: {rq}
- **Planned Methodology / Content Draft Summary**: {strategy}

Evaluate this work strictly against the official 4-tier IB IA assessment rubric matrix:
1. **Criterion A: Personal Engagement & Exploration** (Maximum 4 Points) - Assess the clarity, safety, ethical boundaries, and uniqueness of the focus.
2. **Criterion B: Analysis** (Maximum 6 Points) - Assess if the mathematical framework, raw data collection layout, or text citation choice supports deep academic parsing.
3. **Criterion C: Evaluation** (Maximum 6 Points) - Assess the discussion of gaps, background uncertainties, modifications, and experimental or historical limitations.
4. **Criterion D: Communication** (Maximum 4 Points) - Assess overall precision, structural flow, bibliography rules, and vocabulary.

Provide a comprehensive structural audit. Break down explicit structural gaps, recommend highly targeted optimizations to maximize the score, and assign an estimated holistic predicted score range out of 24.
"""
    return call_ai(prompt)

# =========================================================
# UI HEADER
# =========================================================
st.markdown("""
<div style='text-align:center;padding:30px;background:#0f172a;border-radius:20px;margin-bottom:25px;'>
<h1 style='color:white;margin:0;'>🎓 Student Success Roadmap</h1>
<p style='color:#cbd5e1;margin:5px 0 0 0;'>AI Admissions + Academic Planning System</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# HOME PAGE
# =========================================================
if st.session_state.page == "home":
    col1, col2 = st.columns(2)
    with col1:
        st.info("📊 Create standard university admission timelines, evaluate competitive percentage requirements, or run academic audits.")
        if st.button("Standard Stream", use_container_width=True):
            st.session_state.page = "standard"
            st.rerun()
    with col2:
        st.info("🧠 Build executive performance roadmaps optimized for task-initiation blockages, ADHD pacing, or predictable autism structures.")
        if st.button("Neurodivergent Portal", use_container_width=True):
            st.session_state.page = "neuro"
            st.rerun()

# =========================================================
# STANDARD STREAM SELECTION
# =========================================================
elif st.session_state.page == "standard":
    st.title("📚 Standard Stream")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("International Baccalaureate (IB)", use_container_width=True):
            st.session_state.page = "ib"
            st.rerun()
    with col2:
        if st.button("Mainstream OSSD Track", use_container_width=True):
            st.session_state.page = "ossd"
            st.rerun()

    if st.button("⬅ Back", key="back_standard"):
        st.session_state.page = "home"
        st.rerun()

# =========================================================
# NEURODIVERGENT PORTAL
# =========================================================
elif st.session_state.page == "neuro":
    st.title("🧠 Neurodivergent Focus Portal")
    
    if st.session_state.nd_stream is None:
        st.subheader("Select your preferred focus optimization stream:")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚡ ADHD Pacing Track\n\nOptimized with high-stimulation milestones, dopamine-reward checks, and flexibility tools.", use_container_width=True):
                st.session_state.nd_stream = "ADHD"
                st.rerun()
        with col2:
            if st.button("🧩 Autism Structured Track\n\nOptimized with clear predictability systems, explicit step-by-step detail formatting, and routine tracking.", use_container_width=True):
                st.session_state.nd_stream = "Autism"
                st.rerun()
                
        st.write("---")
        if st.button("⬅ Back to Main Menu", key="back_neuro_landing"):
            st.session_state.page = "home"
            st.rerun()
            
    # ⚡ ADHD PACING WORKFLOW
    elif st.session_state.nd_stream == "ADHD":
        st.subheader("⚡ ADHD Dopamine-Optimized Track Builder")
        is_academic_mode = st.toggle("🏫 Toggle Academic Target Framework Tracking", value=True)
        
        curriculum = "N/A - Non-Academic"
        target_uni = ""
        target_program = ""
        selected_nd_courses = []
        personal_goal = ""
        task_timeline_type = "N/A"
        
        if is_academic_mode:
            st.markdown("<div style='background-color:#1e293b; padding:20px; border-radius:10px; margin: 15px 0; border: 1px solid #334155;'>", unsafe_allow_html=True)
            st.markdown("#### 🎓 ADHD-Friendly Academic Settings Selection")
            curriculum = st.selectbox("Select your track curriculum framework:", ["Ontario OSSD Track", "International Baccalaureate (IB) Track"], key="adhd_curriculum_select")
            
            if curriculum == "International Baccalaureate (IB) Track":
                st.info("💡 Working on an Internal Assessment? You can launch the interactive checker tool directly:")
                if st.button("🔍 Go to IB IA Review Workspace", key="adhd_ia_shortcut_btn"):
                    st.session_state.page = "ib_ia_workspace"
                    st.rerun()
            
            target_uni = st.text_input("Enter Target University System", placeholder="e.g. University of Waterloo", key="adhd_target_uni")
            target_program = st.text_input("Enter Target Program / Major Focus", placeholder="e.g. Software Engineering", key="adhd_target_program")
            
            if curriculum == "Ontario OSSD Track":
                for category, courses in OSSD_CATEGORIES.items():
                    st.markdown(f"### 📁 **{category}**")
                    chosen = st.multiselect(f"Select from {category}", courses, label_visibility="collapsed", key=f"adhd_ossd_{category}")
                    selected_nd_courses.extend(chosen)
                    for course in chosen:
                        if course not in st.session_state.ossd_grades:
                            st.session_state.ossd_grades[course] = 85
                        st.session_state.ossd_grades[course] = st.slider(f"Projected Grade for {course}", 50, 100, int(st.session_state.ossd_grades[course]), key=f"adhd_slide_{course}")
            elif curriculum == "International Baccalaureate (IB) Track":
                for group, subjects in IB_GROUPS.items():
                    st.markdown(f"### 🌍 **{group}**")
                    chosen = st.multiselect(f"Select from {group}", subjects, label_visibility="collapsed", key=f"adhd_ib_{group}")
                    selected_nd_courses.extend(chosen)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color:#1e2e3b; padding:20px; border-radius:10px; margin: 15px 0; border: 1px solid #2b3e50;'>", unsafe_allow_html=True)
            st.markdown("#### 🛠️ Personal Development & Routine Goal Space")
            task_timeline_type = st.selectbox("Select Intervention Strategy Type:", ["⚡ Immediate Task Execution Support (Child knows how, but struggles to initiate right now)", "📅 Long-Term Skill Acquisition & Teaching (Child is systematically learning a new lifelong habit)"], key="adhd_task_type")
            personal_goal = st.text_area("What specific personal milestone or daily skill task execution matrix are we organizing?", placeholder="e.g., Clean out study desk space, build personal profile web portfolio, organize math textbook summary sheets", key="adhd_personal_goal")
            st.markdown("</div>", unsafe_allow_html=True)

        with st.form("adhd_behavioral_scaffolding_form"):
            st.markdown("##### 🛠️ Timer Setup & Parameters")
            custom_minutes = st.number_input("Set Custom Workspace Sprint Duration (Minutes):", min_value=1, max_value=180, value=25, key="adhd_timer_input")
            
            age = st.number_input("Age / Birth Year Context", min_value=10, max_value=40, value=17, key="adhd_age")
            support_level = st.select_slider("Select structure framework:", options=["Level 1 (Independent Scaffolding)", "Level 2 (Moderate Support)", "Level 3 (Substantial Support Breakdown)"], key="adhd_support_level")
            behaviors = st.multiselect("What behavioral friction parameters routinely interrupt your workflow?", ["Task Initiation (Getting started)", "Hyperfocus Burnout", "Time Blindness / Missing Checkpoints", "Distraction Management Fatigue"], key="adhd_behaviors")
            reinforcements = st.multiselect("Select your highest-value reinforcement mechanics:", ["Dopamine-pairing (Music/Gamified Trackers)", "Novelty/Variety Shifts", "Token economy tracking (Visual meters)", "Pacing/Downtime recovery buffers"], key="adhd_reinforcements")
            barriers = st.text_area("Are there specific medical, environmental, or social barriers? (Optional)", placeholder="e.g., Sensory sounds from adjacent rooms, screen distraction loops", key="adhd_barriers")
            
            submit_profile = st.form_submit_button("Generate Curated ADHD Roadmap 🛣️")
            
            if submit_profile:
                compiled_courses = [f"{c} ({st.session_state.ossd_grades.get(c, 85)}%)" for c in selected_nd_courses] if "OSSD" in curriculum else selected_nd_courses
                st.session_state.courses = compiled_courses
                
                profile_summary = {"Age": age, "Track Mode": is_academic_mode, "Goal": personal_goal if not is_academic_mode else f"{target_uni} - {target_program}", "Curriculum": curriculum, "Courses": compiled_courses, "Support": support_level, "Behaviors": behaviors, "TimerDuration": custom_minutes}
                
                generated_steps = generate_adhd_roadmap(str(profile_summary))
                st.session_state.roadmap = generated_steps
                st.session_state.uni = target_uni if is_academic_mode else "Personal Focus Track"
                st.session_state.program = target_program if is_academic_mode else "Routine Task Framework"
                st.session_state["active_sprint_minutes"] = custom_minutes
                st.session_state.page = "roadmap"
                st.rerun()

        if is_academic_mode and selected_nd_courses and target_uni and target_program:
            if st.button("Generate Complete AI Admissions Vulnerability & Report Breakdown", key="adhd_report_btn"):
                with st.spinner("Analyzing metrics and requirements..."):
                    stream_code = "OSSD" if "OSSD" in curriculum else "IB"
                    report = generate_ai_report(target_uni, target_program, st.session_state.courses, stream_code)
                    st.markdown("## 📊 Comprehensive Admissions Audit Report")
                    st.write(report)

        if st.button("⬅ Change Stream / Go Back", key="back_from_adhd_form"):
            st.session_state.nd_stream = None
            st.rerun()

    # 🧩 AUTISM STRUCTURED WORKFLOW
    elif st.session_state.nd_stream == "Autism":
        st.subheader("🧩 Autism Structured Track Builder")
        is_academic_mode = st.toggle("🏫 Toggle Academic Target Framework Tracking", value=True, key="autism_academic_toggle")
        
        curriculum = "N/A - Non-Academic"
        target_uni = ""
        target_program = ""
        selected_nd_courses = []
        personal_goal = ""
        task_timeline_type = "N/A"
        
        if is_academic_mode:
            st.markdown("<div style='background-color:#1e293b; padding:20px; border-radius:10px; margin: 15px 0; border: 1px solid #334155;'>", unsafe_allow_html=True)
            st.markdown("#### 🎓 Autism-Friendly Academic Settings Selection")
            curriculum = st.selectbox("Select your track curriculum framework:", ["Ontario OSSD Track", "International Baccalaureate (IB) Track"], key="autism_curriculum_select")
            
            if curriculum == "International Baccalaureate (IB) Track":
                st.info("💡 Working on an Internal Assessment? You can launch the interactive checker tool directly:")
                if st.button("🔍 Go to IB IA Review Workspace", key="autism_ia_shortcut_btn"):
                    st.session_state.page = "ib_ia_workspace"
                    st.rerun()
                    
            target_uni = st.text_input("Enter Target University System", placeholder="e.g. University of Waterloo", key="autism_target_uni")
            target_program = st.text_input("Enter Target Program / Major Focus", placeholder="e.g. Software Engineering", key="autism_target_program")
            
            if curriculum == "Ontario OSSD Track":
                for category, courses in OSSD_CATEGORIES.items():
                    st.markdown(f"### 📁 **{category}**")
                    chosen = st.multiselect(f"Select from {category}", courses, label_visibility="collapsed", key=f"autism_ossd_{category}")
                    selected_nd_courses.extend(chosen)
                    for course in chosen:
                        if course not in st.session_state.ossd_grades:
                            st.session_state.ossd_grades[course] = 85
                        st.session_state.ossd_grades[course] = st.slider(f"Projected Grade for {course}", 50, 100, int(st.session_state.ossd_grades[course]), key=f"autism_slide_{course}")
            elif curriculum == "International Baccalaureate (IB) Track":
                for group, subjects in IB_GROUPS.items():
                    st.markdown(f"### 🌍 **{group}**")
                    chosen = st.multiselect(f"Select from {group}", subjects, label_visibility="collapsed", key=f"autism_ib_{group}")
                    selected_nd_courses.extend(chosen)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color:#1e2e3b; padding:20px; border-radius:10px; margin: 15px 0; border: 1px solid #2b3e50;'>", unsafe_allow_html=True)
            st.markdown("#### 🛠️ Personal Development & Routine Goal Space")
            task_timeline_type = st.selectbox("Select Intervention Strategy Type:", ["⚡ Immediate Task Execution Support", "📅 Long-Term Skill Acquisition & Teaching"], key="autism_task_type")
            personal_goal = st.text_area("What specific personal milestone or daily skill task execution matrix are we organizing?", placeholder="e.g., Set up clean work notebook hierarchy, step-by-step reading routine execution", key="autism_personal_goal")
            st.markdown("</div>", unsafe_allow_html=True)

        with st.form("autism_behavioral_scaffolding_form"):
            st.markdown("##### 🛠️ Timer Setup & Parameters")
            custom_minutes = st.number_input("Set Custom Workspace Sprint Duration (Minutes):", min_value=1, max_value=180, value=30, key="autism_timer_input")

            age = st.number_input("Age / Birth Year Context", min_value=10, max_value=40, value=17, key="autism_age")
            support_level = st.select_slider("Select structure framework:", options=["Level 1 (Independent Scaffolding)", "Level 2 (Moderate Visual Support)", "Level 3 (Substantial Structural Breakdown)"], key="autism_support_level")
            behaviors = st.multiselect("What behavioral friction parameters routinely interrupt your workflow?", ["Task Initiation (Getting started)", "Rigid Transitions", "Sensory Environmental Fatigue/Overload", "Sustaining Focus"], key="autism_behaviors")
            reinforcements = st.multiselect("Select your highest-value reinforcement mechanics:", ["Earning designated Special Interest intervals", "Token economy tracking (Visual meters)", "Pacing/Downtime recovery buffers"], key="autism_reinforcements")
            barriers = st.text_area("Are there specific medical, environmental, or social barriers? (Optional)", placeholder="e.g., High-frequency fluorescent lighting, unpredictable study room drop-ins", key="autism_barriers")
            
            submit_profile = st.form_submit_button("Generate Curated Autism Roadmap 🛣️")
            
            if submit_profile:
                compiled_courses = [f"{c} ({st.session_state.ossd_grades.get(c, 85)}%)" for c in selected_nd_courses] if "OSSD" in curriculum else selected_nd_courses
                st.session_state.courses = compiled_courses
                
                profile_summary = {"Age": age, "Track Mode": is_academic_mode, "Goal": personal_goal if not is_academic_mode else f"{target_uni} - {target_program}", "Curriculum": curriculum, "Courses": compiled_courses, "Support": support_level, "Behaviors": behaviors, "TimerDuration": custom_minutes}
                
                generated_steps = generate_autism_roadmap(str(profile_summary))
                st.session_state.roadmap = generated_steps
                st.session_state.uni = target_uni if is_academic_mode else "Personal Focus Track"
                st.session_state.program = target_program if is_academic_mode else "Structured Task Plan"
                st.session_state["active_sprint_minutes"] = custom_minutes
                st.session_state.page = "roadmap"
                st.rerun()

        if is_academic_mode and selected_nd_courses and target_uni and target_program:
            if st.button("Generate Complete AI Admissions Vulnerability & Report Breakdown", key="autism_report_btn"):
                with st.spinner("Analyzing metrics and requirements..."):
                    stream_code = "OSSD" if "OSSD" in curriculum else "IB"
                    report = generate_ai_report(target_uni, target_program, st.session_state.courses, stream_code)
                    st.markdown("## 📊 Comprehensive Admissions Audit Report")
                    st.write(report)

        if st.button("⬅ Change Stream / Go Back", key="back_from_autism_form"):
            st.session_state.nd_stream = None
            st.rerun()

# =========================================================
# IB PAGE
# =========================================================
elif st.session_state.page == "ib":
    st.title("📘 IB Course Builder")
    
    st.markdown("<div style='background-color:#1e293b; padding:15px; border-radius:10px; margin-bottom:20px; border:1px dashed #3b82f6;'>", unsafe_allow_html=True)
    st.markdown("### 📝 Need Help Auditing Your Internal Assessments?")
    st.write("Launch the AI-powered assessment review environment to receive instant rubric scoring feedback on your Research Question and methodology plans.")
    if st.button("🔍 Go to IB IA Review Workspace", key="standard_ib_ia_workspace_trigger"):
        st.session_state.page = "ib_ia_workspace"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    selected = []
    for group, subjects in IB_GROUPS.items():
        st.markdown(f"## **{group}**")
        chosen = st.multiselect(f"Select from {group}", subjects, label_visibility="collapsed", key=f"standard_ib_select_{group}")
        selected.extend(chosen)
    st.session_state.courses = selected

    st.divider()
    if selected:
        st.session_state.uni = st.text_input("Enter University", value=st.session_state.uni, placeholder="e.g. University of Waterloo", key="standard_ib_uni")
        st.session_state.program = st.text_input("Enter Program", value=st.session_state.program, placeholder="e.g. Software Engineering", key="standard_ib_program")
        
        st.markdown("##### 🛠️ Set Roadmap Execution Sprint Window")
        standard_ib_mins = st.number_input("Set Workspace Sprint Duration (Minutes):", min_value=1, max_value=180, value=25, key="standard_ib_timer_val")

        if st.session_state.uni and st.session_state.program:
            if st.button("Generate AI Admissions Report", key="standard_ib_report_btn"):
                with st.spinner("AI is analyzing your profile..."):
                    report = generate_ai_report(st.session_state.uni, st.session_state.program, st.session_state.courses, "IB")
                    st.markdown("## 📊 Admissions Report")
                    st.write(report)

            if st.button("Generate Admission Roadmap 🛣️", key="standard_ib_roadmap_btn"):
                with st.spinner("Building roadmap..."):
                    st.session_state.roadmap = generate_roadmap(st.session_state.uni, st.session_state.program, st.session_state.courses)
                    st.session_state["active_sprint_minutes"] = standard_ib_mins
                    st.session_state.page = "roadmap"
                    st.rerun()
    else:
        st.warning("Select IB courses to continue")

    if st.button("⬅ Back", key="back_ib"):
        st.session_state.page = "standard"
        st.rerun()

# =========================================================
# OSSD PAGE
# =========================================================
elif st.session_state.page == "ossd":
    st.title("🏫 Mainstream OSSD Track Builder")
    selected_ossd = []
    for category, courses in OSSD_CATEGORIES.items():
        st.markdown(f"## **{category}**")
        chosen = st.multiselect(f"Select {category}", courses, label_visibility="collapsed", key=f"standard_ossd_select_{category}")
        selected_ossd.extend(chosen)
        for course in chosen:
            if course not in st.session_state.ossd_grades:
                st.session_state.ossd_grades[course] = 85
            st.session_state.ossd_grades[course] = st.slider(f"Current/Projected Grade for {course}", 50, 100, int(st.session_state.ossd_grades[course]), key=f"standard_ossd_slider_{course}")

    st.divider()
    profile_summary = [f"{course} (Grade: {st.session_state.ossd_grades.get(course, 85)}%)" for course in selected_ossd]
    st.session_state.courses = profile_summary

    if len(selected_ossd) >= 1:
        st.session_state.uni = st.text_input("Enter Target University", value=st.session_state.uni, placeholder="e.g. University of Waterloo", key="standard_ossd_uni")
        st.session_state.program = st.text_input("Enter Target Program", value=st.session_state.program, placeholder="e.g. Software Engineering", key="standard_ossd_program")
        
        st.markdown("##### 🛠️ Set Roadmap Execution Sprint Window")
        standard_ossd_mins = st.number_input("Set Workspace Sprint Duration (Minutes):", min_value=1, max_value=180, value=25, key="standard_ossd_timer_val")

        if st.session_state.uni and st.session_state.program:
            if st.button("Generate AI Admissions Report", key="standard_ossd_report_btn"):
                with st.spinner("AI analyzing OSSD averages..."):
                    report = generate_ai_report(st.session_state.uni, st.session_state.program, st.session_state.courses, "OSSD")
                    st.markdown("## 📊 Admissions Report")
                    st.write(report)

            if st.button("Generate Admission Roadmap 🛣️", key="standard_ossd_roadmap_btn"):
                with st.spinner("Building OSSD trajectory roadmap..."):
                    st.session_state.roadmap = generate_roadmap(st.session_state.uni, st.session_state.program, st.session_state.courses)
                    st.session_state["active_sprint_minutes"] = standard_ossd_mins
                    st.session_state.page = "roadmap"
                    st.rerun()
    else:
        st.warning("Please select at least 1 course to begin configuring your OSSD application profile.")

    if st.button("⬅ Back", key="back_ossd"):
        st.session_state.page = "standard"
        st.rerun()

# =========================================================
# ROADMAP PAGE
# =========================================================
elif st.session_state.page == "roadmap":
    st.title("🛣️ Your Personal Success Roadmap")
    st.subheader(f"{st.session_state.uni} ➔ {st.session_state.program}")

    if "active_sprint_minutes" in st.session_state and st.session_state["active_sprint_minutes"] != "N/A":
        st.markdown("<div style='background-color:#0f172a; padding:20px; border-radius:12px; margin-bottom:25px; border: 2px solid #3b82f6;'>", unsafe_allow_html=True)
        st.subheader("⏱️ Live Execution Workspace Sprint Timer")
        sprint_target = int(st.session_state["active_sprint_minutes"])
        st.write(f"This session configuration is locked into a structured **{sprint_target} Minute** execution tracking interval.")
        
        if st.button("🚀 Start Active Workspace Sprint Countdown"):
            timer_box = st.empty()
            progress_bar = st.progress(0.0)
            total_seconds = sprint_target * 60
            
            for elapsed in range(total_seconds):
                remaining_seconds = total_seconds - elapsed
                mins, secs = divmod(remaining_seconds, 60)
                timer_box.metric(label="Time Remaining", value=f"{mins:02d}:{secs:02d}")
                progress_bar.progress((elapsed + 1) / total_seconds)
                time.sleep(1)
                
            st.balloons()
            st.success("🎉 Sprint Complete! Step away from your workspace and activate your downtime recovery buffer intervals now.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <style>
    .checkpoint-card { background: #1e293b; color: white; border: 2px solid #334155; padding: 20px; border-radius: 12px; margin-bottom: 25px; position: relative; width: 85%; margin-left: auto; margin-right: auto; }
    .checkpoint-header { color: #3b82f6; font-size: 18px; font-weight: bold; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.roadmap:
        completed_count = 0
        for i, step in enumerate(st.session_state.roadmap):
            if not step.strip():
                continue
            st.markdown(f"""
            <div class='checkpoint-card'>
                <div class='checkpoint-header'>📍 Step {i+1}</div>
                <p style='margin:0; font-size:15px; color:#f1f5f9;'>{step}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.checkbox("Mark Step as Completed ✔", key=f"roadmap_check_{i}"):
                completed_count += 1
        
        st.divider()
        st.subheader("🎒 Overall Task Progress")
        total_steps = len([s for s in st.session_state.roadmap if s.strip()])
        if total_steps > 0:
            progress_pct = completed_count / total_steps
            st.progress(progress_pct)
            st.write(f"You have completed **{completed_count} out of {total_steps}** steps!")
    else:
        st.info("No roadmap data found. Please return and generate a tracking sequence.")

    st.write("---")
    if st.button("⬅ Back to Planner", key="back_from_roadmap"):
        if st.session_state.nd_stream in ["ADHD", "Autism"]:
            st.session_state.page = "neuro"
        else:
            st.session_state.page = "ossd" if "%)" in "".join(st.session_state.courses) else "ib"
        st.rerun()

# =========================================================
# NEW: IB IA REVIEW WORKSPACE PAGE
# =========================================================
elif st.session_state.page == "ib_ia_workspace":
    st.title("📝 Official IB IA Rubric Evaluation Workspace")
    st.write("Submit your research topic, draft methodology, or paragraph excerpts to run an automated check against official IB evaluation criteria criteria.")
    
    ia_subject = st.text_input("Enter IB Subject Course Focus", placeholder="e.g., Chemistry HL, History SL, Mathematics AA HL", key="ia_subject_field")
    ia_rq = st.text_area("Proposed Research Question (RQ)", placeholder="e.g., To what extent does the concentration of sodium chloride affect the corrosion rate of galvanized steel over 48 hours?", key="ia_rq_field")
    ia_strategy = st.text_area("Methodology Overview / Draft Excerpt", placeholder="Describe your variables, background analysis methods, source evaluation tracking, or paste draft materials here...", key="ia_strategy_field")
    
    if st.button("🛡️ Run AI Rubric Audit & Grading Simulator", use_container_width=True):
        if ia_subject and ia_rq and ia_strategy:
            with st.spinner("Auditing against IB Criterion Matrix (Exploration, Analysis, Evaluation, Communication)..."):
                feedback = generate_ia_feedback(ia_subject, ia_rq, ia_strategy)
                st.markdown("### 📊 Comprehensive IA Examiner Feedback Report")
                st.write(feedback)
        else:
            st.warning("Please fill out the subject, research question, and methodology inputs to execute the simulator.")
            
    st.divider()
    if st.button("⬅ Exit IA Workspace", key="exit_ia_workspace_btn"):
        if st.session_state.nd_stream in ["ADHD", "Autism"]:
            st.session_state.page = "neuro"
        else:
            st.session_state.page = "ib"
        st.rerun()

# =========================================================
# GLOBAL PERSISTENT SHARING PANEL
# =========================================================
st.write("---")
st.markdown("""
<div style='text-align:center; padding:15px; background-color:#1e293b; border-radius:12px; border: 1px solid #334155;'>
    <h4 style='margin:0; color:white;'>🔗 Help Your Peers Stay Structured!</h4>
</div>
""", unsafe_allow_html=True)
app_share_url = "https://student-success-roadmap.streamlit.app"
share_message = f"Hey! Try out this AI Student Success Planner: {app_share_url}"
st.text_area("📋 Copy and share:", value=share_message, height=70, key="global_share_text_area")