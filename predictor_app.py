import streamlit as st
import os
from dotenv import load_dotenv
from model import FactCheckerRAG

# Load environment variables from .env file
load_dotenv()

# Streamlit App Configuration
st.set_page_config(page_title="Fake News Detector", page_icon="📰", layout="wide")

st.title("📰 Real-Time Fake News Detector")
st.write("Detect if a news article or social media post is **Fake** or **Real** using dynamic web retrieval and AI analysis.")

# Retrieve API key from environment
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    # Initialize the Fact checker
    fact_checker = FactCheckerRAG(api_key=api_key)
    
    # Text input
    st.markdown("---")
    text = st.text_area("Paste the news content or claim below 👇", height=150)

    # Predict button
    if st.button("Analyze Claim"):
        if text.strip():
            with st.spinner("Retrieving facts & analyzing..."):
                result = fact_checker.analyze_claim(text)
                
                cred = str(result.get("credibility", "Error"))
                cred_lower = cred.lower()
                
                # Dynamic banner based on the resulting credibility
                if any(word in cred_lower for word in ["real", "true", "verified", "correct"]):
                    st.success(f"### 🧾 Assessment: {cred} ✅")
                elif any(word in cred_lower for word in ["fake", "false", "incorrect"]):
                    st.error(f"### ⚠️ Assessment: {cred} ❌")
                elif any(word in cred_lower for word in ["mixed", "unverified"]):
                    st.warning(f"### 🤔 Assessment: {cred}")
                else:
                    st.info(f"### ℹ️ Assessment: {cred}")

                # Display additional metadata
                st.write(f"**Confidence Score:** {result.get('confidence_score', 0)}")
                
                # Display the Summary Context
                st.subheader("Analysis Summary")
                summary = result.get("summary_points") or result.get("summary", ["No analysis summary provided by the model."])
                
                if isinstance(summary, list):
                    for point in summary:
                        st.markdown(f"- {point}")
                else:
                    st.write(summary)
                
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
    st.error("⚠️ GEMINI_API_KEY not found. Please create a `.env` file and add your `GEMINI_API_KEY`.")
