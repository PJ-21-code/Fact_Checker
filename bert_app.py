import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load model and tokenizer
MODEL_PATH = "./bert_fake_news_model"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

# Title and description
st.title("📰 Fake News Detector (BERT-based)")
st.write("Detect whether a news article or social media post is **Fake** or **Real** using a fine-tuned BERT model.")

# Text input
text = st.text_area("Paste the news content below 👇", height=200)

# Predict button
if st.button("Analyze"):
    if text.strip():
        with st.spinner("Analyzing..."):
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                fake_prob = probs[0][1].item()
                real_prob = probs[0][0].item()

            label = "🧾 Real News ✅" if real_prob > fake_prob else "⚠️ Fake News ❌"
            st.subheader(label)
            st.write(f"**Fake probability:** {fake_prob:.2%}")
            st.write(f"**Real probability:** {real_prob:.2%}")
    else:
        st.warning("Please enter some text to analyze.")
