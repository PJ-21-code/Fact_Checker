import streamlit as st
from model import FactCheckerRAG

# Streamlit App Configuration
st.set_page_config(page_title="Fake News Detector", page_icon="📰", layout="wide")

st.title("📰 Real-Time Fake News Detector (RAG + Gemini)")
st.write("Detect if a news article or social media post is **Fake** or **Real** using dynamic web retrieval and AI analysis.")

# Need API key for the LLM
api_key = st.text_input("Enter your Google Gemini API Key to proceed:", type="password")

if api_key:
    # Initialize the Fact checker only when API key is available
    fact_checker = FactCheckerRAG(api_key=api_key)
    
    # Text input
    st.markdown("---")
    text = st.text_area("Paste the news content or claim below 👇", height=150)

    # Predict button
    if st.button("Analyze Claim"):
        if text.strip():
            with st.spinner("Retrieving facts & analyzing..."):
                result = fact_checker.analyze_claim(text)
                
                cred = result.get("credibility", "Error")
                
                # Dynamic banner based on the resulting credibility
                if "Real" in cred:
                    st.success(f"### 🧾 Assessment: {cred} ✅")
                elif "Fake" in cred:
                    st.error(f"### ⚠️ Assessment: {cred} ❌")
                elif "Mixed" in cred or "Unverified" in cred:
                    st.warning(f"### 🤔 Assessment: {cred}")
                else:
                    st.error(f"### ❗ Error: {cred}")

                # Display additional metadata
                st.write(f"**Confidence Score:** {result.get('confidence_score', 0)}%")
                
                # Display the Summary Context
                st.subheader("Analysis Summary")
                st.write(result.get("summary", "No summary provided by the model."))
                
                # Display External Sources
                st.subheader("Fact-Check Sources Retrieved")
                sources = result.get("sources", [])
                if sources:
                    for s in sources:
                        # Extract the base URL or valid link properly if needed
                        if s.startswith("http"):
                            st.write(f"- {s}")
                else:
                    st.write("No direct sources were referenced by the model.")
        else:
            st.warning("Please enter some text to analyze.")
else:
    st.info("⚠️ An API Key is required to power the web retrieval and generation engine.")
