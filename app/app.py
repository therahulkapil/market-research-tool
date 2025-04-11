import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Business Report Generator", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .title {
        font-size: 42px;
        font-weight: bold;
        margin-bottom: 20px;
        color: #1E3A8A;
        text-align: center;
    }
    .subtitle {
        font-size: 24px;
        margin-bottom: 20px;
        color: #1E3A8A;
        text-align: center;
    }
    .report-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        background-color: #f9f9f9;
        margin-top: 20px;
        min-height: 300px;
    }
    .section-header {
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        color: #1E3A8A;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='title'>Business Report Generator</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Generate comprehensive business reports with AI</div>", unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.header("Settings")
    
    # Company name input
    company_name = st.text_input("Company Name", help="Enter the name of the company to generate a report for")
    
    # Report topics selection
    st.subheader("Report Topics")
    business_overview = st.checkbox("Business Overview", value=True)
    financial_analysis = st.checkbox("Financial Analysis")
    recent_news_announcements = st.checkbox("Recent News and Announcements")
    competitive_analysis = st.checkbox("Competitive Analysis")
    swot_analysis = st.checkbox("SWOT Analysis")
    risk_assessment = st.checkbox("Risk Assessment")
    
    # API endpoint
    api_endpoint = st.text_input("API Endpoint", value="http://localhost:8000/generate_report_stream")
    
    # Generate button
    generate_button = st.button("Generate Report", type="primary", disabled=not company_name)
    
    # About section
    st.sidebar.markdown("---")
    st.sidebar.subheader("About")
    st.sidebar.info(
        "This tool uses AI to generate business reports on the fly. "
        "Simply enter a company name, select the desired report sections, "
        "and click 'Generate Report'."
    )

# Main content area
if 'report_content' not in st.session_state:
    st.session_state.report_content = {}

# Function to collect selected topics
def get_selected_topics():
    topics = []
    if business_overview:
        topics.append("business_overview")
    if financial_analysis:
        topics.append("financial_analysis")
    if recent_news_announcements:
        topics.append("recent_news_announcements")
    if competitive_analysis:
        topics.append("competitive_analysis")
    if swot_analysis:
        topics.append("swot_analysis")
    if risk_assessment:
        topics.append("risk_assessment")
    return topics

# Function to stream from API
def stream_report(topic):
    try:
        payload = {
            "company_name": company_name,
            "topic": [topic]
        }
        
        with requests.post(api_endpoint, json=payload, stream=True) as response:
            if response.status_code == 200:
                content = ""
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        content += chunk.decode('utf-8')
                        # Update the placeholder with the accumulated content
                        st.session_state.report_content[topic] = content
                        placeholder = placeholders[topic]
                        placeholder.markdown(content)
                        time.sleep(0.1)  # Small delay to make streaming visible
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Generate the report when button is clicked
if generate_button:
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        topics = get_selected_topics()
        if not topics:
            st.warning("Please select at least one report topic.")
        else:
            # Create a container for the report
            report_container = st.container()
            
            with report_container:
                st.markdown(f"<div class='section-header'>Report for {company_name}</div>", unsafe_allow_html=True)
                
                # Create a placeholder for each selected topic
                placeholders = {}
                for topic in topics:
                    # Create a nice header for each section
                    topic_title = topic.replace('_', ' ').title()
                    st.markdown(f"<div class='section-header'>{topic_title}</div>", unsafe_allow_html=True)
                    
                    # Create a placeholder for the content
                    placeholders[topic] = st.empty()
                    
                    # Initialize the content in session state
                    st.session_state.report_content[topic] = ""
                
                # Generate content for each topic
                for topic in topics:
                    stream_report(topic)
            
            # Add a download button for the report
            report_text = ""
            for topic in topics:
                topic_title = topic.replace('_', ' ').title()
                report_text += f"# {topic_title}\n\n"
                report_text += st.session_state.report_content.get(topic, "") + "\n\n"
            
            st.download_button(
                label="Download Report",
                data=report_text,
                file_name=f"{company_name}_report.md",
                mime="text/markdown"
            )
else:
    # Display an example report or instructions
    st.markdown("""
    <div class='report-container'>
        <h3>How to use this tool:</h3>
        <ol>
            <li>Enter a company name in the sidebar</li>
            <li>Select the report sections you want to generate</li>
            <li>Click "Generate Report" to create your custom business report</li>
            <li>Download the finished report as a markdown file</li>
        </ol>
        <p>The AI will analyze the company and generate a comprehensive report based on your selections.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Powered by GPT-4o-mini API • Created with Streamlit")