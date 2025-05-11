import streamlit as st
import boto3
from dotenv import load_dotenv
import os
import json
import requests
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

modelID_templete = 'anthropic.claude-3-5-haiku-20241022-v1:0'

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)

# Weather API configuration
WEATHER_API_KEY = "d961cef0211049fdb3d03915251105"
WEATHER_API_BASE_URL = "https://api.weatherapi.com/v1"  # Changed to https

def get_weather_data(location, start_date, end_date):
    """Fetch weather data for a location and date range"""
    try:
        # Convert dates to datetime objects
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = min((end - start).days + 1, 14)
        
        # Get weather forecast
        params = {
            'key': WEATHER_API_KEY,
            'q': location,
            'days': days,
            'aqi': 'no'
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
            print("Data successfually getted")
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
    /* Fix input field colors */
    .stTextInput>div>div>input {
        color: black !important;
        background-color: white !important;
        caret-color: black !important;  /* Makes cursor visible */
    }
    .stTextArea>div>div>textarea {
        color: black !important;
        background-color: white !important;
        caret-color: black !important;  /* Makes cursor visible */
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
        color: white;
    }
    .chat-message.assistant {
        background-color: #f0f2f6;
        color: black !important;  /* Ensures text is visible */
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
        caret-color: black !important;  /* Makes cursor visible */
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
</style>
""", unsafe_allow_html=True)

# Title
st.title("🧳 Travel Packing Assistant")
st.markdown("---")

# Trip Information Form
with st.expander("Enter Trip Details", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input("Destination (e.g., 'London, UK' or 'New York, USA')")
        start_date = st.date_input("Start Date")
    with col2:
        activities = st.text_area("Planned Activities (one per line)")
        end_date = st.date_input("End Date")
    
    if st.button("Generate Packing List"):
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
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"""<div class="packing-list">
                        Here's your personalized packing list based on the weather forecast and your activities:
                        
                        {packing_list}
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
