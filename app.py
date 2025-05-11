import streamlit as st
import boto3
from dotenv import load_dotenv
import os
import json
import requests
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Get AWS credentials from Streamlit secrets
AWS_ACCESS_KEY_ID = st.secrets["aws"]["aws_access_key_id"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["aws_secret_access_key"]
AWS_REGION = st.secrets["aws"]["aws_region"]
AWS_SESSION_TOKEN = st.secrets["aws"].get("aws_session_token", None)  # Optional session token

# Get Weather API key from secrets
WEATHER_API_KEY = st.secrets["weather_api"]["api_key"]
WEATHER_API_BASE_URL = "https://api.weatherapi.com/v1"  # Changed to https

# Configure AWS Bedrock
modelID_templete = 'anthropic.claude-3-5-haiku-20241022-v1:0'

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN if AWS_SESSION_TOKEN else None
)

def get_weather_data(location, start_date, end_date):
    """Fetch weather data for a location and date range"""
    try:
        # Convert dates to datetime objects
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate number of days
        days = (end - start).days + 1
        
        # Get weather forecast
        params = {
            'key': WEATHER_API_KEY,
            'q': location,
            'days': days,  # Number of days of forecast
            'aqi': 'no',
            'alerts': 'no'
        }
        
        # Add timeout and verify SSL
        response = requests.get(
            f"{WEATHER_API_BASE_URL}/forecast.json",
            params=params,
            timeout=50,
            verify=True
        )
        
        # Check if the response is successful
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Weather API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Weather API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"API Response: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def generate_packing_list(weather_data, activities, stay_period):
    """Generate a packing list based on weather data and activities"""
    try:
        # Prepare the prompt for Claude
        prompt = f"""Based on the following information, generate a detailed packing list:
        
        Weather Data: {json.dumps(weather_data)}
        Activities: {activities}
        Stay Period: {stay_period} days
        
        Please provide a comprehensive packing list that includes:
        1. Essential clothing based on the weather forecast
        2. Activity-specific items
        3. General travel essentials
        4. Any weather-specific items (umbrella, sunscreen, etc.)
        
        Format the response as a clear, organized list with categories."""
        
        # Prepare the request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Call Bedrock
        response = bedrock.invoke_model(
            modelId=modelID_templete,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        st.error(f"Error generating packing list: {str(e)}")
        return None

def generate_daily_routines(weather_data, activities, stay_period):
    """Generate daily routines based on weather data and activities"""
    try:
        # Prepare the prompt for Claude
        prompt = f"""Based on the following information, generate a daily routine for each day of the stay:
        
        Weather Data: {json.dumps(weather_data)}
        Activities: {activities}
        Stay Period: {stay_period} days
        
        Please provide a detailed daily routine that includes:
        1. Best times for outdoor activities based on weather
        2. Indoor activities for bad weather days
        3. Local spots and attractions to visit
        4. Suggested meal times and locations
        5. Transportation recommendations
        
        Format the response as a day-by-day schedule with specific times and locations."""
        
        # Prepare the request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Call Bedrock
        response = bedrock.invoke_model(
            modelId=modelID_templete,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        st.error(f"Error generating daily routines: {str(e)}")
        return None

def generate_recommended_spots(weather_data, activities, stay_period):
    """Generate recommended visit spots based on weather data and activities"""
    try:
        # Prepare the prompt for Claude
        prompt = f"""Based on the following information, generate a list of recommended spots to visit each day:
        
        Weather Data: {json.dumps(weather_data)}
        Activities: {activities}
        Stay Period: {stay_period} days
        
        Please provide:
        1. A list of recommended spots for each day
        2. Best times to visit each spot based on weather
        3. Brief description of each spot
        4. Why these spots are recommended based on the activities and weather
        
        Format the response as a day-by-day schedule with specific spots and times."""
        
        # Prepare the request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Call Bedrock
        response = bedrock.invoke_model(
            modelId=modelID_templete,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        st.error(f"Error generating recommended spots: {str(e)}")
        return None

# Set page config
st.set_page_config(
    page_title="Travel Packing Assistant",
    page_icon="🧳",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "trip_info" not in st.session_state:
    st.session_state.trip_info = {
        "destination": None,
        "start_date": None,
        "end_date": None,
        "activities": None
    }

# Custom CSS for better UI
st.markdown("""
<style>
    /* Global background and text */
    .stApp {
        background-color: white !important;
    }
    
    /* Global text color */
    * {
        color: black !important;
    }
    
    /* Title styling */
    h1 {
        text-align: center !important;
        font-size: 3rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Fix input field colors */
    .stTextInput>div>div>input {
        color: black !important;
        background-color: white !important;
        caret-color: black !important;
    }
    .stTextArea>div>div>textarea {
        color: black !important;
        background-color: white !important;
        caret-color: black !important;
    }
    /* Chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
        color: white !important;
    }
    .chat-message.assistant {
        background-color: #f0f2f6;
        color: black !important;
    }
    .chat-message .avatar {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    /* Form styling */
    .stDateInput>div>div>input {
        color: black !important;
        background-color: white !important;
        caret-color: black !important;
    }
    /* Make sure all text in the app is visible */
    .stMarkdown {
        color: black !important;
    }
    /* Style for the packing list */
    .packing-list {
        color: black !important;
        background-color: white !important;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    /* Date inputs container */
    .date-inputs {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    .date-inputs > div {
        flex: 1;
    }
    /* Labels and text */
    label {
        color: black !important;
    }
    .stButton>button {
        color: black !important;
    }
    .stExpander {
        color: black !important;
    }
    .streamlit-expanderHeader {
        color: black !important;
    }
    /* Chat input */
    .stChatInput>div>div>textarea {
        color: black !important;
    }
    /* Warning messages */
    .stAlert {
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🧳 Carry Buddy ✈️")
st.markdown("---")

# Trip Information Form
with st.expander("📝 Enter Trip Details", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input("🌍 Destination (e.g., 'London, UK' or 'New York, USA')")
    with col2:
        activities = st.text_area(
            "🎯 Planned Activities",
            placeholder="Enter one activity per line:\n- Sightseeing\n- Beach\n- Hiking\n- Shopping",
            help="List each activity on a new line"
        )
    
    # Date inputs in a single row
    st.markdown('<div class="date-inputs">', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        start_date = st.date_input("📅 Start Date", min_value=datetime.now().date())
    with col4:
        end_date = st.date_input("📅 End Date", min_value=datetime.now().date())
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("✨ Generate Packing List"):
        if destination and start_date and end_date and activities:
            # Validate date range
            stay_period = (end_date - start_date).days + 1
            if stay_period > 3:
                st.error("⚠️ Please select a stay period of 3 days or less")
            else:
                # Update trip info
                st.session_state.trip_info = {
                    "destination": destination,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "activities": activities
                }
                
                # Get weather data
                with st.spinner("Fetching weather data..."):
                    weather_data = get_weather_data(
                        destination,
                        st.session_state.trip_info["start_date"],
                        st.session_state.trip_info["end_date"]
                    )
                
                if weather_data:
                    # Generate packing list
                    with st.spinner("Generating packing list..."):
                        packing_list = generate_packing_list(
                            weather_data,
                            activities,
                            stay_period
                        )
                    
                    if packing_list:
                        # Generate recommended spots
                        with st.spinner("Generating recommended spots..."):
                            recommended_spots = generate_recommended_spots(
                                weather_data,
                                activities,
                                stay_period
                            )
                        
                        if recommended_spots:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"""<div class="packing-list">
                                Here's your personalized packing list based on the weather forecast and your activities:
                                
                                {packing_list}
                                </div>"""
                            })
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"""<div class="packing-list">
                                Here are your recommended spots to visit each day:
                                
                                {recommended_spots}
                                </div>"""
                            })
                            st.rerun()
        else:
            st.warning("Please fill in all fields to generate a packing list.")

# Display chat messages
for message in st.session_state.messages:
    with st.container():
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user">
                <div style="display: flex; align-items: center;">
                    <div class="avatar">👤</div>
                    <div>You</div>
                </div>
                <div style="margin-left: 2rem;">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant">
                <div style="display: flex; align-items: center;">
                    <div class="avatar">🤖</div>
                    <div>Assistant</div>
                </div>
                <div style="margin-left: 2rem;">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

# Chat input for additional questions
if prompt := st.chat_input("Ask about your packing list..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        # Prepare the messages for Bedrock
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        
        # Add context about the trip
        if st.session_state.trip_info["destination"]:
            context = f"\nContext: The user is traveling to {st.session_state.trip_info['destination']} from {st.session_state.trip_info['start_date']} to {st.session_state.trip_info['end_date']}. Planned activities: {st.session_state.trip_info['activities']}"
            messages.append({"role": "system", "content": context})
        
        # Prepare the request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": messages,
            "temperature": 0.7
        }
        
        # Call Bedrock
        response = bedrock.invoke_model(
            modelId=modelID_templete,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        assistant_response = response_body['content'][0]['text']
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        # Rerun to update the chat display
        st.rerun()
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please make sure you have set up your AWS credentials in the .env file.") 
