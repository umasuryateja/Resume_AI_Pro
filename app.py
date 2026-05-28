import streamlit as st
import plotly.graph_objects as go
import sys, os, re

sys.path.insert(0, os.path.dirname(__file__))
from src.pdf_reader import extract_text_from_pdf
from src.text_processor import extract_skills
from src.model import load_model, predict_role
from src.ats_feedback import generate_ats_feedback, check_resume_sections
from src.scorer import compute_skill_match, compute_resume_quality, compute_jd_match, compute_final_ats_score

# Sparklines removed for minimal and clean SaaS aesthetics

def get_status_details(lbl, val, has_jd):
    """
    Returns the dot status label and styling color matching the design mock image.
    """
    if lbl in ["ATS Score", "ATS"]:
        if val >= 70:
            return "Excellent", "#10B981"
        elif val >= 45:
            return "Good", "#F59E0B"
        else:
            return "Needs Improvement", "#EF4444"
    elif lbl in ["Role Match", "Role"]:
        if val == 0:
            return "Analysis Pending", "#3B82F6"
        elif val >= 70:
            return "Excellent", "#10B981"
        elif val >= 45:
            return "Good", "#F59E0B"
        else:
            return "Needs Improvement", "#EF4444"
    elif lbl in ["Skills Match", "Skills"]:
        if val >= 70:
            return "Excellent", "#10B981"
        elif val >= 45:
            return "Average", "#F59E0B"
        else:
            return "Critical Gap", "#EF4444"
    elif lbl in ["JD Match", "JD"]:
        if not has_jd:
            return "No JD Provided", "#6B7280"
        elif val >= 70:
            return "Excellent Match", "#10B981"
        elif val >= 45:
            return "Average Match", "#F59E0B"
        else:
            return "Weak Match", "#EF4444"
    elif lbl in ["Quality", "Overall Quality"]:
        if val >= 85:
            return "Excellent", "#10B981"
        elif val >= 55:
            return "Good", "#F59E0B"
        else:
            return "Needs Improvement", "#EF4444"
    return "Insufficient Data", "#3B82F6"

st.set_page_config(page_title="Resume AI Pro", page_icon="🚀", layout="wide")

# ── FUTURISTIC MESH BACKGROUND & TOP NAV ──────────────────────────────────────
st.markdown("""
<div class="mesh-bg">
  <div class="glow-orb orb-1"></div>
  <div class="glow-orb orb-2"></div>
  <div class="glow-orb orb-3"></div>
  <div class="light-streak streak-1"></div>
  <div class="light-streak streak-2"></div>
  <div class="glow-grid"></div>
</div>

<div class="mesh-waves-container">
  <div class="mesh-wave wave-left">
    <svg width="100%" height="100%" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="wave-grad-left" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#3B82F6" stop-opacity="0.5"/>
          <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      <path d="M 0,100 C 100,60 150,140 250,90 C 300,65 350,110 400,80" fill="none" stroke="url(#wave-grad-left)" stroke-width="2.5" stroke-dasharray="3 6"/>
      <path d="M 0,120 C 80,80 170,160 230,110 C 290,60 340,130 400,100" fill="none" stroke="url(#wave-grad-left)" stroke-width="1.5" stroke-dasharray="1 3"/>
      <path d="M 0,140 C 90,100 130,120 210,130 C 280,140 330,90 400,120" fill="none" stroke="url(#wave-grad-left)" stroke-width="1" stroke-dasharray="4 8"/>
    </svg>
  </div>
  <div class="mesh-wave wave-right">
    <svg width="100%" height="100%" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="wave-grad-right" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#8B5CF6" stop-opacity="0.5"/>
          <stop offset="100%" stop-color="#8B5CF6" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      <path d="M 400,100 C 300,60 250,140 150,90 C 100,65 50,110 0,80" fill="none" stroke="url(#wave-grad-right)" stroke-width="2.5" stroke-dasharray="3 6"/>
      <path d="M 400,120 C 320,80 230,160 170,110 C 110,60 60,130 0,100" fill="none" stroke="url(#wave-grad-right)" stroke-width="1.5" stroke-dasharray="1 3"/>
      <path d="M 400,140 C 310,100 270,120 190,130 C 120,140 70,90 0,120" fill="none" stroke="url(#wave-grad-right)" stroke-width="1" stroke-dasharray="4 8"/>
    </svg>
  </div>
</div>

<div class="top-nav">
  <div class="nav-left">
    <div class="nav-logo-box">
      <svg class="logo-svg" width="24" height="24" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <rect x="6" y="6" width="20" height="20" rx="4" fill="none" stroke="#6366F1" stroke-width="2.5" stroke-linejoin="round"/>
        <path d="M 11,12 L 21,12" stroke="#6366F1" stroke-width="2" stroke-linecap="round"/>
        <path d="M 11,17 L 17,17" stroke="#6366F1" stroke-width="2" stroke-linecap="round"/>
        <circle cx="21" cy="21" r="1.5" fill="#3B82F6"/>
      </svg>
      <span class="logo-text">Resume <span class="logo-highlight">AI</span> Pro</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── NUCLEAR CSS: overrides every Streamlit default ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── BASE & DYNAMIC MESH BACKGROUND ── */
html, body {
  font-family: 'Inter', sans-serif!important;
  background-color: #0B1120!important;
}
/* Force Streamlit container elements to be fully transparent so the animated mesh-bg shows through */
[data-testid="stAppViewContainer"], 
.stApp, 
.main, 
.block-container {
  background: transparent!important;
  background-color: transparent!important;
  color: #E5E7EB!important;
}
[data-testid="stHeader"] {
  display: none!important; /* Hide streamlit default header completely */
}
.block-container {
  padding: 0.5rem 2.5rem 3rem!important;
  max-width: 1350px;
  margin: 0 auto;
}
/* Glassmorphism sidebar styling */
[data-testid="stSidebar"] {
  background: rgba(15, 23, 42, 0.75)!important;
  backdrop-filter: blur(16px)!important;
  -webkit-backdrop-filter: blur(16px)!important;
  border-right: 1px solid rgba(255, 255, 255, 0.05)!important;
}

/* Custom Navigation Bar */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 2.5rem!important;
  margin-left: -2.5rem!important;
  margin-right: -2.5rem!important;
  margin-bottom: 0.8rem!important;
  background: rgba(11, 17, 32, 0.45)!important;
  backdrop-filter: blur(12px)!important;
  -webkit-backdrop-filter: blur(12px)!important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05)!important;
  position: relative!important;
  z-index: 9999!important;
}
.nav-left {
  display: flex;
  align-items: center;
}
.nav-logo-box {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo-svg {
  filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
}
.logo-text {
  font-size: 1.15rem;
  font-weight: 800;
  color: #FFFFFF;
  letter-spacing: -0.5px;
}
.logo-highlight {
  color: #3B82F6;
}
.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.theme-toggle-btn {
  background: rgba(255, 255, 255, 0.03)!important;
  border: 1px solid rgba(255, 255, 255, 0.06)!important;
  color: #9CA3AF!important;
  width: 36px!important;
  height: 36px!important;
  border-radius: 50%!important;
  display: flex!important;
  align-items: center!important;
  justify-content: center!important;
  cursor: pointer!important;
  transition: all 0.2s ease!important;
}
.theme-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.08)!important;
  color: #E5E7EB!important;
  border-color: rgba(255, 255, 255, 0.15)!important;
}
.new-analysis-btn {
  background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%)!important;
  color: #FFFFFF!important;
  border: 1px solid rgba(255, 255, 255, 0.1)!important;
  border-radius: 999px!important;
  font-size: 0.8rem!important;
  font-weight: 700!important;
  padding: 7px 18px!important;
  cursor: pointer!important;
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.35)!important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
}
.new-analysis-btn:hover {
  background: linear-gradient(135deg, #6366F1 0%, #60A5FA 100%)!important;
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5), 0 0 10px rgba(59, 130, 246, 0.2)!important;
  transform: translateY(-1px)!important;
}

/* Background Waving Mesh Vectors */
.mesh-waves-container {
  position: absolute;
  top: 50px;
  left: 0;
  width: 100%;
  height: 250px;
  z-index: -1;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
  overflow: hidden;
}
.mesh-wave {
  width: 42%;
  height: 100%;
  opacity: 0.75;
}
.wave-left {
  animation: wave-float-left 12s infinite ease-in-out alternate;
}
.wave-right {
  animation: wave-float-right 14s infinite ease-in-out alternate;
}
@keyframes wave-float-left {
  0% { transform: translateY(0px) scaleY(1); }
  50% { transform: translateY(15px) scaleY(1.1) skewX(2deg); }
  100% { transform: translateY(-10px) scaleY(0.9) skewX(-2deg); }
}
@keyframes wave-float-right {
  0% { transform: translateY(0px) scaleY(1); }
  50% { transform: translateY(-15px) scaleY(1.1) skewX(-2deg); }
  100% { transform: translateY(10px) scaleY(0.9) skewX(2deg); }
}

/* Fixed Futuristic Background */
.mesh-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #070B19; /* Deeper space black-blue background */
  z-index: -999;
  overflow: hidden;
  pointer-events: none;
}
.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  mix-blend-mode: screen;
  pointer-events: none;
  opacity: 0.55; /* Higher opacity for noticeable effect */
}
.orb-1 {
  top: -10%;
  left: -10%;
  width: 650px;
  height: 650px;
  background: radial-gradient(circle, rgba(29, 78, 216, 0.5) 0%, rgba(29, 78, 216, 0.05) 70%);
  animation: float-aurora-1 25s infinite ease-in-out alternate;
}
.orb-2 {
  bottom: -15%;
  right: -10%;
  width: 700px;
  height: 700px;
  background: radial-gradient(circle, rgba(109, 40, 217, 0.45) 0%, rgba(109, 40, 217, 0.05) 70%);
  animation: float-aurora-2 30s infinite ease-in-out alternate;
}
.orb-3 {
  top: 30%;
  left: 45%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.35) 0%, rgba(6, 182, 212, 0) 70%);
  animation: float-aurora-3 22s infinite ease-in-out alternate;
}

/* Light streaks */
.light-streak {
  position: absolute;
  width: 150vw;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.25), rgba(139, 92, 246, 0.25), transparent);
  transform: rotate(-35deg);
  opacity: 0.7;
  pointer-events: none;
}
.streak-1 {
  top: 15%;
  left: -25%;
  animation: drift-streak-1 15s infinite linear;
}
.streak-2 {
  bottom: 25%;
  left: -35%;
  animation: drift-streak-2 20s infinite linear;
}

/* Float Animations for Aurora Orbs */
@keyframes float-aurora-1 {
  0% { transform: translate(0px, 0px) rotate(0deg) scale(1); }
  33% { transform: translate(80px, 60px) rotate(120deg) scale(1.15); }
  66% { transform: translate(-50px, 120px) rotate(240deg) scale(0.9); }
  100% { transform: translate(0px, 0px) rotate(360deg) scale(1); }
}
@keyframes float-aurora-2 {
  0% { transform: translate(0px, 0px) rotate(0deg) scale(0.9); }
  50% { transform: translate(-120px, -80px) rotate(-180deg) scale(1.1); }
  100% { transform: translate(0px, 0px) rotate(-360deg) scale(0.9); }
}
@keyframes float-aurora-3 {
  0% { transform: translate(0px, 0px) scale(1); }
  50% { transform: translate(-60px, 90px) scale(1.2); }
  100% { transform: translate(80px, -40px) scale(0.85); }
}

/* Drift animations for light streaks */
@keyframes drift-streak-1 {
  0% { transform: translate(-30%, -30%) rotate(-35deg); opacity: 0; }
  10% { opacity: 0.5; }
  90% { opacity: 0.5; }
  100% { transform: translate(30%, 30%) rotate(-35deg); opacity: 0; }
}
@keyframes drift-streak-2 {
  0% { transform: translate(-30%, 30%) rotate(-35deg); opacity: 0; }
  10% { opacity: 0.4; }
  90% { opacity: 0.4; }
  100% { transform: translate(30%, -30%) rotate(-35deg); opacity: 0; }
}

.glow-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  background-position: center;
  pointer-events: none;
  mask-image: radial-gradient(ellipse at 50% 50%, black 20%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at 50% 50%, black 20%, transparent 80%);
  opacity: 0.75;
}

/* ── HIDE chrome ── */
#MainMenu, footer, header, [data-testid="stToolbar"] {
  visibility: hidden!important;
  height: 0!important;
}

/* ── ALL TEXT ── */
p, span, label, div, .stMarkdown, h1, h2, h3, h4, li {
  color: #E5E7EB!important;
}
.stTextArea label, .stFileUploader label, .stTextInput label {
  color: #9CA3AF!important;
  font-size: .75rem!important;
  font-weight: 700!important;
  letter-spacing: 1px!important;
  text-transform: uppercase!important;
}

/* ── INPUTS ── */
.stTextArea textarea {
  background: rgba(17, 24, 39, 0.75)!important;
  backdrop-filter: blur(8px)!important;
  -webkit-backdrop-filter: blur(8px)!important;
  color: #E5E7EB!important;
  border: 1px solid rgba(255, 255, 255, 0.08)!important;
  border-radius: 14px!important;
  font-size: .9rem!important;
  transition: all 0.3s ease!important;
}
.stTextArea textarea:focus {
  border-color: #3B82F6!important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15)!important;
  background: rgba(17, 24, 39, 0.9)!important;
}
.stTextArea textarea::placeholder {
  color: #4B5563!important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
  background: rgba(17, 24, 39, 0.55)!important;
  backdrop-filter: blur(8px)!important;
  -webkit-backdrop-filter: blur(8px)!important;
  border: 2px dashed rgba(59, 130, 246, 0.25)!important;
  border-radius: 16px!important;
  padding: 1.5rem!important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
  box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.2)!important;
}
[data-testid="stFileUploader"]:hover {
  border-color: #3B82F6!important;
  background: rgba(59, 130, 246, 0.06)!important;
  box-shadow: 0 0 25px rgba(59, 130, 246, 0.18), inset 0 0 12px rgba(59, 130, 246, 0.05)!important;
}
/* hide the duplicate native button that causes double text */
[data-testid="stFileUploaderDropzone"] button {
  display: none!important;
}
[data-testid="stFileDropzoneInstructions"] {
  color: #9CA3AF!important;
  font-size: .88rem!important;
}
[data-testid="stFileDropzoneInstructions"] span {
  color: #E5E7EB!important;
  font-weight: 500!important;
}
[data-testid="stFileDropzoneInstructions"] small,
.stFileUploader small,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileDropzoneInstructions"] > *:last-child,
.stFileUploader [data-testid="stFileDropzoneInstructions"] > *:last-child {
  display: none !important;
  font-size: 0px !important;
  height: 0px !important;
  visibility: hidden !important;
  opacity: 0 !important;
}
[data-testid="stFileDropzoneInstructions"]::after,
.stFileUploader [data-testid="stFileDropzoneInstructions"]::after {
  content: "Limit 10 MB per file • PDF" !important;
  font-size: 0.75rem !important;
  color: #6B7280 !important;
  display: block !important;
  margin-top: 4px !important;
  visibility: visible !important;
  opacity: 1 !important;
}
[data-testid="stFileUploaderDropzone"] {
  cursor: pointer!important;
  text-align: center!important;
  padding: .5rem!important;
}
[data-testid="stFileUploaderDropzone"] * {
  color: #9CA3AF!important;
}
/* uploaded file row */
.uploadedFileName {
  background: rgba(31, 41, 55, 0.8)!important;
  border: 1px solid rgba(255, 255, 255, 0.1)!important;
  border-radius: 10px!important;
}
[data-testid="stFileUploaderDeleteBtn"] button {
  background: rgba(239, 68, 68, 0.15)!important;
  border-radius: 6px!important;
  color: #F87171!important;
  transition: all 0.2s ease!important;
}
[data-testid="stFileUploaderDeleteBtn"] button:hover {
  background: rgba(239, 68, 68, 0.3)!important;
  color: #FFA1A1!important;
}

/* ── BUTTON ── */
.stButton>button {
  background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%)!important;
  color: #FFFFFF!important;
  border: 1px solid rgba(255, 255, 255, 0.1)!important;
  border-radius: 14px!important;
  font-weight: 700!important;
  font-size: 0.88rem!important;
  padding: 0.85rem 2rem!important;
  width: 100%!important;
  box-shadow: 0 4px 20px rgba(29, 78, 216, 0.4)!important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
  letter-spacing: 0.5px!important;
  text-transform: uppercase!important;
  cursor: pointer!important;
}
.stButton>button:hover {
  background: linear-gradient(135deg, #2563EB 0%, #60A5FA 100%)!important;
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.6), 0 0 15px rgba(59, 130, 246, 0.3)!important;
  transform: translateY(-2px)!important;
}
.stButton>button:active {
  transform: translateY(0px)!important;
  box-shadow: 0 4px 10px rgba(29, 78, 216, 0.4)!important;
}

/* ── TABS ── */
.stTabs {
  margin-top: .5rem;
}
.stTabs [data-baseweb="tab-list"] {
  background: rgba(15, 23, 42, 0.85)!important;
  backdrop-filter: blur(8px)!important;
  -webkit-backdrop-filter: blur(8px)!important;
  border-radius: 16px!important;
  padding: 6px!important;
  border: 1px solid rgba(255, 255, 255, 0.05)!important;
  gap: 6px!important;
  display: flex!important;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.3)!important;
}
.stTabs [data-baseweb="tab"] {
  color: #9CA3AF!important;
  border-radius: 12px!important;
  font-weight: 600!important;
  font-size: .88rem!important;
  background: transparent!important;
  padding: 10px 24px!important;
  border: none!important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
  white-space: nowrap!important;
  flex: 1!important;
  text-align: center!important;
}
.stTabs [data-baseweb="tab"]:hover {
  background: rgba(59, 130, 246, 0.08)!important;
  color: #93C5FD!important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%)!important;
  color: #FFFFFF!important;
  box-shadow: 0 4px 15px rgba(29, 78, 216, 0.5), 0 0 10px rgba(59, 130, 246, 0.2)!important;
}
.stTabs [data-baseweb="tab-panel"] {
  padding: 1.2rem 0 0 0!important;
  background: transparent!important;
}

/* ── ALERTS ── */
.stAlert {
  background: rgba(17, 24, 39, 0.7)!important;
  backdrop-filter: blur(12px)!important;
  border-radius: 14px!important;
  border-left: 4px solid #3B82F6!important;
  color: #E5E7EB!important;
  border-top: 1px solid rgba(255, 255, 255, 0.04)!important;
  border-right: 1px solid rgba(255, 255, 255, 0.04)!important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04)!important;
}
.stAlert [data-testid="stMarkdownContainer"] p {
  color: #E5E7EB!important;
}

/* ── SUCCESS / INFO / ERROR OVERRIDES ── */
[data-testid="stSuccess"] {
  background: rgba(16, 185, 129, 0.08)!important;
  border-left-color: #10B981!important;
}
[data-testid="stInfo"] {
  background: rgba(59, 130, 246, 0.08)!important;
}
[data-testid="stError"] {
  background: rgba(239, 68, 68, 0.08)!important;
  border-left-color: #EF4444!important;
}

/* ── PROGRESS ── */
.stProgress>div>div {
  background: linear-gradient(90deg, #1D4ED8, #3B82F6)!important;
  border-radius: 4px!important;
}
.stProgress>div {
  background: rgba(31, 41, 55, 0.5)!important;
  border-radius: 4px!important;
}

/* ── SPINNER ── */
[data-testid="stSpinner"] p {
  color: #9CA3AF!important;
}

/* ── PLOTLY ── */
.js-plotly-plot .plotly, .js-plotly-plot, .plot-container {
  background: transparent!important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #0B1120;
}
::-webkit-scrollbar-thumb {
  background: #1F2937;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #374151;
}

/* ── CUSTOM COMPONENTS ── */
.hero {
  text-align: center;
  padding: 1.2rem 0 0.8rem;
}
.badge {
  display: inline-block;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%)!important;
  border: 1px solid rgba(59, 130, 246, 0.3)!important;
  color: #93C5FD!important;
  padding: 6px 18px!important;
  border-radius: 999px!important;
  font-size: 0.75rem!important;
  font-weight: 700!important;
  letter-spacing: 1.5px!important;
  text-transform: uppercase!important;
  margin-bottom: 0.5rem!important;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.1)!important;
  animation: badge-pulse 2.5s ease-in-out infinite alternate!important;
}
@keyframes badge-pulse {
  0% { box-shadow: 0 0 10px rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.25); }
  100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.25); border-color: rgba(139, 92, 246, 0.45); }
}

.title {
  font-size: 3.5rem!important;
  font-weight: 900!important;
  line-height: 1.05!important;
  margin: 0.5rem 0 1rem!important;
  background: linear-gradient(135deg, #FFFFFF 20%, #93C5FD 70%, #3B82F6 100%)!important;
  -webkit-background-clip: text!important;
  -webkit-text-fill-color: transparent!important;
  background-clip: text!important;
  letter-spacing: -2px!important;
  text-shadow: 0 2px 20px rgba(59, 130, 246, 0.05)!important;
}
.subtitle {
  color: #9CA3AF!important;
  font-size: 1.1rem!important;
  font-weight: 400!important;
  margin: 0 auto!important;
  max-width: 600px!important;
  line-height: 1.5!important;
}
.divider {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  margin: 0.8rem 0 1.2rem;
}

/* Premium SaaS Cards */
.card, .rcard {
  background: rgba(17, 24, 39, 0.65)!important;
  backdrop-filter: blur(16px)!important;
  -webkit-backdrop-filter: blur(16px)!important;
  border: 1px solid rgba(255, 255, 255, 0.06)!important;
  border-radius: 16px!important;
  padding: 1.5rem!important;
  margin-bottom: 1.2rem!important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3)!important;
}
.card:hover, .rcard:hover {
  border-color: rgba(59, 130, 246, 0.35)!important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 15px rgba(59, 130, 246, 0.05)!important;
  transform: translateY(-2px)!important;
}
.clabel {
  font-size: 0.72rem!important;
  font-weight: 800!important;
  color: #3B82F6!important;
  text-transform: uppercase!important;
  letter-spacing: 1.5px!important;
  margin-bottom: 0.8rem!important;
}

/* Premium Replica Card Design (Kbox v2) */
.kbox-v2 {
  background: rgba(10, 15, 30, 0.75)!important;
  backdrop-filter: blur(16px)!important;
  -webkit-backdrop-filter: blur(16px)!important;
  border: 1px solid rgba(255, 255, 255, 0.05)!important;
  border-radius: 14px!important;
  padding: 1.2rem 1.1rem 1rem!important; /* adjusted bottom padding */
  min-height: 120px!important; /* compact height for minimal, sparkline-free cards */
  position: relative!important;
  overflow: hidden!important;
  display: flex!important;
  flex-direction: column!important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1)!important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4)!important;
}
.kbox-v2:hover {
  transform: translateY(-2px)!important;
  border-color: rgba(255, 255, 255, 0.12)!important;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5)!important;
}

/* Overall Quality special card override (subtle, non-pulsing) */
.kbox-v2.special-card {
  border: 1px solid rgba(16, 185, 129, 0.25)!important;
}
.kbox-v2.special-card:hover {
  border-color: rgba(16, 185, 129, 0.55)!important;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5)!important;
}

/* Top right star ribbon */
.card-ribbon {
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 35px 35px 0;
  border-color: transparent #10B981 transparent transparent;
  z-index: 10;
}
.card-ribbon::after {
  content: "★";
  position: absolute;
  top: 4px;
  right: -31px;
  color: #FFFFFF;
  font-size: 0.65rem;
  font-weight: bold;
}

.kbox-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
  color: #9CA3AF!important;
}
.kbox-title {
  font-size: 0.62rem!important; /* Scale down to match mockup micro-typography */
  font-weight: 700!important;
  text-transform: uppercase!important;
  letter-spacing: 0.8px!important;
}
.kbox-info {
  font-size: 0.75rem!important;
  opacity: 0.6;
  cursor: help;
}
.kbox-val {
  font-size: 1.95rem!important; /* Reduced font size to perfectly fit scorecard numbers without clipping */
  font-weight: 800!important;
  color: #FFFFFF!important;
  line-height: 1!important;
  margin-bottom: 0.4rem!important;
  letter-spacing: -0.5px!important;
}
.kbox-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.76rem!important;
  font-weight: 700!important;
  margin-bottom: 0px!important; /* removed bottom margin since there's no sparkline */
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
/* Obsolete sparkline container styling removed */

/* Custom premium results complete banner */
.analysis-complete-banner {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(59, 130, 246, 0.05) 100%)!important;
  backdrop-filter: blur(12px)!important;
  -webkit-backdrop-filter: blur(12px)!important;
  border: 1px solid rgba(16, 185, 129, 0.25)!important;
  border-radius: 16px!important;
  padding: 1rem 1.8rem!important;
  margin-bottom: 1.5rem!important;
  display: flex!important;
  justify-content: space-between!important;
  align-items: center!important;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.1)!important;
}
.banner-left {
  display: flex!important;
  align-items: center!important;
  gap: 15px!important;
}
.banner-icon-circle {
  width: 42px!important;
  height: 42px!important;
  background: rgba(16, 185, 129, 0.15)!important;
  border-radius: 50%!important;
  display: flex!important;
  align-items: center!important;
  justify-content: center!important;
  border: 1px solid rgba(16, 185, 129, 0.3)!important;
  flex-shrink: 0!important;
}
.banner-text-box {
  display: flex!important;
  flex-direction: column!important;
}
.banner-title {
  font-size: 1.1rem!important;
  font-weight: 800!important;
  color: #FFFFFF!important;
}
.banner-subtitle {
  font-size: 0.85rem!important;
  color: #9CA3AF!important;
  margin-top: 1px!important;
}
.banner-vector-box {
  display: flex!important;
  align-items: center!important;
  opacity: 0.85!important;
}

/* Obsolete drawing animations removed */

/* Remaining Custom styles */
.rcard-t {
  font-size: .72rem;
  font-weight: 800;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: .6rem;
}
.rcard-v {
  font-size: 1.8rem;
  font-weight: 800;
  color: #F9FAFB;
}
.rcard-s {
  font-size: .8rem;
  color: #6B7280;
  margin-top: .2rem;
}

.role-badge {
  display: inline-block;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #93C5FD;
  padding: 7px 18px;
  border-radius: 999px;
  font-size: .95rem;
  font-weight: 700;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.1);
}

.bar-bg {
  background: rgba(31, 41, 55, 0.6);
  border-radius: 999px;
  height: 8px;
  overflow: hidden;
  margin: .4rem 0 .8rem;
}
.bar-fill {
  height: 100%;
  border-radius: 999px;
}

/* High-quality Glowing Tags */
.tag {
  display: inline-block!important;
  padding: 6px 14px!important;
  border-radius: 999px!important;
  font-size: 0.76rem!important;
  font-weight: 700!important;
  margin: 3px!important;
  transition: all 0.2s ease!important;
  letter-spacing: 0.2px!important;
}
.tag:hover {
  transform: translateY(-1px) scale(1.03)!important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)!important;
}
.tg {
  background: rgba(16, 185, 129, 0.1)!important;
  color: #34D399!important;
  border: 1px solid rgba(16, 185, 129, 0.25)!important;
}
.tg:hover {
  background: rgba(16, 185, 129, 0.16)!important;
  border-color: rgba(16, 185, 129, 0.45)!important;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.15)!important;
}
.tr {
  background: rgba(239, 68, 68, 0.1)!important;
  color: #F87171!important;
  border: 1px solid rgba(239, 68, 68, 0.25)!important;
}
.tr:hover {
  background: rgba(239, 68, 68, 0.16)!important;
  border-color: rgba(239, 68, 68, 0.45)!important;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.15)!important;
}
.tb {
  background: rgba(59, 130, 246, 0.1)!important;
  color: #60A5FA!important;
  border: 1px solid rgba(59, 130, 246, 0.25)!important;
}
.tb:hover {
  background: rgba(59, 130, 246, 0.16)!important;
  border-color: rgba(59, 130, 246, 0.45)!important;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.15)!important;
}
.tp {
  background: rgba(139, 92, 246, 0.1)!important;
  color: #A78BFA!important;
  border: 1px solid rgba(139, 92, 246, 0.25)!important;
}
.tp:hover {
  background: rgba(139, 92, 246, 0.16)!important;
  border-color: rgba(139, 92, 246, 0.45)!important;
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.15)!important;
}
.ty {
  background: rgba(245, 158, 11, 0.1)!important;
  color: #FCD34D!important;
  border: 1px solid rgba(245, 158, 11, 0.25)!important;
}
.ty:hover {
  background: rgba(245, 158, 11, 0.16)!important;
  border-color: rgba(245, 158, 11, 0.45)!important;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.15)!important;
}

.sugg {
  background: rgba(59, 130, 246, 0.05);
  border-left: 3px solid #3B82F6;
  border-radius: 0 12px 12px 0;
  padding: .8rem 1.1rem;
  margin-bottom: .6rem;
  color: #D1D5DB;
  font-size: .88rem;
  line-height: 1.6;
  border-top: 1px solid rgba(255,255,255,0.02);
  border-right: 1px solid rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.02);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 380px;
  background: rgba(17, 24, 39, 0.5);
  backdrop-filter: blur(8px);
  border: 2px dashed rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  text-align: center;
}
.empty-ico {
  font-size: 3.5rem;
  margin-bottom: .8rem;
}
.empty-t {
  font-size: 1.1rem;
  font-weight: 700;
  color: #9CA3AF;
}
.empty-s {
  font-size: .88rem;
  color: #4B5563;
  margin-top: .3rem;
}

.pred-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: .55rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.pred-row:last-child {
  border: none;
}
.pred-n {
  font-size: .88rem;
  color: #D1D5DB;
  font-weight: 500;
}
.pred-p {
  font-size: .88rem;
  color: #3B82F6;
  font-weight: 700;
}

.sec-tag-ok {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(16, 185, 129, 0.1);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.2);
  padding: 4px 12px;
  border-radius: 8px;
  font-size: .75rem;
  font-weight: 600;
  margin: 3px;
}
.sec-tag-no {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(239, 68, 68, 0.1);
  color: #F87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 4px 12px;
  border-radius: 8px;
  font-size: .75rem;
  font-weight: 600;
  margin: 3px;
}

.howbox {
  background: rgba(59, 130, 246, 0.04);
  border: 1px solid rgba(59, 130, 246, 0.1);
  border-radius: 14px;
  padding: 1.1rem 1.3rem;
  color: #9CA3AF;
  font-size: .85rem;
  line-he/* ── ULTRA-RESPONSIVE MEDIA QUERIES ── */

/* Tablet Breakpoint (max-width: 1024px) */
@media (max-width: 1024px) {
  .block-container {
    padding: 0.5rem 1.8rem 2.5rem!important;
    max-width: 95%!important;
  }
  
  /* Make 5 columns scorecard wrap elegantly into 3 or 2 columns grid */
  div[data-testid="stHorizontalBlock"]:has(.kbox-v2),
  [data-testid="stHorizontalBlock"]:has(.kbox-v2),
  .stHorizontalBlock:has(.kbox-v2) {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 1rem !important;
    width: 100% !important;
  }
  
  div[data-testid="stHorizontalBlock"]:has(.kbox-v2) [data-testid="stColumn"],
  div[data-testid="stHorizontalBlock"]:has(.kbox-v2) [data-testid="column"],
  [data-testid="stHorizontalBlock"]:has(.kbox-v2) [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has(.kbox-v2) [data-testid="column"],
  .stHorizontalBlock:has(.kbox-v2) [data-testid="stColumn"],
  .stHorizontalBlock:has(.kbox-v2) [data-testid="column"] {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 100% !important;
  }
}

/* Mobile landscape and generic screens (max-width: 768px) */
@media (max-width: 768px) {
  /* Force Streamlit standard multi-column layout blocks to stack vertically and take 100% width */
  div[data-testid="stHorizontalBlock"],
  [data-testid="stHorizontalBlock"],
  .stHorizontalBlock {
    flex-direction: column !important;
    display: flex !important;
    gap: 1.2rem !important;
    width: 100% !important;
  }
  
  /* Target EVERY possible column div inside a horizontal block aggressively */
  div[data-testid="stHorizontalBlock"] > div,
  [data-testid="stHorizontalBlock"] > div,
  div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"],
  div[data-testid="stHorizontalBlock"] div[data-testid="column"],
  [data-testid="stHorizontalBlock"] [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"] [data-testid="column"],
  .stHorizontalBlock [data-testid="stColumn"],
  .stHorizontalBlock [data-testid="column"] {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 100% !important;
    flex: 1 1 100% !important;
    display: block !important;
  }

  .title {
    font-size: 2.1rem !important;
    letter-spacing: -1.2px !important;
    line-height: 1.1 !important;
  }
  .subtitle {
    font-size: 0.95rem !important;
  }
  .hero {
    padding: 0.8rem 0 0.4rem;
  }
}

/* Mobile portrait Breakpoint (max-width: 640px) */
@media (max-width: 640px) {
  .block-container {
    padding: 0.4rem 1rem 2rem!important;
  }
  
  /* Top Custom Nav bar mobile spacing adjustment */
  .top-nav {
    padding: 0.5rem 1rem!important;
    margin-left: -1rem!important;
    margin-right: -1rem!important;
    margin-bottom: 0.6rem!important;
  }
  .logo-text {
    font-size: 0.95rem !important;
  }
  
  /* Responsive Scorecard Grid (1 column on small phones for perfect spacing and full-width) */
  div[data-testid="stHorizontalBlock"]:has(.kbox-v2),
  [data-testid="stHorizontalBlock"]:has(.kbox-v2),
  .stHorizontalBlock:has(.kbox-v2) {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 0.9rem !important;
    width: 100% !important;
  }
  
  /* Target columns inside card grid to override vertical stacking block width */
  div[data-testid="stHorizontalBlock"]:has(.kbox-v2) > div,
  [data-testid="stHorizontalBlock"]:has(.kbox-v2) [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has(.kbox-v2) [data-testid="column"] {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 100% !important;
  }
  
  .kbox-v2 {
    min-height: 110px !important;
    padding: 1.1rem 1rem 0.9rem!important;
    box-sizing: border-box !important;
    width: 100% !important;
  }
  .kbox-val {
    font-size: 2.1rem !important;
  }
  .kbox-title {
    font-size: 0.72rem !important;
    letter-spacing: 0.8px !important;
  }
  .kbox-status {
    font-size: 0.82rem !important;
  }
  
  /* Swipeable Horizontal Scroll Tabs for Mobile UX */
  .stTabs [data-baseweb="tab-list"] {
    overflow-x: auto !important;
    white-space: nowrap !important;
    display: flex !important;
    flex-wrap: nowrap !important;
    padding: 4px !important;
    gap: 4px !important;
    scrollbar-width: none; /* Hide scrollbars for absolute clean look on Firefox */
  }
  .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none; /* Hide scrollbars for absolute clean look on Webkit/Chrome */
  }
  .stTabs [data-baseweb="tab"] {
    padding: 8px 16px !important;
    font-size: 0.78rem !important;
    flex: 0 0 auto !important;
  }
  
  /* Touch-friendly buttons */
  .stButton>button {
    padding: 0.95rem 1.5rem !important;
    font-size: 0.9rem !important;
  }
  
  /* Result Complete Banner mobile spacing - full width and neatly aligned */
  .analysis-complete-banner {
    padding: 1rem 1.2rem!important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    width: 100% !important;
    box-sizing: border-box !important;
  }
  .banner-left {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
  }
  .banner-icon-circle {
    width: 36px !important;
    height: 36px !important;
    flex-shrink: 0 !important;
  }
  .banner-title {
    font-size: 0.95rem !important;
  }
  .banner-subtitle {
    font-size: 0.78rem !important;
  }
  .banner-vector-box {
    display: none !important; /* Hide secondary graphics on mobile to maximize viewport area */
  }
}
</style>

""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_model():
    return load_model()


def gauge_fig(val):
    c = "#10B981" if val >= 70 else "#F59E0B" if val >= 45 else "#EF4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={"suffix": "%", "font": {"color": c, "size": 30, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#374151", "tickfont": {"color": "#4B5563"}},
            "bar": {"color": c, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],  "color": "rgba(239,68,68,0.05)"},
                {"range": [40, 70], "color": "rgba(245,158,11,0.05)"},
                {"range": [70, 100],"color": "rgba(16,185,129,0.05)"},
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=15, r=15, t=10, b=10),
        height=145,
        font={"family": "Inter"},
    )
    return fig


def bar(pct, color):
    return f'<div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>'


# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="badge">✦ AI-Powered Resume Intelligence</div>
  <div class="title">Resume AI Pro</div>
  <div class="subtitle">Upload your resume → Instant ATS score, role prediction, skill gap & smart feedback</div>
</div>
<hr class="divider">
""", unsafe_allow_html=True)

# ── TWO-COLUMN LAYOUT ─────────────────────────────────────────────────────────
left, gap, right = st.columns([1, 0.04, 1.65])

# ════════════════════ LEFT ════════════════════
with left:
    st.markdown('<div class="card"><div class="clabel">📂 Step 1 — Upload Resume (PDF)</div></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload Resume PDF", type=["pdf"], label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="clabel">📝 Step 2 — Job Description (Optional)</div></div>', unsafe_allow_html=True)
    job_desc = st.text_area(
        "Job Description", height=150,
        placeholder="Paste the job posting here for JD match analysis...",
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    analyze = st.button("🚀  Analyze My Resume", use_container_width=True)

    if not uploaded:
        st.markdown("""
        <div class="howbox">
          <strong>How it works:</strong><br>
          📄 Upload your PDF resume<br>
          🤖 AI extracts & analyzes content<br>
          📊 Get ATS score & role match<br>
          💡 Receive smart improvement tips
        </div>
        """, unsafe_allow_html=True)

# ════════════════════ RIGHT ════════════════════
with right:
    if not uploaded:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-ico">📊</div>
          <div class="empty-t">Your Analysis Will Appear Here</div>
          <div class="empty-s">Upload a resume to get started →</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    if uploaded and not analyze:
        st.info("✅ Resume uploaded! Click **Analyze My Resume** to start the analysis.")
        st.stop()

    # ── ANALYSIS ─────────────────────────────────────────────────────────────
    with st.spinner("🧠 Analyzing your resume with AI..."):
        raw = extract_text_from_pdf(uploaded)
        if not raw or len(raw) < 50:
            st.error("❌ Could not extract text. Ensure the PDF has selectable text (not a scanned image).")
            st.stop()

        model = get_model()
        pred, conf, top3 = predict_role(raw, model)
        if pred == "Unknown":
            pred = "Insufficient Data"

        # ── NEW INTELLIGENT SCORING ─────────────────────────────────────
        skill_data   = compute_skill_match(raw, pred)
        quality_data = compute_resume_quality(raw)
        jd_data      = compute_jd_match(raw, job_desc)
        has_jd       = bool(job_desc.strip())
        ats_result   = compute_final_ats_score(
            skill_pct       = skill_data["pct"],
            role_confidence = conf,
            jd_sim_pct      = jd_data["similarity_pct"],
            quality_pct     = quality_data["total"],
            has_jd          = has_jd
        )

        # ── LEGACY DISPLAY VARS ─────────────────────────────────────────
        skills   = extract_skills(raw)
        missing  = skill_data["missing"]
        sections = check_resume_sections(raw)
        kw       = {"matched": jd_data["matched_keywords"],
                    "overlap_pct": jd_data["keyword_overlap_pct"]}

        # Build score dict for feedback module
        score = {
            "total":        ats_result["score"],
            "skills_pct":   skill_data["pct"],
            "jd_pct":       jd_data["similarity_pct"],
            "complete_pct": quality_data["total"],
            "jd_similarity": jd_data["similarity_pct"],
            # legacy keys
            "skills_score": skill_data["pct"] * 0.4,
            "jd_score":     jd_data["similarity_pct"] * 0.4,
            "completeness_score": quality_data["total"] * 0.2,
            "matched_role_skills": skill_data["matched"],
            "total_role_skills":   skill_data["total"],
        }
        ats = generate_ats_feedback(raw, pred, missing, score)
        ats["sections"] = sections

    # ── METADATA & REPLICA ANALYSIS BANNER ─────────────────────────────────────────
    st.markdown("""<div class="analysis-complete-banner">
<div class="banner-left">
  <div class="banner-icon-circle">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  </div>
  <div class="banner-text-box">
    <div class="banner-title">Analysis complete!</div>
    <div class="banner-subtitle">Scroll through the tabs below to explore your results.</div>
  </div>
</div>
<div class="banner-right">
  <div class="banner-vector-box">
    <svg width="56" height="56" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="14" y="10" width="36" height="44" rx="4" fill="rgba(59, 130, 246, 0.08)" stroke="#3B82F6" stroke-width="2" stroke-dasharray="1 1"/>
      <line x1="22" y1="20" x2="38" y2="20" stroke="#3B82F6" stroke-width="2" stroke-linecap="round"/>
      <line x1="22" y1="28" x2="42" y2="28" stroke="#3B82F6" stroke-width="2" stroke-linecap="round"/>
      <line x1="22" y1="36" x2="32" y2="36" stroke="#3B82F6" stroke-width="2" stroke-linecap="round"/>
      <circle cx="44" cy="44" r="8" fill="#10B981" />
      <polyline points="41 44 43 46 47 42" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>
</div>
</div>""", unsafe_allow_html=True)

    # ── KPI ROW (5 metrics, fully matching scorecard aesthetics) ───────────────────
    tot      = int(ats_result["score"])
    sk_pct   = int(skill_data["pct"])
    jd_pct   = int(jd_data["similarity_pct"])
    qual_pct = int(quality_data["total"])
    conf_int = int(round(conf))

    vals = [tot, conf_int, sk_pct, jd_pct, qual_pct]
    names = ["ats-score", "role-match", "skills-match", "jd-match", "quality"]
    labels = ["ATS Score", "Role Match", "Skills Match", "JD Match", "Overall Quality"]

    k1, k2, k3, k4, k5 = st.columns(5)
    for col, num, lbl, val, name_id in zip(
        [k1, k2, k3, k4, k5],
        [f"{tot}%", f"{conf_int}%", f"{sk_pct}%", f"{jd_pct}%", f"{qual_pct}%"],
        labels,
        vals,
        names
    ):
        with col:
            status_text, status_color = get_status_details(lbl.replace(" Match", "").replace("Overall ", ""), val, has_jd)
            
            is_special = (lbl == "Overall Quality")
            special_class = "special-card" if is_special else ""
            ribbon = '<div class="card-ribbon"></div>' if is_special else ""
            
            status_prefix = "● " if status_text != "Not Available" else ""
            
            st.markdown(f"""<div class="kbox-v2 {special_class}">
{ribbon}
<div class="kbox-header">
  <span class="kbox-title">{lbl}</span>
  <span class="kbox-info">ⓘ</span>
</div>
<div class="kbox-val">{num}</div>
<div class="kbox-status" style="color: {status_color}; margin-bottom: 0px!important;">
  <span class="status-dot" style="background-color: {status_color};"></span>
  {status_prefix}{status_text}
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs(["🎯 Overview", "🔧 Skills", "💡 Feedback", "📄 Raw Text"])

    # ── TAB 1: OVERVIEW ───────────────────────────────────────────────────────
    with t1:
        ov1, ov2 = st.columns([1, 1.3])
        with ov1:
            st.markdown('<div style="text-align: center; font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1.2px; color: #8F9CAE; margin-bottom: -20px;">ATS Score</div>', unsafe_allow_html=True)
            st.plotly_chart(gauge_fig(tot), use_container_width=True)

            st.markdown(f"""
            <div class="rcard">
              <div class="rcard-t">🎯 Predicted Role</div>
              <div style="margin:.3rem 0;"><span class="role-badge">{pred}</span></div>
              <div class="rcard-s">Model confidence: {conf}%</div>
            </div>""", unsafe_allow_html=True)

        with ov2:
            # ── 4-FACTOR BREAKDOWN: integer scores, color-coded ───────────────
            def score_color(v):
                return "#10B981" if v >= 70 else "#F59E0B" if v >= 50 else "#EF4444"

            st.markdown('<div class="rcard"><div class="rcard-t">📊 Score Breakdown</div>', unsafe_allow_html=True)
            breakdown_items = [
                ("🟣 Skill Match",     sk_pct,   f"{len(skill_data['matched'])}/{skill_data['total']} role skills"),
                ("🔵 Role Confidence", conf_int, f"AI predicted: {pred}"),
                ("🟡 JD Similarity",   jd_pct,   "Semantic match vs JD" if has_jd else "Paste a JD to unlock"),
                ("🟢 Resume Quality",  qual_pct, f"{quality_data['found_sections']} sections · {quality_data['word_count']} words"),
            ]
            for name, v, subtitle in breakdown_items:
                c = score_color(v)
                st.markdown(f"""
                <div style="margin-bottom:.9rem;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="font-size:.83rem;color:#D1D5DB;font-weight:600;">{name}</span>
                    <span style="font-size:1rem;color:{c};font-weight:800;">{v}%</span>
                  </div>
                  <div style="background:#1F2937;border-radius:999px;height:8px;overflow:hidden;">
                    <div style="width:{v}%;height:100%;background:{c};border-radius:999px;"></div>
                  </div>
                  <div style="font-size:.7rem;color:#374151;margin-top:3px;">{subtitle}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Top predictions
            st.markdown('<div class="rcard"><div class="rcard-t">🏆 Top Predictions</div>', unsafe_allow_html=True)
            for r_name, r_pct in top3:
                st.markdown(f"""
                <div class="pred-row">
                  <span class="pred-n">{r_name}</span>
                  <span class="pred-p">{r_pct}%</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Resume sections
            sections = ats.get("sections", {})
            st.markdown('<div class="rcard"><div class="rcard-t">📋 Resume Sections</div><div>', unsafe_allow_html=True)
            for sec, ok in sections.items():
                cls = "sec-tag-ok" if ok else "sec-tag-no"
                ico = "✓" if ok else "✗"
                st.markdown(f'<span class="{cls}">{ico} {sec}</span>', unsafe_allow_html=True)
            st.markdown("</div></div>", unsafe_allow_html=True)

    # ── TAB 2: SKILLS ─────────────────────────────────────────────────────────
    with t2:
        s1, s2 = st.columns(2)
        tag_colors = ["tg", "tb", "tp", "ty", "tg", "tb"]

        with s1:
            st.markdown('<div class="rcard"><div class="rcard-t">✅ Skills Found in Resume</div>', unsafe_allow_html=True)
            if skills:
                for i, (cat, cat_skills) in enumerate(skills.items()):
                    st.markdown(f'<div style="font-size:.72rem;color:#4B5563;font-weight:700;margin:.5rem 0 .2rem;text-transform:uppercase;letter-spacing:1px;">{cat}</div>', unsafe_allow_html=True)
                    tags = "".join(f'<span class="tag {tag_colors[i % len(tag_colors)]}">{s}</span>' for s in cat_skills)
                    st.markdown(tags, unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:#6B7280;font-size:.85rem;">No specific skills detected. Ensure PDF has selectable text.</span>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with s2:
            st.markdown('<div class="rcard"><div class="rcard-t">❌ Missing Skills for This Role</div>', unsafe_allow_html=True)
            if missing:
                tags = "".join(f'<span class="tag tr">{s}</span>' for s in missing)
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.markdown('<span class="tag tg">🎉 All key skills present!</span>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if job_desc.strip() and kw.get("matched"):
                st.markdown('<div class="rcard"><div class="rcard-t">🎯 JD Keyword Matches</div>', unsafe_allow_html=True)
                tags = "".join(f'<span class="tag tb">{k}</span>' for k in kw["matched"][:24])
                st.markdown(tags, unsafe_allow_html=True)
                st.markdown(f'<div style="margin-top:.5rem;font-size:.78rem;color:#6B7280;">{kw.get("overlap_pct",0)}% keyword overlap with job description</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            elif not job_desc.strip():
                st.markdown('<div class="rcard"><div style="color:#4B5563;font-size:.83rem;">Paste a job description to see keyword match analysis.</div></div>', unsafe_allow_html=True)

    # ── TAB 3: FEEDBACK ───────────────────────────────────────────────────────
    with t3:
        recs = ats.get("recommendations", [])
        # Header
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:1rem;padding:.9rem 1.1rem;
                    background:#111827;border:1px solid #1F2937;border-radius:14px;">
          <span style="font-size:1.4rem;">💡</span>
          <div>
            <div style="font-size:.95rem;font-weight:700;color:#E5E7EB;">Smart Recommendations</div>
            <div style="font-size:.76rem;color:#475569;margin-top:2px;">{len(recs) if recs else 6} personalized suggestions based on your resume analysis</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        display_recs = recs if recs else [
            "🔧 **Add Role-Specific Skills**: Check the Skills tab to see which skills are missing for your target role.",
            "📊 **Add Measurable Results**: Include metrics like percentages, revenue, team size, or time saved.",
            "💪 **Use Action Verbs**: Start every bullet with: Built, Led, Developed, Improved, Optimized, Delivered.",
            "📋 **Add Missing Sections**: Ensure your resume has: Summary, Skills, Experience, Education, Projects.",
            "🎯 **Mirror the Job Description**: Paste the JD in the sidebar to get a keyword match score.",
            "💡 **ATS Format Tip**: Use clean PDF format, standard section headings, no tables or images.",
        ]
        for i, rec in enumerate(display_recs, 1):
            if rec.startswith("✅"):
                accent, bg = "#10B981", "rgba(16,185,129,.06)"
            elif any(rec.startswith(x) for x in ["⚠️","💪","🔧"]):
                accent, bg = "#F59E0B", "rgba(245,158,11,.06)"
            elif any(rec.startswith(x) for x in ["❌","🎯 **Low"]):
                accent, bg = "#EF4444", "rgba(239,68,68,.06)"
            else:
                accent, bg = "#3B82F6", "rgba(59,130,246,.06)"
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {accent}22;border-left:4px solid {accent};
                        border-radius:0 12px 12px 0;padding:.85rem 1.1rem;margin-bottom:.55rem;
                        display:flex;align-items:flex-start;gap:.75rem;">
              <div style="background:{accent}22;color:{accent};border-radius:50%;min-width:22px;height:22px;
                          display:flex;align-items:center;justify-content:center;font-size:.68rem;
                          font-weight:800;flex-shrink:0;margin-top:2px;">{i}</div>
              <div style="color:#D1D5DB;font-size:.87rem;line-height:1.65;">{rec}</div>
            </div>
            """, unsafe_allow_html=True)

        # Skill tips
        skill_tips = ats.get("skill_tips", [])
        if skill_tips:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="rcard"><div class="rcard-t">🚀 Skill Development Tips</div>', unsafe_allow_html=True)
            for tip in skill_tips:
                st.markdown(f'<div style="color:#CBD5E1;font-size:.86rem;padding:.35rem 0;border-bottom:1px solid #1F2937;line-height:1.6;">› {tip}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)


        fb1, fb2 = st.columns(2)
        with fb1:
            verbs = ats.get("action_verbs", {})
            v_ok  = verbs.get("has_enough", False)
            ico   = "✅" if v_ok else "⚠️"
            st.markdown(f'<div class="rcard"><div class="rcard-t">{ico} Action Verbs ({verbs.get("count",0)} found)</div>', unsafe_allow_html=True)
            found_v = verbs.get("found", [])
            if found_v:
                st.markdown("".join(f'<span class="tag tg">{v}</span>' for v in found_v[:10]), unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:#6B7280;font-size:.82rem;">No strong verbs found. Use: Developed, Led, Built, Achieved…</span>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            wc = ats.get("word_count", {})
            st.markdown(f"""<div class="rcard">
              <div class="rcard-t">📝 Word Count</div>
              <div class="rcard-v">{wc.get("word_count",0)}</div>
              <div class="rcard-s">{wc.get("status","")} — {wc.get("tip","")}</div>
            </div>""", unsafe_allow_html=True)

        with fb2:
            quant = ats.get("quantification", {})
            q_ok  = quant.get("has_quantification", False)
            st.markdown(f'<div class="rcard"><div class="rcard-t">{"✅" if q_ok else "❌"} Quantified Achievements</div>', unsafe_allow_html=True)
            found_q = quant.get("found", [])
            if found_q:
                for q in found_q[:5]:
                    st.markdown(f'<div style="font-size:.82rem;color:#93C5FD;padding:2px 0;">• {q}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#6B7280;font-size:.82rem;">No metrics found. Add numbers like "Improved speed by 40%" or "Led team of 8".</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            rating  = ats.get("rating", "")
            summary = ats.get("summary", "")
            r_color = "#10B981" if "Excellent" in rating else "#F59E0B" if "Good" in rating else "#EF4444"
            st.markdown(f"""<div class="rcard" style="border-color:rgba(255,255,255,0.08);">
              <div class="rcard-t">🏅 Overall Rating</div>
              <div style="font-size:1.2rem;font-weight:800;color:{r_color};margin:.3rem 0;">{rating}</div>
              <div class="rcard-s">{summary}</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 4: RAW TEXT ───────────────────────────────────────────────────────
    with t4:
        wc_info = ats.get("word_count", {})
        st.markdown(f'<div style="color:#6B7280;font-size:.8rem;margin-bottom:.5rem;">📄 {wc_info.get("word_count",0)} words · {len(raw):,} characters extracted</div>', unsafe_allow_html=True)
        st.text_area("Extracted Resume Text", raw, height=380, label_visibility="collapsed")
