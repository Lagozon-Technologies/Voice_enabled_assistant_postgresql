import os
import psycopg2
import toml
import streamlit as st

# Load the secrets.toml configuration to get the OpenAI API key
config = toml.load('.streamlit/secrets.toml')
OPENAI_API_KEY = config['openai_api_key']

# Fetch database configuration from environment variables
DBNAME = os.environ.get('DBNAME')
DBUSER = os.environ.get('DBUSER')
DBPASSWORD = os.environ.get('DBPASSWORD')
DBHOST = os.environ.get('DBHOST')
DBPORT = os.environ.get('DBPORT')
SSL_MODE = os.environ.get('SSL_MODE', 'require')  # Default to 'require' if not specified

# PostgreSQL connection string
connection_string = f"dbname={DBNAME} user={DBUSER} password={DBPASSWORD} host={DBHOST} port={DBPORT} sslmode={SSL_MODE}"

SCHEMA_PATH = os.environ.get("SCHEMA_PATH", "public")
QUALIFIED_TABLE_NAME = f"{SCHEMA_PATH}.LZ_Foods"
TABLE_DESCRIPTION = """
The dataset contains sales data for various stores, including total sales, orders, and sales distribution across different channels. It provides insights into delivery sales, dine-in sales, and takeaway sales, segmented by different delivery platforms such as Swiggy, Zomato, Amazon Foods, and various payment gateways like GPay, Paytm, PhonePe, and more. Additionally, it includes information on sales made through different devices such as desktop, mobile apps (Android and iPhone), and web platforms (PWA).
"""

GEN_SQL = """ 
You will be acting as an AI  PostgreSQL Server  Expert named Lagozon assistant.
Your goal is to give correct, executable sql query to users.
You will be replying to users who will be confused if you don't respond in the character of Lagozon.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond and include a sql query based on the question and the table. 

{context}

Here are 6 critical rules for the interaction you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3. Text / string where clauses must be fuzzy match e.g ilike %keyword%
4. Make sure to generate a single snowflake sql code, not multiple. 
5. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names
6. DO NOT put numerical at the very front of sql variable.
</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response.

Now to get started, please briefly introduce yourself as a Helping Chatbot not more than one line, donot mention table name.
Then provide 3 example questions using bullet points.
"""

# Database connection function
@st.cache(allow_output_mutation=True)
def get_connection():
    return psycopg2.connect(connection_string)

# Retrieve table context with SQL Server specifics
@st.cache_data(show_spinner="Loading Lagozon's context...")
def get_table_context(table_name: str, table_description: str):
    columns_description = """
   - **STORE_ID**: VARCHAR
    - **BUSINESS_MONTH**: VARCHAR
    - **TOTAL_SALES**: FLOAT
    - **TOTAL_ORDER**: INT
    - **DELIVERY_SALES**: FLOAT
    - **NON_DELIVERY_SALES**: FLOAT
    - **DELIVERY_ORDER**: INT
    - **NON_DELIVERY_ORDER**: INT
    - **DINEIN_SALES**: FLOAT
    - **DINEIN_ORDER**: INT
    - **TAKEAWAY_SALES**: FLOAT
    - **TAKEAWAY_ORDER**: INT
    - **DNP_SALES**: FLOAT
    - **DNP_ORDER**: FLOAT
    - **SWIGGY_DELIVERY_SALES**: FLOAT
    - **SWIGGY_DELIVERY_ORDER**: INT
    - **ZOMATO_DELIVERY_SALES**: FLOAT
    - **ZOMATO_DELIVERY_ORDER**: INT
    - **AMAZON_FOODS_DELIVERY_SALES**: FLOAT
    - **AMAZON_FOODS_DELIVERY_ORDER**: INT
    - **AMAZON_FOODS_DINEIN_SALES**: FLOAT
    - **AMAZON_FOODS_DINEIN_ORDER**: INT
    - **AMAZON_FOODS_TAKEAWAY_SALES**: FLOAT
    - **AMAZON_FOODS_TAKEAWAY_ORDER**: INT
    - **GPAY_DELIVERY_SALES**: FLOAT
    - **GPAY_DELIVERY_ORDER**: INT
    - **GPAY_DINEIN_SALES**: FLOAT
    - **GPAY_DINEIN_ORDER**: INT
    - **GPAY_TAKEAWAY_SALES**: FLOAT
    - **GPAY_TAKEAWAY_ORDER**: INT
    - **PAYTM_MICROAPP_DELIVERY_SALES**: FLOAT
    - **PAYTM_MICROAPP_DELIVERY_ORDER**: INT
    - **PAYTM_MICROAPP_TAKEAWAY_SALES**: FLOAT
    - **PAYTM_MICROAPP_TAKEAWAY_ORDER**: INT
    - **PAYTM_MICROAPP_DINEIN_SALES**: FLOAT
    - **PAYTM_MICROAPP_DINEIN_ORDER**: INT
    - **PHONEPE_DELIVERY_SALES**: FLOAT
    - **PHONEPE_DELIVERY_ORDER**: INT
    - **DESKTOP_DELIVERY_SALES**: FLOAT
    - **DESKTOP_DELIVERY_ORDER**: INT
    - **DESKTOP_TAKEAWAY_SALES**: FLOAT
    - **DESKTOP_TAKEAWAY_ORDER**: INT
    - **IRCTC_DELIVERY_SALES**: FLOAT
    - **IRCTC_DELIVERY_ORDER**: INT
    - **NEW_APP_ANDROID_DELIVERY_SALES**: FLOAT
    - **NEW_APP_ANDROID_DELIVERY_ORDER**: INT
    - **NEW_APP_ANDROID_DINEIN_SALES**: FLOAT
    - **NEW_APP_ANDROID_DINEIN_ORDER**: INT
    - **NEW_APP_ANDROID_DRIVE_PICK_SALES**: FLOAT
    - **NEW_APP_ANDROID_DRIVE_PICK_ORDER**: INT
    - **NEW_APP_ANDROID_TAKEAWAY_SALES**: FLOAT
    - **NEW_APP_ANDROID_TAKEAWAY_ORDER**: INT
    - **NEW_APP_IPHONE_DELIVERY_SALES**: FLOAT
    - **NEW_APP_IPHONE_DELIVERY_ORDER**: INT
    - **NEW_APP_IPHONE_DRIVE_PICK_SALES**: FLOAT
    - **NEW_APP_IPHONE_DRIVE_PICK_ORDER**: INT
    - **NEW_APP_IPHONE_TAKEAWAY_SALES**: FLOAT
    - **NEW_APP_IPHONE_TAKEAWAY_ORDER**: INT
    - **PWA_DELIVERY_SALES**: FLOAT
    - **PWA_DELIVERY_ORDER**: INT
    - **PWA_DINEIN_SALES**: FLOAT
    - **PWA_DINEIN_ORDER**: INT
    - **PWA_TAKEAWAY_SALES**: FLOAT
    - **PWA_TAKEAWAY_ORDER**: INT
    - **CALL_CENTER_DELIVERY_SALES**: FLOAT
    - **CALL_CENTER_DELIVERY_ORDER**: INT
    - **CALL_CENTER_TAKEAWAY_SALES**: FLOAT
    - **CALL_CENTER_TAKEAWAY_ORDER**: INT
    - **PHONE_DELIVERY_SALES**: FLOAT
    - **PHONE_DELIVERY_ORDER**: INT
    - **DINEIN_CHANNEL_SALES**: FLOAT
    - **DINEIN_CHANNEL_ORDER**: INT
    - **ODC_DINEIN_SALES**: FLOAT
    - **ODC_DINEIN_ORDER**: INT
    - **DINEIN_TAKEAWAY_SALES**: FLOAT
    - **DINEIN_TAKEAWAY_ORDER**: INT
    - **KIOSK_DINEIN_SALES**: FLOAT
    - **KIOSK_DINEIN_ORDER**: INT
    - **KIOSK_TAKEAWAY_SALES**: FLOAT
    - **KIOSK_TAKEAWAY_ORDER**: INT
    - **OLD_APP_ANDROID_TAKEAWAY_SALES**: FLOAT
    - **OLD_APP_ANDROID_TAKEAWAY_ORDER**: INT
    - **OLD_APP_IPHONE_TAKEAWAY_SALES**: FLOAT
    - **OLD_APP_IPHONE_TAKEAWAY_ORDER**: INT
    """
    context = f"""
    Here is the table name: <tableName>{table_name}</tableName>

    <tableDescription>{table_description}</tableDescription>

    Here are the columns of the {table_name}:

    <columns>\n\n{columns_description}\n\n</columns>
    """
    return context

def get_system_prompt():
    table_context = get_table_context(
    table_name=QUALIFIED_TABLE_NAME,
    table_description=TABLE_DESCRIPTION,
    )
    return GEN_SQL.format(context=table_context)

def generate_gpt_response(user_input):
    connection = get_connection()
    cursor = connection.cursor()
    # Adapt SQL query to PostgreSQL's syntax and capabilities
    sql_query = "SELECT * FROM your_table_name WHERE your_condition LIMIT 10"
    cursor.execute(sql_query)
    results = cursor.fetchall()
    cursor.close()
    return results

if __name__ == "__main__":
    st.header("Prompt Engineering for Lagozon")
    st.markdown(get_system_prompt())
