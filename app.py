import streamlit as st
import google.generativeai as genai
import requests
from PIL import Image
import io
import os
import json
from datetime import datetime
import re  # Import re for emoji stripping

# Configure API keys
GEMINI_API_KEY = "AIzaSyBqVy-aaD1KRUtTN2i4TiqDsFgLLY3FA2s"
WEATHER_API_KEY = "606de568beb36a59ed1be29e162c0f57"

# Initialize Gemini client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# Function to fetch weather data with debugging
def get_weather(location):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Could not fetch weather data. Status code: {response.status_code}")
        return None


# Function to analyze images (plants/pests) using Gemini
def analyze_image(image, query, previous_context=""):
    try:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format)
        img_byte_arr = img_byte_arr.getvalue()

        prompt = f"Previous context: {previous_context}. Analyze this image. If it's a plant, provide its scientific name, common uses, optimal growing conditions (soil, light, water), and care tips. If it's a pest, identify it and suggest control methods. User query: '{query}'"

        response = model.generate_content(
            [prompt, {"inline_data": {"mime_type": f"image/{image.format.lower()}", "data": img_byte_arr}}],
            generation_config={"max_output_tokens": 500}
        )
        # Strip any emojis and prepend plant emoji
        text_without_emoji = re.sub(r'[^\w\s.,!?]', '', response.text)  # Remove emojis and special characters
        return f"🌱 {text_without_emoji}"
    except Exception as e:
        st.error(f"Error analyzing image: {e}")
        return "Sorry, there was an issue analyzing the image."


# Function to get gardening advice from Gemini with context and plant details
def get_gardening_advice(user_input, location, previous_context=""):
    weather_data = get_weather(location)
    if weather_data is None:
        return "Error fetching weather data."

    context_str = f"Previous context: {previous_context}" if previous_context else "No previous context."
    prompt = f"{context_str} Based on weather in {location} (temp: {weather_data['main']['temp']}C, humidity: {weather_data['main']['humidity']}%), and the user query: '{user_input}', provide concise and clear gardening advice."

    try:
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 500}
        )
        # Strip any emojis and prepend plant emoji
        text_without_emoji = re.sub(r'[^\w\s.,!?]', '', response.text)  # Remove emojis and special characters
        return f"🌱 {text_without_emoji}"
    except Exception as e:
        st.error(f"Error generating advice: {e}")
        return "Sorry, there was an issue processing your request."


# User login and data management
def load_user_data(email):
    if os.path.exists(f"user_data_{email}.json"):
        with open(f"user_data_{email}.json", "r") as f:
            return json.load(f)
    return {"messages": [], "location": "", "context": ""}


def save_user_data(email, data):
    with open(f"user_data_{email}.json", "w") as f:
        json.dump(data, f)


# Streamlit UI
st.set_page_config(page_title="Garden Planner", page_icon="🌱", layout="wide")

# Dynamic background based on login state
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    background_url = "https://wallpaperaccess.com/full/704428.jpg"  # Login background
else:
    background_url = "https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIzLTExL3Jhd3BpeGVsX29mZmljZV8zNF9hX3Bob3RvX29mX19zZWVkX2dyb3dpbmdfc3RlcHNfXzNhODBhNzM0LWEzMzUtNDIzNi04ZWI0LTkyYWMxMzBmYjIxMV8xLmpwZw.jpg"  # Main page background

st.markdown(f"""
    <style>
        /* MAIN BACKGROUND FIX */
        [data-testid="stAppViewContainer"] {{
            background-image: url('{background_url}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Make the app container transparent */
        .stApp {{
            background-color: transparent !important;
        }}

        /* ALL TEXT WHITE WITH SHADOW */
        h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stChatMessage {{
            color: white !important;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
        }}

        /* SIDEBAR - BLACK TRANSPARENT BACKGROUND */
        .stSidebar {{
            background-color: rgba(0, 0, 0, 0.7) !important;
            border-radius: 15px;
            padding: 20px;
            margin: 10px;
            border: 1px solid #4CAF50;
        }}

        /* ABOUT CONTAINER - BLACK TRANSPARENT BACKGROUND */
        .about-container {{
            background-color: rgba(0, 0, 0, 0.7) !important;
            border-radius: 15px;
            padding: 20px;
            margin: 10px;
            border: 1px solid #4CAF50;
        }}

        /* CHAT AREA - BLACK TRANSPARENT BACKGROUND */
        .stChatMessage {{
            background-color: rgba(0, 0, 0, 0.7) !important;
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid #4CAF50;
        }}

        /* INPUT FIELDS */
        .stTextInput, .stTextArea {{
            background-color: rgba(0, 0, 0, 0.8) !important;
            border: 2px solid #4CAF50 !important;
        }}

        /* INPUT TEXT WHITE */
        .stTextInput input, .stTextArea textarea {{
            color: white !important;
        }}

        /* LABELS */
        .stTextInput label p, .stTextArea label p, .stFileUploader label p {{
            color: white !important;
            background-color: rgba(0, 0, 0, 0.7) !important;
            padding: 5px 10px !important;
            border-radius: 5px !important;
            display: inline-block !important;
        }}

        /* BUTTONS */
        .stButton>button {{
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
        }}

        /* FOOTER */
        footer {{
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.7);
        }}

        /* CENTER THE TITLE */
        h1 {{
            text-align: center !important;
        }}

    </style>
""", unsafe_allow_html=True)

# Main content
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Login Page
    st.title("🌱Garden Planner")

    col1, col2 = st.columns(2)

    with col1:
        # About GardenAI section with black transparent background
        with st.container():
            st.markdown("""
                <div class="about-container">
                    <h2>About Garden Planner</h2>
                    <p>Welcome to Garden Planner, your personal gardening assistant! Powered by advanced AI and real-time weather data, GardenAI helps you with:</p>
                    <ul>
                        <li>Plant care tips and identification</li>
                        <li>Pest control advice</li>
                        <li>Optimal growing conditions based on your location</li>
                        <li>Continuous chat support for a seamless experience</li>
                    </ul>
                    <p>Let us help you grow your green thumb!</p>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        # Login/Sign Up section without container
        st.markdown("## Login or Sign Up")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login/Sign Up"):
            if email and password:
                st.session_state.email = email
                st.session_state.logged_in = True
                st.session_state.messages = []
                st.session_state.location = "London"
                st.session_state.context = ""
                st.rerun()

    # Footer
    st.markdown("""
    <footer>
        Created by Naga Srinivasa Reddy, David, Shashank. Grow greener with GardenAI!
    </footer>
    """, unsafe_allow_html=True)

else:
    # Main App Page
    with st.sidebar:
        st.subheader("Your Garden Settings")
        location = st.text_input("Your Location", st.session_state.location)
        st.session_state.location = location

        if location:
            weather_data = get_weather(location)
            if weather_data:
                st.write(f"**Current Weather in {location}:**")
                st.write(f"Temperature: {weather_data['main']['temp']}°C")
                st.write(f"Humidity: {weather_data['main']['humidity']}%")
                st.write(f"Conditions: {weather_data['weather'][0]['description']}")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🌱Garden Planner")
    st.subheader("Need help in Gardening? Upload your photo or ask your question!")

    # Display chat history
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Input area
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Type your message...", key="chat_input")
    with col2:
        uploaded_file = st.file_uploader("Upload image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

    if st.button("Send"):
        if not location:
            st.error("Please enter your location")
        else:
            current_context = st.session_state.context or ""

            if uploaded_file:
                image = Image.open(uploaded_file)
                with st.chat_message("user"):
                    st.image(image, caption="Uploaded Image", use_column_width=True)
                    st.write(query if query else "Please analyze this image")

                with st.chat_message("assistant"):
                    advice = analyze_image(image, query if query else "", current_context)
                    st.write(f"🌱 {advice}")  # Ensure plant emoji is used, stripping any existing emojis
                st.session_state.messages.append({"role": "user", "content": query or "Image uploaded"})
                st.session_state.messages.append({"role": "assistant", "content": advice})
                st.session_state.context = f"Last topic: {query or 'image analysis'}"

            elif query:
                with st.chat_message("user"):
                    st.write(query)

                with st.chat_message("assistant"):
                    advice = get_gardening_advice(query, location, current_context)
                    st.write(f"🌱 {advice}")  # Ensure plant emoji is used, stripping any existing emojis
                st.session_state.messages.append({"role": "user", "content": query})
                st.session_state.messages.append({"role": "assistant", "content": advice})
                st.session_state.context = f"Last topic: {query}"

            save_user_data(st.session_state.email, {
                "messages": st.session_state.messages,
                "location": location,
                "context": st.session_state.context
            })
            st.rerun()

    # Footer
    st.markdown("""
    <footer>
        Created by Naga Srinivasa Reddy, David, Shashank. Grow greener with GardenAI!
    </footer>
    """, unsafe_allow_html=True)