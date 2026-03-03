import streamlit as st
import random
import requests
import time
import threading
# === Optional TTS (Works Locally, Disabled in Cloud) ===
try:
    import pyttsx3
    tts_enabled = True
except:
    tts_enabled = False
try:
    import speech_recognition as sr
except ImportError:
    sr = None
import json
from datetime import datetime
import base64

# === Configuration ===
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# === Animation HTML Constants ===
BOT_IMAGE_URL = "https://cdn-icons-png.flaticon.com/512/4712/4712042.png"

BOT_HTML_STATIC = f"""
<div class="bot-container">
    <img src="{BOT_IMAGE_URL}" class="bot-img"/>
</div>
"""

BOT_HTML_ECHO = f"""
<div class="bot-container">
    <div class="echo"></div>
    <div class="echo" style="animation-delay:0.5s"></div>
    <div class="echo" style="animation-delay:1s"></div>
    <img src="{BOT_IMAGE_URL}" class="bot-img"/>
</div>
"""

BOT_HTML_GLOW = f"""
<div class="bot-container">
    <div class="glow-listening"></div>
    <img src="{BOT_IMAGE_URL}" class="bot-img"/>
</div>
"""

# === Enhanced Question Bank with Categories (UPDATED to include all user-provided questions) ===
# Note: Questions are categorized based on typical interview practices.
question_bank = {
    "General Interview": {
        "General": [
            "Tell me about yourself.",
            "What are your strengths and weaknesses?",
            "Why should we hire you?",
            "Where do you see yourself in five years?",
            "Why do you want to work here?",
        ],
        "Behavioral": [
            "Describe a challenge you faced and how you handled it.",
            "Can you explain a time you worked in a team?",
            "How do you handle stress and pressure?"
        ]
    },
    "Microsoft": {
        "Technical": [
            "Explain difference between overloading and overriding",
            "Explain the concept of thread safety in multithreading.",
            "What is garbage collection in Java?",
        ],
        "Behavioral": [
            "Describe a time you worked in a diverse team.",
            "How do you prioritize tasks when managing multiple projects?",
        ],
        "General": [
            "What are your strengths and weaknesses?",
            "Tell me about yourself.",
            "Why do you want to work at Microsoft?"
        ]
    },
    "Google": {
        "Technical": [
            "Explain the difference between stack and queue.",
            "What is Big-O notation?",
            "Explain the concept of recursion.",
            "Given a string, check if it is a palindrome using recursion.",
        ],
        "Behavioral": [
            "Describe a challenging bug you fixed in your code.",
        ],
        "General": [
            "Why do you want to work at Google?",
            "What are your strengths and weaknesses?",
            "Tell me about yourself."
        ]
    },
    "Amazon": {
        "Technical": [
            "What is the difference between process and thread?",
        ],
        "Behavioral": [
            "How do you handle tight deadlines?",
            "Describe a project where you used data to make a key decision.",
        ],
        "General": [
            "Why do you want to work for Amazon?",
            "What are your strengths and weaknesses?",
            "Tell me about yourself."
        ]
    },
    "TCS": {
        "Technical": [
            "Tell the logic behind to check if a number is prime.",
            "Difference between C and C++.",
        ],
        "Behavioral": [
            "How do you stay updated with the latest technology trends?",
            "Describe a situation where you had to work under pressure.",
        ],
        "General": [
            "What do you know about TCS and its services?",
            "Why do you want to work at TCS?",
            "What are your strengths and weaknesses?",
            "Tell me about yourself.",
        ]
    },
    "Infosys": {
        "Technical": [
            "What is the difference between for and while loop?",
            "Explain different ways to import modules in Python.",
            "Explain the concept of inheritance in OOP.",
        ],
        "Behavioral": [
            "Describe a time you had to learn a new technology quickly.",
        ],
        "General": [
            "Why do you want to work at Infosys?",
            "What are your strengths and weaknesses?",
            "Tell me about yourself."
        ]
    },
    "Capgemini": {
        "Technical": [
            "What is the difference between a list and a tuple in Python?",
            "What is dynamic memory allocation?",
            "Explain linear search vs binary search.",
            "What are the four pillars of OOP?",
            "Difference between compiler and interpreter.",
        ],
        "General": [
            "Why do you want to work at Capgemini?",
            "What are your strengths and weaknesses?",
            "Tell me about yourself."
        ]
    },
    "Deloitte": {
        "Technical": [
            "What is recursion and give a practical example.",
            "Explain the difference between == and is in Python.",
            "What is a dictionary in Python and how is it implemented internally?",
        ],
        "Behavioral": [
            "Describe a time you had to resolve a conflict within a team.",
        ],
        "General": [
            "What are your strengths and weaknesses?",
            "Tell me about yourself.",
            "Why do you want to work at Deloitte?",
            "What are your career goals?"
        ]
    }
}

# === Difficulty Levels ===
DIFFICULTY_LEVELS = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3
}


# === Session State Initialization ===
def initialize_session_state():
    default_states = {
        "is_speaking": False,
        "interview_log": [],
        "interview_active": False,
        "current_question_index": 0,
        "current_question_text": "",
        "questions_list": [],
        "is_listening": False,
        "final_feedback": "",
        "animation_placeholder": None,
        "question_count": 3,
        "selected_company": list(question_bank.keys())[0],
        "selected_difficulty": "Medium",
        "interview_start_time": None,
        "interview_duration": 0,
        "user_answers": [],
        "current_score": 0,
        "show_transcript": False,
        "interview_history": []
    }

    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# === Animation Functions ===
def set_animation(html_code):
    """Sets the bot animation via the placeholder."""
    if st.session_state.animation_placeholder:
        st.session_state.animation_placeholder.markdown(html_code, unsafe_allow_html=True)


# === Enhanced TTS with Error Handling ===
def tts_process(text):
    """Enhanced TTS with better error handling and voice selection"""
    try:
        engine = pyttsx3.init()

        # Get available voices and select a pleasant one
        voices = engine.getProperty('voices')
        if voices:
            # Prefer female voices for better clarity
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break

        engine.setProperty("rate", 175)
        engine.setProperty('volume', 0.8)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        st.error(f"Text-to-speech error: {e}")


def speak(text):
    st.session_state.is_speaking = True
    st.session_state.is_listening = False

    set_animation(BOT_HTML_ECHO)

    st.markdown(f"<p class='interviewer-speech'>🤖 Interviewer: {text}</p>", unsafe_allow_html=True)

    if tts_enabled:
        speech_thread = threading.Thread(target=tts_process, args=(text,))
        speech_thread.start()
        speech_thread.join()

    st.session_state.is_speaking = False


# === Enhanced Speech Recognition with Multiple Fallbacks ===
def listen():
    if sr is None:
        st.markdown("<p class='warning-text'>SpeechRecognition library is not available.</p>", unsafe_allow_html=True)
        return None

    st.session_state.is_listening = True
    st.session_state.is_speaking = False
    set_animation(BOT_HTML_GLOW)

    r = sr.Recognizer()
    r.pause_threshold = 1.5
    r.energy_threshold = 300

    try:
        with sr.Microphone(sample_rate=16000) as source:
            st.markdown("<p class='listening-indicator'>🎙 Listening... Speak now!</p>", unsafe_allow_html=True)
            r.adjust_for_ambient_noise(source, duration=2)
            audio = r.listen(source, timeout=10, phrase_time_limit=20)

            # Try multiple recognition services as fallback
            try:
                text = r.recognize_google(audio)
            except sr.UnknownValueError:
                try:
                    text = r.recognize_sphinx(audio)  # Offline option
                except:
                    text = None

            if text:
                st.markdown(f"<p class='user-response'>🗣 You said: {text}</p>", unsafe_allow_html=True)
                st.session_state.is_listening = False
                return text
            else:
                st.markdown("<p class='warning-text'>❌ Could not understand your speech. Please try again.</p>",
                            unsafe_allow_html=True)
                return None

    except sr.WaitTimeoutError:
        st.markdown("<p class='warning-text'>⏱ No speech detected within 10 seconds. Try again.</p>",
                    unsafe_allow_html=True)
        return None
    except Exception as e:
        st.markdown(f"<p class='warning-text'>⚙ Error during listening: {e}</p>", unsafe_allow_html=True)
        return None
    finally:
        st.session_state.is_listening = False


# === Real-time Answer Analysis ===
def analyze_answer_quality(question, answer):
    """Provide real-time feedback on answer quality"""
    prompt = f"""
    Analyze this interview Q&A and provide a brief assessment:

    Question: {question}
    Answer: {answer}

    Provide a JSON response with:
    - score (1-10)
    - strengths (array of strings)
    - improvements (array of strings)
    - brief_feedback (one sentence)
    """

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return json.loads(data["choices"][0]["message"]["content"])
        else:
            st.error(f"Groq API Error {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error during analysis: {e}")
    except json.JSONDecodeError as e:
        st.error(f"JSON Decode Error in analysis: {e}")
    except Exception as e:
        st.error(f"Unexpected Error in analysis: {e}")

    return {"score": 6, "strengths": ["Good attempt"], "improvements": ["Could be more detailed"],
            "brief_feedback": "Keep going! (Default feedback used due to API error.)"}


# === Enhanced Question Selection (FIXED) ===
def select_questions(company, count, difficulty):
    """Select exactly 'count' questions with a balanced category distribution."""

    # 1. Flatten all available questions with their category
    available_questions = []
    for category, questions in question_bank[company].items():
        available_questions.extend([(q, category) for q in questions])

    # 2. Handle case where total questions are less than requested count
    if len(available_questions) <= count:
        random.shuffle(available_questions)
        return [q[0] for q in available_questions]

    # 3. Calculate target distribution
    categories = list(question_bank[company].keys())
    num_categories = len(categories)

    # Base number of questions per category
    base_per_cat = count // num_categories
    # The remainder questions to be distributed
    remainder = count % num_categories

    category_counts = {}
    for i, category in enumerate(categories):
        # Base count + 1 for the first 'remainder' categories
        category_counts[category] = base_per_cat + (1 if i < remainder else 0)

    # 4. Select questions based on calculated counts
    selected_questions = []
    unselected_pool = available_questions.copy()

    for category, target_count in category_counts.items():
        # Filter questions for the current category
        category_pool = [q for q in unselected_pool if q[1] == category]

        # Determine how many to actually select from this category
        num_to_select = min(target_count, len(category_pool))

        # Randomly sample and add to selected list
        if num_to_select > 0:
            sample = random.sample(category_pool, num_to_select)
            selected_questions.extend(sample)

            # Remove selected questions from the unselected pool
            for q in sample:
                unselected_pool.remove(q)

    # 5. Final check: Ensure the list is shuffled and contains the correct number of questions
    final_questions = [q[0] for q in selected_questions]
    random.shuffle(final_questions)

    return final_questions[:count]


# === Progress Tracking ===
def calculate_progress():
    total = st.session_state.question_count
    current = st.session_state.current_question_index
    # Use max(1, total) to prevent division by zero if somehow total is 0
    return min(100, int((current / max(1, total)) * 100))


def calculate_current_score():
    if not st.session_state.user_answers:
        return 0
    return sum(answer.get('score', 5) for answer in st.session_state.user_answers) / len(st.session_state.user_answers)


# === Enhanced Feedback Generation ===
def get_final_feedback(interview_log):
    prompt = """You are an expert AI interview coach. Analyze this interview and provide comprehensive feedback:

"""
    for i, entry in enumerate(interview_log, 1):
        prompt += f"Q{i}: {entry['question']}\nA{i}: {entry['answer']}\nAnalysis: {entry.get('analysis', {})}\n\n"

    prompt += """
Provide structured feedback covering:
1. Overall Performance Score (0-10)
2. Technical Knowledge Assessment
3. Communication Skills
4. STAR Method Application (for behavioral questions)
5. Key Strengths (3-4 bullet points)
6. Areas for Improvement (3-4 actionable suggestions)
7. Final Recommendation

Format with clear sections and use emojis for readability."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"⚠ Could not generate detailed feedback. HTTP Error {response.status_code}."
    except Exception as e:
        return f"⚠ Could not generate feedback. Error: {e}"


# === Export Functionality ===
def create_download_link(content, filename, text):
    """Create a download link for interview data"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href


# === Enhanced Interview Logic ===
def run_interview():
    company = st.session_state.selected_company
    num_qs = st.session_state.question_count

    if st.session_state.current_question_index == 0:
        # Initial setup
        st.session_state.questions_list = select_questions(
            company, num_qs, st.session_state.selected_difficulty
        )
        st.session_state.interview_log = []
        st.session_state.user_answers = []
        st.session_state.interview_active = True
        st.session_state.interview_start_time = time.time()

        # Safety check: Update question count if selection was limited by availability
        st.session_state.question_count = len(st.session_state.questions_list)

        speak(
            f"Welcome to your {company}, interview at {st.session_state.selected_difficulty} level. We will cover {st.session_state.question_count} questions. Let's begin!")
        st.session_state.current_question_index = 1
        st.rerun()

    elif st.session_state.current_question_index <= len(st.session_state.questions_list):
        # Display progress
        progress = calculate_progress()
        st.progress(progress / 100)
        st.write(f"Progress: {st.session_state.current_question_index}/{st.session_state.question_count}")

        # Current question
        q_index = st.session_state.current_question_index - 1
        current_q = st.session_state.questions_list[q_index]

        if st.session_state.current_question_text != current_q:
            st.session_state.current_question_text = current_q
            speak(current_q)
            st.rerun()

        # Display question with category
        st.markdown(
            f"<p class='main-question'>Question {st.session_state.current_question_index}: <b>{st.session_state.current_question_text}</b></p>",
            unsafe_allow_html=True
        )

        # Listen for answer
        if not st.session_state.is_speaking and not st.session_state.is_listening:
            time.sleep(3)
            answer = listen()

            if answer:
                # Real-time analysis
                analysis = analyze_answer_quality(current_q, answer)

                st.session_state.interview_log.append({
                    "question": current_q,
                    "answer": answer,
                    "analysis": analysis
                })

                st.session_state.user_answers.append({
                    "question": current_q,
                    "answer": answer,
                    "score": analysis.get("score", 5),
                    "timestamp": datetime.now().isoformat()
                })

                # Show immediate feedback
                with st.expander("📊 Immediate Feedback", expanded=True):
                    st.write(f"*Score:* {analysis.get('score', 'N/A')}/10")
                    st.write(f"*Feedback:* {analysis.get('brief_feedback', 'No feedback available')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("*Strengths:*")
                        for strength in analysis.get('strengths', []):
                            st.write(f"✅ {strength}")
                    with col2:
                        st.write("*Improvements:*")
                        for improvement in analysis.get('improvements', []):
                            st.write(f"💡 {improvement}")

                speak("Thank you for your answer. Let's move to the next question.")
                st.session_state.current_question_index += 1
                st.rerun()
            else:
                # FIX: Ask to try again on recognition failure
                speak("I couldn't quite hear that. Please try answering again.")
                st.rerun()

    else:
        # Interview completion
        if st.session_state.final_feedback == "":
            st.session_state.interview_duration = time.time() - st.session_state.interview_start_time
            speak("Interview completed! Generating your detailed feedback...")

            with st.spinner("Analyzing your performance..."):
                feedback = get_final_feedback(st.session_state.interview_log)
                st.session_state.final_feedback = feedback

            st.balloons()
            st.rerun()
        else:
            # Display comprehensive results
            display_results()


def display_results():
    """Display final results and analytics"""
    st.markdown("## 🎉 Interview Completed!")

    # Overall stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", st.session_state.question_count)
    with col2:
        st.metric("Duration",
                  f"{int(st.session_state.interview_duration // 60)}m {int(st.session_state.interview_duration % 60)}s")
    with col3:
        avg_score = calculate_current_score()
        st.metric("Average Score", f"{avg_score:.1f}/10")

    # Final feedback
    st.markdown("### 📝 Detailed Feedback")
    st.markdown(st.session_state.final_feedback)

    # Enhanced transcript
    with st.expander("📄 Detailed Question-by-Question Analysis", expanded=False):
        for i, entry in enumerate(st.session_state.interview_log, 1):
            st.markdown(f"#### Q{i}: {entry['question']}")
            st.write(f"*Your Answer:* {entry['answer']}")
            analysis = entry.get('analysis', {})
            if analysis:
                st.write(f"*Score:* {analysis.get('score', 'N/A')}/10")
                st.write(f"*Feedback:* {analysis.get('brief_feedback', 'No feedback')}")

    # Export options
    st.markdown("### 💾 Export Results")
    col1, col2 = st.columns(2)

    with col1:
        # Export as text
        export_text = f"Interview Report for {st.session_state.selected_company}\n\n"
        export_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        export_text += f"Difficulty: {st.session_state.selected_difficulty}\n"
        export_text += f"Final Score: {calculate_current_score():.1f}/10\n\n"
        export_text += st.session_state.final_feedback

        st.markdown(create_download_link(
            export_text,
            f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            "📥 Download Text Report"
        ), unsafe_allow_html=True)

    with col2:
        if st.button("🔄 Start New Interview", use_container_width=True):
            # Save to history
            st.session_state.interview_history.append({
                "company": st.session_state.selected_company,
                "date": datetime.now().isoformat(),
                "score": calculate_current_score(),
                "duration": st.session_state.interview_duration,
                "difficulty": st.session_state.selected_difficulty
            })

            # Reset for new interview
            # Use explicit keys to reset instead of relying on del and re-init, which is safer
            st.session_state.interview_active = False
            st.session_state.current_question_index = 0
            st.session_state.current_question_text = ""
            st.session_state.final_feedback = ""
            st.session_state.interview_log = []
            st.session_state.user_answers = []
            st.rerun()


# === Enhanced UI Setup ===
st.set_page_config(
    page_title="🎯 AI Interviewer Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === UI CSS/Styling ===
st.markdown("""
<style>
    /* Background Gradient */
    body, .stApp {
        background-color: #f0f2f6; 
        color: #333333; 
    }
    .stApp {background: linear-gradient(45deg, #00ff8f 10%, #00a1ff 100%);}

    /* Remove default Streamlit boxes/padding */
    .st-emotion-cache-18ni7ap, .st-emotion-cache-1jm6gjm { 
        padding-top: 0; 
    }
    /* Targeted Streamlit Info/Success box removal */
    div.st-emotion-cache-p5m013, div.st-emotion-cache-g9z7n7 { 
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        margin-bottom: 0.5rem;
    }

    /* Main Header Title */
    .gradient-text {
        font-size: 50px;
        font-weight: bold;
        background: linear-gradient(0deg, #ff00d4 5%, #00ddff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Bot Card - Minimalist */
    .bot-card {
        padding: 20px;
        margin-bottom: 30px;
        text-align: center;
        margin-top: 50px; 
    }
    .bot-card h3 {
        color: #fff;
        margin-top: 10px;
        font-size: 1.2rem;
        font-weight: 600;
    }

    /* Interview Question Display */
    .main-question {
        color: #fff;
        font-size: 1.8rem;
        font-weight: 600;
        margin-top: 25px;
        margin-bottom: 25px;
        padding-left: 10px;
        border-left: 5px solid #ff00d4;
    }

    /* CUSTOM DIALOGUE STYLES */
    .interviewer-speech {
        background: rgba(255, 255, 255, 0.1);
        color: #eee;
        padding: 10px 15px;
        border-radius: 8px;
        font-style: italic;
        font-weight: 500;
        margin-bottom: 10px;
    }
    .user-response {
        background: rgba(255, 255, 255, 0.2);
        color: #fff;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .listening-indicator {
        color: #000000;
        font-weight: bold;
        padding: 10px 0;
    }
    .warning-text {
        color: #FFFFFF;
        padding: 10px 0;
    }

    /* Bot Animation Styles */
    .bot-container {position:relative; width:220px; height:220px; margin:auto;}
    .bot-img {position:absolute; width:100%; height:100%; border-radius:50%;
        box-shadow:0 0 10px rgba(0,0,0,0.1); z-index:2;}
    .echo {position:absolute; border:3px solid rgba(255, 255, 255, 0.4); 
        border-radius:50%; left:0; top:0; width:220px; height:220px;
        animation: echoPulse 2s ease-out infinite;}
    @keyframes echoPulse {
        0% {transform:scale(1); opacity:0.9;}
        100% {transform:scale(2.5); opacity:0;}
    }
    .glow-listening {
        position:absolute; border:3px solid rgba(255, 255, 255, 0.6); 
        border-radius:50%; left:0; top:0; width:220px; height:220px;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.8), 0 0 25px rgba(255, 255, 255, 0.6);
        animation: glowPulse 1.5s ease-in-out infinite alternate;
    }
    @keyframes glowPulse {
        0% {transform:scale(1); opacity:0.8; box-shadow: 0 0 15px rgba(255, 255, 255, 0.8), 0 0 25px rgba(255, 255, 255, 0.6);}
        100% {transform:scale(1.05); opacity:1; box-shadow: 0 0 20px rgba(255, 255, 255, 1), 0 0 35px rgba(255, 255, 255, 0.8);}
    }
</style>
""", unsafe_allow_html=True)

# === Main Application ===
st.markdown("<h1 class='gradient-text'> 🤖 Virtual Interviewer Bot</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col2:
    st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
    bot_container = st.container()
    with bot_container:
        if st.session_state.animation_placeholder is None:
            st.session_state.animation_placeholder = st.empty()
            st.session_state.animation_placeholder.markdown(BOT_HTML_STATIC, unsafe_allow_html=True)

        if not st.session_state.is_speaking and not st.session_state.is_listening:
            st.session_state.animation_placeholder.markdown(BOT_HTML_STATIC, unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center;'>AI Interviewer Bot</h3>", unsafe_allow_html=True)

    # Quick stats
    if st.session_state.interview_history:
        st.markdown("### 📈 Recent Performance")
        for history in st.session_state.interview_history[-3:]:  # Show last 3
            st.write(f"{history['company']}: {history['score']:.1f}/10")

    st.markdown("</div>", unsafe_allow_html=True)

with col1:
    if not st.session_state.interview_active:
        # Enhanced setup
        st.markdown(
            "<p style='color:#fff;'>Practice with realistic interviews and get instant AI-powered feedback.</p>",
            unsafe_allow_html=True)

        col_setup1, col_setup2 = st.columns(2)

        with col_setup1:
            st.selectbox(
                "🏢 Select Company",
                options=list(question_bank.keys()),
                key="selected_company"
            )

            st.selectbox(
                "🎯 Difficulty Level",
                options=list(DIFFICULTY_LEVELS.keys()),
                key="selected_difficulty"
            )

        with col_setup2:
            num_available = sum(
                len(questions) for questions in question_bank[st.session_state.selected_company].values())
            st.slider(
                "Number of Questions",
                min_value=1,
                max_value=min(10, num_available),
                value=st.session_state.question_count,
                step=1,
                key="question_count"
            )

            st.info(
                f"ℹ {st.session_state.selected_company} has {num_available} questions across {len(question_bank[st.session_state.selected_company])} categories")

        if st.button("🎬 Start Professional Interview", use_container_width=True, type="primary"):
            st.session_state.interview_active = True
            st.session_state.current_question_index = 0
            st.rerun()

        # Interview tips
        with st.expander("💡 Interview Tips"):
            st.write("""
            - Use the STAR method (Situation, Task, Action, Result) for behavioral questions
            - Speak clearly and at a moderate pace
            - Structure your technical answers logically
            - Practice active listening
            - Ask for clarification if needed
            """)
    else:
        run_interview()