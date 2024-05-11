import os
import re
import tempfile
import base64
import pandas as pd
import streamlit as st
import seaborn as sns
from openai import OpenAI
from io import BytesIO
from PIL import Image
import plotly.express as px
import speech_recognition as sr
import plotly.graph_objects as go
import plotly.figure_factory as ff
import matplotlib.pyplot as plt
from lida import Manager, TextGenerationConfig, llm
from prompts import get_system_prompt, generate_gpt_response
import psycopg2
import toml

#OPENAI_API_KEY = 'sk-proj-FlppOcEOPJNa4IiiNralT3BlbkFJnmP54NfQYV2l98wGubn5'

# Fetch database configuration from environment variables
DBNAME = os.environ.get('DBNAME')
DBUSER = os.environ.get('DBUSER')
DBPASSWORD = os.environ.get('DBPASSWORD')
DBHOST = os.environ.get('DBHOST')
DBPORT = os.environ.get('DBPORT')
SSL_MODE = os.environ.get('SSL_MODE', 'require')  # Default to 'require' if not specified

# Construct the connection string for PostgreSQL
connection_string = f"""
dbname={DBNAME} user={DBUSER} password={DBPASSWORD} 
host={DBHOST} port={DBPORT} sslmode={SSL_MODE}
"""

# Establish connection to PostgreSQL
def get_sql_connection():
    return psycopg2.connect(connection_string)
print(os.environ.get('OPENAI_API_KEY'))
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
lida = Manager(text_gen = llm("openai", api_key=OPENAI_API_KEY)) # !! api key
textgen_config = TextGenerationConfig(n=1, temperature=0.2, model="gpt-3.5-turbo", use_cache=True)
#textgen_config = TextGenerationConfig(n=1, temperature=0.2, use_cache=True)

def generate_lida_visualization(data_df):
    if data_df is None or data_df.empty:
        st.write("No data available for visualization.")
        return
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
        data_df.to_csv(temp_file.name, index=False)
        summary = lida.summarize(temp_file.name, summary_method="default", textgen_config=textgen_config)
    
    try:
        user_query = "Show data visualization"
        charts = lida.visualize(summary=summary, goal=user_query, textgen_config=textgen_config)

        if charts:
            image_base64 = charts[0].raster
            image = Image.open(BytesIO(base64.b64decode(image_base64)))
            st.image(image, caption="Lida Generated Visualization")
        else:
            st.error("Lida did not generate any charts.")
    finally:
        os.unlink(temp_file.name)

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio_data = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text  
        except sr.UnknownValueError:
            st.write("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            st.write(f"Could not request results from Google Speech Recognition service; {e}")
    return None  

st.image("img.jpg", width=100)
st.title("LAGOZON TECHNOLOGIES PVT. LTD.")
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "Welcome!"}]

if st.button('Speak'):
    recognized_text = recognize_speech()
    if recognized_text:
        st.session_state.messages.append({"role": "user", "content": recognized_text})

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "results" in message:
            st.dataframe(message["results"])

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response = ""
        resp_container = st.empty()
        for delta in client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            response += (delta.choices[0].delta.content or "")
            resp_container.markdown(response)

        message = {"role": "assistant", "content": response}
        
        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1)
            conn = get_sql_connection()
            query_results = pd.read_sql(sql, conn)
            message["results"] = query_results
            st.write("Query Results:")
            st.dataframe(query_results)
            generate_lida_visualization(query_results)
        
        st.session_state.messages.append(message)
