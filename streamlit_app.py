import streamlit as st
import os
import sys
import json
from datetime import datetime

# Add the current directory to path to import the backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import backend services
from gemini_service import GeminiService
from speech_processor import SpeechRecognizer
from code_analyzer import CodeAnalyzer
from user_profiles import UserProfileManager
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(
    page_title="AI Coding Assistant",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDUMYNQBolwT8YqvNhuYRpKhtXV_xPUxok")

# Initialize services
@st.cache_resource
def load_services():
    gemini_service = GeminiService(api_key=GEMINI_API_KEY)
    speech_recognizer = SpeechRecognizer()
    code_analyzer = CodeAnalyzer()
    user_profile_manager = UserProfileManager()
    return gemini_service, speech_recognizer, code_analyzer, user_profile_manager

gemini_service, speech_recognizer, code_analyzer, user_profile_manager = load_services()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
if 'code' not in st.session_state:
    st.session_state.code = ""
if 'language' not in st.session_state:
    st.session_state.language = "python"
if 'theme' not in st.session_state:
    st.session_state.theme = "dark"
if 'font_size' not in st.session_state:
    st.session_state.font_size = 14

# CSS to customize the appearance
st.markdown("""
<style>
    .stApp {
        background-color: #282659;
    }
    .editor-container {
        border-radius: 5px;
        padding: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .output-container {
        border-radius: 5px;
        padding: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-top: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #2e2e2e;
    }
    h1, h2, h3 {
        color: #2e7d32;
    }
    .stButton>button {
        background-color: #2e7d32;
        color: white;
    }
    .stButton>button:hover {
        background-color: #1b5e20;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("AI Coding Assistant")
st.sidebar.image("https://www.svgrepo.com/show/374171/python.svg", width=100)

# Get user preferences from profile manager
user_context = user_profile_manager.get_user_context(st.session_state.user_id)
user_preferences = user_context.get("preferences", {})

# User preferences section
st.sidebar.header("User Preferences")
user_language = st.sidebar.selectbox(
    "Preferred Language",
    ["Python", "JavaScript", "Java", "C++", "Go"],
    index=["python", "javascript", "java", "c++", "go"].index(
        user_preferences.get("preferred_language", "Python").lower()
    ) if user_preferences.get("preferred_language", "Python").lower() in ["python", "javascript", "java", "c++", "go"] else 0
)
skill_level = st.sidebar.select_slider(
    "Skill Level",
    options=["beginner", "intermediate", "advanced"],
    value=user_preferences.get("skill_level", "intermediate").lower()
)
theme = st.sidebar.radio(
    "Theme", 
    ["Light", "Dark"], 
    index=0 if user_preferences.get("theme", "dark") == "light" else 1
)
font_size = st.sidebar.slider(
    "Font Size", 
    12, 24, 
    value=user_preferences.get("font_size", 14)
)

# Save preferences
if st.sidebar.button("Save Preferences"):
    # Update session state
    st.session_state.language = user_language.lower()
    st.session_state.theme = theme.lower()
    st.session_state.font_size = font_size
    
    # Update backend preferences
    updated_preferences = {
        "preferred_language": user_language,
        "skill_level": skill_level,
        "theme": theme.lower(),
        "font_size": font_size
    }
    user_profile_manager.update_preferences(st.session_state.user_id, updated_preferences)
    st.sidebar.success("Preferences saved!")

# Main navigation
page = st.sidebar.radio(
    "Navigation",
    ["Code Editor", "Code Analysis", "Documentation", "Test Generator", "Voice Coding"]
)

# Code Editor Page
if page == "Code Editor":
    st.title("Code Editor")
    
    # Language selection for current code
    code_language = st.selectbox(
        "Language",
        ["Python", "JavaScript", "Java", "C++", "Go"],
        index=["python", "javascript", "java", "c++", "go"].index(st.session_state.language) 
        if st.session_state.language in ["python", "javascript", "java", "c++", "go"] else 0
    )
    
    # Code editor
    code = st.text_area(
        "Write or paste your code here:",
        value=st.session_state.code,
        height=400,
        key="code_editor"
    )
    
    # Save code to session state when changed
    if code != st.session_state.code:
        st.session_state.code = code
        st.session_state.language = code_language.lower()
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Format Code"):
            if code:
                with st.spinner("Formatting code..."):
                    try:
                        formatted_code = gemini_service.format_code(code, code_language.lower())
                        st.session_state.code = formatted_code
                        st.success("Code formatted successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter some code first.")
    
    with col2:
        if st.button("Explain Code"):
            if code:
                with st.spinner("Generating explanation..."):
                    try:
                        explanation = gemini_service.explain_code(code, code_language.lower())
                        st.info(explanation)
                        # Add to user history
                        user_profile_manager.add_history_entry(
                            st.session_state.user_id, 
                            "explain_code", 
                            {"code": code, "explanation": explanation}
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter some code first.")
    
    with col3:
        if st.button("Improve Code"):
            if code:
                with st.spinner("Improving code..."):
                    try:
                        improved_code, explanation = gemini_service.improve_code(code, code_language.lower())
                        st.session_state.code = improved_code
                        st.success("Code improved!")
                        st.info(explanation)
                        # Add to user history
                        user_profile_manager.add_history_entry(
                            st.session_state.user_id, 
                            "improve_code", 
                            {"original_code": code, "improved_code": improved_code}
                        )
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter some code first.")
    
    with col4:
        if st.button("Analyze Code"):
            if code:
                with st.spinner("Analyzing code..."):
                    try:
                        analysis = code_analyzer.analyze(code, code_language.lower())
                        suggestions = gemini_service.get_code_improvements(code, code_language.lower())
                        
                        st.subheader("Code Analysis")
                        if "complexity" in analysis:
                            st.metric("Complexity Score", analysis["complexity"])
                        
                        if "issues" in analysis and analysis["issues"]:
                            st.error("Issues Found:")
                            for issue in analysis["issues"]:
                                st.write(f"- {issue}")
                        else:
                            st.success("No issues found!")
                        
                        st.subheader("Suggestions")
                        st.write(suggestions)
                        
                        # Add to user history
                        user_profile_manager.add_history_entry(
                            st.session_state.user_id, 
                            "analyze_code", 
                            {"code": code, "analysis": analysis, "suggestions": suggestions}
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter some code first.")

# Code Analysis Page
elif page == "Code Analysis":
    st.title("Code Analysis")
    
    # Use the code from the editor or allow new input
    use_editor_code = st.checkbox("Use code from editor", value=True)
    
    if use_editor_code and st.session_state.code:
        code = st.session_state.code
        language = st.session_state.language
        st.code(code, language=language)
    else:
        language = st.selectbox(
            "Language",
            ["Python", "JavaScript", "Java", "C++", "Go"],
            index=["python", "javascript", "java", "c++", "go"].index(st.session_state.language)
            if st.session_state.language in ["python", "javascript", "java", "c++", "go"] else 0
        )
        code = st.text_area("Enter code to analyze:", height=300)
    
    if st.button("Run Analysis") and code:
        with st.spinner("Analyzing code..."):
            try:
                # Get analysis from code analyzer
                analysis = code_analyzer.analyze(code, language.lower())
                
                # Get suggestions from Gemini service
                suggestions = gemini_service.get_code_improvements(code, language.lower())
                
                # Display analysis results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Code Analysis")
                    if "complexity" in analysis:
                        st.metric("Complexity Score", analysis["complexity"])
                    
                    if "issues" in analysis and analysis["issues"]:
                        st.error("Issues Found:")
                        for issue in analysis["issues"]:
                            st.write(f"- {issue}")
                    else:
                        st.success("No issues found!")
                
                with col2:
                    st.subheader("Improvement Suggestions")
                    if "suggestions" in analysis and analysis["suggestions"]:
                        for suggestion in analysis["suggestions"]:
                            st.info(suggestion)
                    
                    st.write(suggestions)
                
                # Add to user history
                user_profile_manager.add_history_entry(
                    st.session_state.user_id, 
                    "analyze_code", 
                    {"code": code, "analysis": analysis, "suggestions": suggestions}
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Documentation Generator Page
elif page == "Documentation":
    st.title("Documentation Generator")
    
    # Use the code from the editor or allow new input
    use_editor_code = st.checkbox("Use code from editor", value=True)
    
    if use_editor_code and st.session_state.code:
        code = st.session_state.code
        language = st.session_state.language
        st.code(code, language=language)
    else:
        language = st.selectbox(
            "Language",
            ["Python", "JavaScript", "Java", "C++", "Go"],
            index=["python", "javascript", "java", "c++", "go"].index(st.session_state.language)
            if st.session_state.language in ["python", "javascript", "java", "c++", "go"] else 0
        )
        code = st.text_area("Enter code to document:", height=300)
    
    if st.button("Generate Documentation") and code:
        with st.spinner("Generating documentation..."):
            try:
                # Generate documentation using Gemini service
                documentation = gemini_service.generate_documentation(code, language.lower())
                
                st.subheader("Generated Documentation")
                st.markdown(documentation)
                
                # Option to download documentation
                doc_filename = f"documentation_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
                st.download_button(
                    label="Download Documentation",
                    data=documentation,
                    file_name=doc_filename,
                    mime="text/markdown"
                )
                
                # Add to user history
                user_profile_manager.add_history_entry(
                    st.session_state.user_id, 
                    "generate_documentation", 
                    {"code": code, "documentation": documentation}
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Test Generator Page
elif page == "Test Generator":
    st.title("Test Case Generator")
    
    # Use the code from the editor or allow new input
    use_editor_code = st.checkbox("Use code from editor", value=True)
    
    if use_editor_code and st.session_state.code:
        code = st.session_state.code
        language = st.session_state.language
        st.code(code, language=language)
    else:
        language = st.selectbox(
            "Language",
            ["Python", "JavaScript", "Java", "C++", "Go"],
            index=["python", "javascript", "java", "c++", "go"].index(st.session_state.language)
            if st.session_state.language in ["python", "javascript", "java", "c++", "go"] else 0
        )
        code = st.text_area("Enter code to generate tests for:", height=300)
    
    if st.button("Generate Test Cases") and code:
        with st.spinner("Generating test cases..."):
            try:
                # Generate test cases using Gemini service
                test_cases = gemini_service.generate_test_cases(code, language.lower())
                
                st.subheader("Generated Test Cases")
                st.code(test_cases, language=language.lower())
                
                # Option to download test cases
                file_extension = {
                    "python": "py",
                    "javascript": "js",
                    "java": "java",
                    "c++": "cpp",
                    "go": "go"
                }.get(language.lower(), language.lower())
                
                test_filename = f"tests_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_extension}"
                st.download_button(
                    label="Download Test Cases",
                    data=test_cases,
                    file_name=test_filename,
                    mime=f"text/{language.lower()}"
                )
                
                # Add to user history
                user_profile_manager.add_history_entry(
                    st.session_state.user_id, 
                    "generate_test_cases", 
                    {"code": code, "test_cases": test_cases}
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Voice Coding Page
elif page == "Voice Coding":
    st.title("Voice Coding Assistant")
    st.write("Record your voice to get coding assistance")
    
    # File uploader for audio file
    audio_file = st.file_uploader("Upload audio file", type=["wav", "mp3"])
    
    if audio_file is not None:
        st.audio(audio_file, format="audio/wav")
        
        if st.button("Process Voice Command"):
            with st.spinner("Processing voice command..."):
                try:
                    # Process audio using speech recognizer
                    text = speech_recognizer.transcribe(audio_file)
                    
                    # Get user context
                    user_context = user_profile_manager.get_user_context(st.session_state.user_id)
                    
                    # Generate response using Gemini service
                    response = gemini_service.generate_code_response(text, user_context)
                    
                    st.subheader("Transcribed Text")
                    st.write(text)
                    
                    st.subheader("AI Response")
                    st.write(response)
                    
                    # Add to user history
                    user_profile_manager.add_history_entry(
                        st.session_state.user_id, 
                        "voice_coding", 
                        {"text": text, "response": response}
                    )
                except Exception as e:
                    st.error(f"Error processing voice command: {str(e)}")
    
    st.info("You can ask questions about coding, request code examples, or ask for explanations using your voice.")

# User History Section (can be added as a separate page)
if st.sidebar.checkbox("Show User History"):
    st.sidebar.subheader("Recent Activity")
    user_context = user_profile_manager.get_user_context(st.session_state.user_id)
    history = user_context.get("history", [])
    
    if history:
        for entry in history[-5:]:  # Show last 5 entries
            timestamp = entry.get("timestamp", "")
            entry_type = entry.get("type", "")
            st.sidebar.text(f"{timestamp[:10]} - {entry_type}")
    else:
        st.sidebar.text("No activity yet")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <p>Built with Streamlit and AI coding assistance</p>
    </div>
    """,
    unsafe_allow_html=True
)