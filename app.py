import streamlit as st
from together import Together
import fitz  # PyMuPDF
import time
import csv
import io
import os

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
def chunk_text(text, chunk_size=250):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

# ----------------- UI -------------------
st.set_page_config(page_title="PDF → Flashcards & Quiz", layout="wide")
st.title("📘 PDF to Flashcards & Practice Quiz")



uploaded_pdf = st.file_uploader("📄 Upload a PDF of notes:", type="pdf")

if uploaded_pdf and api_key:
    with st.spinner("Extracting text..."):
        text = extract_text_from_pdf(uploaded_pdf)
        chunks = chunk_text(text)

    flashcards = []
    quiz_questions = []

    if st.button("✨ Generate Flashcards and Questions"):
        with st.spinner("Calling Together.ai and generating content..."):
            for i, chunk in enumerate(chunks):
                prompt = f"From the following notes, devise 25 multiple choice questions with the answer choices in bullet points. Do not show answers. Include all chunks. Notes:\n{chunk}"
                result = call_together_ai(api_key, prompt)
                flashcards.append((chunk, result))
                time.sleep(1.5)  # throttle to avoid hitting rate limit

        st.success("Done generating content!")

        # Optionally display results
        st.header("🧠 Flashcards & Questions Preview")
        for i, (chunk, content) in enumerate(flashcards):
            st.subheader(f"Chunk {i+1}")
            st.markdown(content)

        # Allow CSV export
        if st.button("📥 Download as CSV"):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Chunk", "Generated Content"])
            for chunk, content in flashcards:
                writer.writerow([chunk, content])
            st.download_button("Download CSV", data=output.getvalue(), file_name="flashcards.csv", mime="text/csv")
    if st.button ("Generate Groupings/Mind Map Ideas"):
        with st.spinner("Calling Together.ai and generating content..."):
            chunkList=[]
            for i, chunk in enumerate(chunks):
                chunkList.append(chunk)
            prompt=f"From the following notes, place everything into key groups and explain their connection in depth. Aim for 6-7 terms per group and pay attention to headers in the text to make judgements. Notes:\n{chunkList}"
            result = call_together_ai(api_key, prompt)
            st.header("🧠 Flashcards & Questions Preview")
            st.subheader(f"Groupings")
            st.markdown(result)

else:
    st.warning("Please upload a PDF and enter your API key.")