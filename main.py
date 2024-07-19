import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompts
summary_prompt = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 250 words. Please provide the summary of the text given here: """

fact_check_prompt = """You are to fact-check the information I have given here. Check if it is valid and
 give the appropriate response. Also, if fact-checking is not possible for the given text, 
 give the proper reason for the same: """

query_prompt = """You are an assistant who answers questions based on the provided transcript of a YouTube video. Here is the transcript:
{transcript}
Now, please answer the following question: {question}. If the question is not answerable from the transcript then answer off the internet.
Don't use the word transcript instead use video. Act like a chatbot in that scenario:"""

def extract_video_id(youtube_url):
    video_id = None
    regex_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)'
    ]
    for pattern in regex_patterns:
        match = re.match(pattern, youtube_url)
        if match:
            video_id = match.group(1)
            break
    return video_id

def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([i["text"] for i in transcript_text])
        return transcript
    except Exception as e:
        st.error(f"Error extracting transcript: {e}")
        return None

def generate_gemini_content(prompt, transcript_text):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating content: {e}")
        return None

def generate_query_response(transcript_text, question):
    try:
        prompt = query_prompt.format(transcript=transcript_text, question=question)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating content: {e}")
        return None

st.title("YouTube Video Summarizer and Fact-Checker")

# Session state initialization
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'fact_check' not in st.session_state:
    st.session_state.fact_check = None
if 'fact_check_enabled' not in st.session_state:
    st.session_state.fact_check_enabled = False
if 'queries' not in st.session_state:
    st.session_state.queries = []

youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    video_id = extract_video_id(youtube_link) 
    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", width=400, use_column_width=False, caption="YouTube Video Thumbnail")

if st.button("Get Detailed Notes"):
    if youtube_link:
        st.session_state.transcript_text = extract_transcript_details(youtube_link)

        if st.session_state.transcript_text:
            st.session_state.summary = generate_gemini_content(summary_prompt, st.session_state.transcript_text)
            st.session_state.fact_check_enabled = True

# Display the summary if it exists
if st.session_state.summary:
    st.markdown("## Detailed Notes:")
    st.write(st.session_state.summary)

# Fact Check button
if st.session_state.fact_check_enabled:
    if st.button("Fact Check"):
        st.session_state.fact_check = generate_gemini_content(fact_check_prompt, st.session_state.summary)

# Display fact check response if it exists
if st.session_state.fact_check:
    st.markdown("## Fact Check Response:")
    st.write(st.session_state.fact_check)

# Ask Query section
if st.session_state.transcript_text:
    st.subheader("Ask further doubts or queries about the video:")
    user_query = st.text_input("Type your query here:", key='user_query')
    
    if st.button("Ask"):
        if user_query:
            query_response = generate_query_response(st.session_state.transcript_text, user_query)
            st.session_state.queries.append((user_query, query_response))
        else:
            st.warning("Please type your query first.")

# Display all queries and responses
if st.session_state.queries:
    st.markdown("## Queries and Responses:")
    for i, (query, response) in enumerate(st.session_state.queries, start=1):
        st.markdown(f"*Query {i}:* {query}")
        st.write(response)