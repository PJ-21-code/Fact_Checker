import streamlit as st
from transformers import pipeline

st.title("📰 Fake News Detector")
st.write("Detect fake or real news using BERT")

pipe = pipeline("text-classification", model="YerayEsp/FakeBerta", trust_remote_code=True)

text = st.text_area("Enter news text:")
if st.button("Detect"):
    result = pipe(text)[0]
    label = result['label']
    score = result['score']
    label = "🟢 Real News" if "REAL" in label.upper() else "🔴 Fake News"
    st.write(f"**{label}** (Confidence: {score:.2f})")
