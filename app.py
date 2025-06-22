import streamlit as st
from together import Together
import fitz  # PyMuPDF
import time
import csv
import io
import os
st.markdown("""<meta name="robots" content="noindex">""", unsafe_allow_html=True)
if "mode" not in st.session_state:
    st.session_state.mode = "home"

api_key=os.getenv("api_key")

# ----------------- PDF TEXT EXTRACTION -------------------
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

# ----------------- TOGETHER.AI REQUEST (SDK Version) -------------------
def call_together_ai(api_key, prompt):
    client = Together(api_key=api_key)
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[
            {"role": "system", "content": "You are an expert tutor creating flashcards and practice test questions."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024,
        temperature=0.7,
        stream=False  # Set to True for real-time streaming in future
    )
    return response.choices[0].message.content
    

# ----------------- CHUNKING -------------------
def chunk_text(text, chunk_size=1000):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]



# ----------------- UI -------------------
st.set_page_config(page_title="PDF → Flashcards & Quiz", layout="wide")
st.title("📘 PDF to Flashcards & Practice Quiz")



uploaded_pdf = st.file_uploader("📄 Upload a PDF of notes:", type="pdf")

if uploaded_pdf and api_key:
    # Extract and store chunks if not done already
    if "chunks" not in st.session_state:
        text = extract_text_from_pdf(uploaded_pdf)
        st.session_state.chunks = chunk_text(text)

    # Show the 3 main buttons only if no mode is active yet
    if st.session_state.mode == "home":
        if st.button("✨ Generate Practice Quiz Questions"):
            st.session_state.mode = "practice_quiz"
            

        if st.button("Generate Flashcards"):
            st.session_state.mode = "flashcards"

        if st.button("Generate Groupings/Mind Map Ideas"):
            st.session_state.mode = "mind_map"

    # Practice Quiz Mode UI and Logic
    if st.session_state.mode == "practice_quiz":
        st.write("**Practice Quiz Mode Active**")
        with st.spinner("Calling Together.ai and generating content..."):
            flashcards=[]
            for i, chunk in enumerate(st.session_state.chunks):
                prompt = f"From the following notes, devise 10 multiple choice questions with the answer choices in bullet points. Do not show answers. If mathematical concepts are present, please interpret and make the questions math-related (or similar to the questions present), while enclosing mathematical equations in LaTeX format enclosed by dollar signs. However, if math is not present, don't bring it in. Notes:\n{chunk}"
                try:
                    result = call_together_ai(api_key, prompt)
                    flashcards.append(result)
                    # Optional sleep to avoid hitting rate limit
                    time.sleep(1.5)
                except Exception as e:
                    error_str = str(e).lower()
                    if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                        st.error("Rate limit hit — try again shortly or reduce chunk size.")
                        st.stop()
                    else:
                        st.error(f"Unexpected error: {e}")
                        st.stop()
        st.success("Done generating practice questions!")
        

        st.header("🧠 Practice Quiz Preview")
        for idx, content in enumerate(flashcards):
            st.subheader(f"Chunk {idx+1}")
            st.markdown(content)

        # Save to session state if needed
        st.session_state.last_quiz_result = flashcards

        if st.button("⬅️ Back"):
            
            st.session_state.mode = "home"

    # Flashcards Mode UI and Logic
    if st.session_state.mode == "flashcards":
        st.write("**Flashcards Mode Active**")
        with st.spinner("Calling Together.ai and making your flashcards..."):
            mergeList=[]
            flashcards=[]
            for i, chunk in enumerate(st.session_state.chunks):
                prompt=f"From the following notes, give me 10 questions (just the question, do not give multiple choice answers)based on the chunk at hand. Notes:\n{chunk}"
                result=call_together_ai(api_key,prompt)
                mergeList.append(result)
                
                st.header("Flashcards")
                st.markdown(result)
            st.session_state.flashcards=mergeList

        if st.button("⬅️ Back"):
           st.session_state.pop("flashcards", None) 
           st.session_state.mode = "home"
           st.rerun()

    # Mind Map Mode UI and Logic
    if st.session_state.mode == "mind_map":
        if "mind_map" not in st.session_state:
            
            st.write("**Mind Map Mode Active**")
            with st.spinner("Calling Together.ai and generating content..."):
                chunkList=[]
                for i, chunk in enumerate(st.session_state.chunks):
                    chunkList.append(chunk)
                prompt=f"From the following notes, place everything into key groups and explain their connection in depth. Aim for 6-7 terms per group and pay attention to headers in the text to make judgements. Describe all terms and the pages of the groups they are on. Notes:\n{chunkList}"
                result = call_together_ai(api_key, prompt)
                st.session_state.mind_map=result
        else:
      
            st.header("🧠 Grouping and Mind Map Preview")
            st.subheader(f"Groupings")
            st.markdown(st.session_state.mind_map)

            if st.button("⬅️ Back"):
                st.session_state.mode = "home"
                st.session_state.pop("mind_map", None)
                st.experimental_rerun()

else:
    st.warning("Please upload a PDF and enter your API key.")