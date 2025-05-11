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
            modelId='anthropic.claude-3-5-haiku-20241022-v1:0',
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
            modelId='anthropic.claude-3-5-haiku-20241022-v1:0',
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        st.error(f"Error generating daily routines: {str(e)}")
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

# Custom CSS for new UI design
st.markdown("""
<style>
    /* Modern UI Theme */
    :root {
        --primary: #4F46E5;
        --primary-dark: #4338CA;
        --secondary: #10B981;
        --background: #FFFFFF;
        --surface: #FFFFFF;
        --text: #000000;
        --text-light: #000000;
        --border: #E5E7EB;
        --shadow: rgba(0, 0, 0, 0.1);
    }

    /* Global Styles */
    .stApp {
        background-color: var(--background);
    }

    /* Container */
    .main .block-container {
        padding: 3rem 2rem;
        max-width: 1000px;
        margin: 0 auto;
        background-color: var(--background);
    }

    /* Title */
    h1 {
        color: var(--text) !important;
        font-size: 2.75rem !important;
        font-weight: 800 !important;
        text-align: center !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.025em !important;
    }

    /* Subtitle */
    .subtitle {
        color: var(--text) !important;
        font-size: 1.25rem !important;
        text-align: center !important;
        margin-bottom: 3rem !important;
    }

    /* Card Style */
    .card {
        background: var(--surface);
        border-radius: 1rem;
        padding: 2rem;
        box-shadow: 0 4px 6px var(--shadow);
        margin-bottom: 2rem;
    }

    /* Form Elements */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stDateInput>div>div>input {
        background: var(--surface) !important;
        border: 2px solid var(--border) !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1rem !important;
        color: var(--text) !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
    }

    /* Make text area smaller and fixed height */
    .stTextArea>div>div>textarea {
        height: 80px !important;
        min-height: 80px !important;
        max-height: 80px !important;
        resize: none !important;
    }

    /* Ensure date input has fixed height */
    .stDateInput>div>div>input {
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
    }

    /* Force columns to be equal height */
    .row-widget.stHorizontal {
        display: flex !important;
        gap: 2rem !important;
    }

    .row-widget.stHorizontal > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        display: flex !important;
        flex-direction: column !important;
    }

    /* Ensure form elements take full width */
    .stTextInput,
    .stTextArea,
    .stDateInput {
        width: 100% !important;
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stDateInput>div>div>input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
    }

    /* Labels */
    .stTextInput label,
    .stTextArea label,
    .stDateInput label {
        color: var(--text) !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }

    /* Button */
    .stButton>button {
        background: var(--primary) !important;
        color: white !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px var(--shadow) !important;
    }

    .stButton>button:hover {
        background: var(--primary-dark) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 6px var(--shadow) !important;
    }

    /* Chat Messages */
    .chat-message {
        background: var(--surface);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px var(--shadow);
        color: var(--text) !important;
    }

    .chat-message.user {
        background: var(--primary);
        color: white;
        margin-left: 2rem;
    }

    .chat-message.assistant {
        background: var(--surface);
        color: var(--text) !important;
        margin-right: 2rem;
        border: 2px solid var(--border);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--primary) !important;
        color: white !important;
        border-radius: 1rem !important;
        padding: 1.25rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px var(--shadow) !important;
    }

    .streamlit-expanderContent {
        background: var(--surface) !important;
        border-radius: 0 0 1rem 1rem !important;
        padding: 2rem !important;
        margin-top: -0.5rem !important;
        box-shadow: 0 4px 6px var(--shadow) !important;
    }

    /* Chat Input */
    .stChatInput>div>div>textarea {
        background: var(--surface) !important;
        border: 2px solid var(--border) !important;
        border-radius: 0.75rem !important;
        padding: 1rem !important;
        color: var(--text) !important;
    }

    /* Alerts */
    .stAlert {
        border-radius: 0.75rem !important;
        padding: 1rem !important;
        box-shadow: 0 2px 4px var(--shadow) !important;
    }

    /* Spacing */
    .element-container {
        margin-bottom: 1.5rem !important;
    }

    /* Date inputs container */
    .date-inputs {
        display: flex;
        gap: 2rem;
        margin-top: 1rem;
    }
    .date-inputs > div {
        flex: 1;
    }
</style>
""", unsafe_allow_html=True)

# Title and Subtitle
st.title("Carry Buddy")
st.markdown("""
<div class="subtitle">
    Plan your perfect trip with our AI-powered packing assistant
</div>
""", unsafe_allow_html=True)

# Trip Information Form
with st.expander("📝 Trip Details", expanded=True):
    st.markdown("""
    <div style='color: var(--text-light); margin-bottom: 1.5rem;'>
        Tell us about your trip to get a personalized packing list
    </div>
    """, unsafe_allow_html=True)
    
    # First row: Destination and Activities
    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input(
            "🌍 Destination",
            placeholder="e.g., London, UK",
            help="Where are you traveling to?"
        )
    with col2:
        activities = st.text_area(
            "🎯 Activities",
            placeholder="Enter one activity per line\n- Sightseeing\n- Beach\n- Hiking",
            help="What activities do you have planned?"
        )
    
    # Second row: Dates
    st.markdown('<div class="date-inputs">', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        start_date = st.date_input(
            "📅 Start Date",
            help="When does your trip begin?"
        )
    with col4:
        end_date = st.date_input(
            "📅 End Date",
            help="When does your trip end?"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("✨ Generate Packing List & Daily Routine"):
        if destination and start_date and end_date and activities:
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
                # Calculate stay period
                stay_period = (end_date - start_date).days + 1
                
                # Generate packing list
                with st.spinner("Generating packing list..."):
                    packing_list = generate_packing_list(
                        weather_data,
                        activities,
                        stay_period
                    )
                
                if packing_list:
                    # Generate daily routines
                    with st.spinner("Generating daily routines..."):
                        daily_routines = generate_daily_routines(
                            weather_data,
                            activities,
                            stay_period
                        )
                    
                    if daily_routines:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"""Here's your personalized packing list based on the weather forecast and your activities:
                            
                            {packing_list}"""
                        })
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"""Here's your suggested daily routine for each day of your stay:
                            
                            {daily_routines}"""
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
if prompt := st.chat_input("Ask about your packing list or daily routine... (e.g., 'What should I do if it rains?' or 'Can you suggest more indoor activities?')"):
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
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
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
