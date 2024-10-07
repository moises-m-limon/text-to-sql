import gradio as gr
import snowflake.connector
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import SQLDatabaseToolkit  # Import the toolkit

# Snowflake connection parameters
snowflake_params = {
    "user": "",
    "password": "",
    "account": "",
    "warehouse": "",
    "database": "",
    "schema": "",
}

connection = None
llm = None
sql_agent = None

# Agent instructions
SNOWFLAKE_AGENT_PREFIX = """
You are an agent designed to interact with a SQL database.
## Instructions:
- Everything must be formatted and readable as a string.
- Given an input question, create a syntactically correct {dialect} query
to run, then look at the results of the query and return the answer.
- Unless the user specifies a specific number of examples they wish to
obtain, **ALWAYS** limit your query to at most {top_k} results.
- You can order the results by a relevant column to return the most
interesting examples in the database.
- Never query for all the columns from a specific table, only ask for
the relevant columns given the question.
- You have access to tools for interacting with the database.
- You MUST double check your query before executing it. If you get an error
while executing a query, rewrite the query and try again.
- DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.)
to the database.
- DO NOT CREATE any new tables.
- DO NOT MAKE UP AN ANSWER OR USE PRIOR KNOWLEDGE, ONLY USE THE RESULTS
OF THE CALCULATIONS YOU HAVE DONE.
- ALWAYS, start final answer with "Final Answer:"
- ALWAYS, as part of your final answer, explain how you got to the answer
in a section that starts with "Explanation:". 
- Include only the sql_db_query Action's input and include it in a section that starts with "SQL Query:"
"""

SNOWFLAKE_AGENT_FORMAT_INSTRUCTIONS = """
## Response Format:
Final Answer: [Your answer here.]
Explanation: I queried the [table_name] for the [columns] with the condition [conditions]. 
SQL Query: The SQL query used was: 
[SQL Query]
"""

def sign_in_openai(api_key):
    global llm
    try:
        # Initialize the ChatOpenAI model
        llm = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4",
            max_tokens=500,
        )
        return "Successfully signed into OpenAI!"
    except Exception as e:
        # Print the exact error message in the console
        print(f"Error signing into OpenAI: {str(e)}")
        return f"Error: {str(e)}"

def sign_in_snowflake(username, password, account, warehouse, database, schema):
    global connection, sql_agent, llm
    try:
        # Ensure llm (OpenAI) is initialized
        if llm is None:
            return "Please sign into OpenAI first."

        # Ensure none of the Snowflake parameters are empty
        if not all([username, password, account, warehouse, database, schema]):
            return "All Snowflake parameters must be provided!"
        
        snowflake_params.update({
            "user": username,
            "password": password,
            "account": account,
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
        })
        
        # Attempt connection
        connection = snowflake.connector.connect(**snowflake_params)
        
        # Construct URI
        db_uri = f"snowflake://{username}:{password}@{account}/{database}/{schema}?warehouse={warehouse}"
        
        # Create SQL database instance
        database_instance = SQLDatabase.from_uri(db_uri)

        # Create the toolkit
        toolkit = SQLDatabaseToolkit(db=database_instance, llm=llm)

        # Create the SQL agent using the toolkit
        sql_agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,  # Pass the toolkit
            top_k=30,
            verbose=True,
            handle_parsing_errors=True,
        )
        
        return "Successfully signed into Snowflake!"
    except Exception as e:
        return f"Error signing into Snowflake: {str(e)}"

def text_to_sql(natural_language_query):
    if sql_agent is None:
        return "Please sign into OpenAI and Snowflake."
    
    try:
        response = sql_agent.run(natural_language_query)
        print(f"Agent Response: {response}")
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

def run_query(sql_query):
    if connection is None:
        return "You must sign into Snowflake first!"

    try:
        cursor = connection.cursor()
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        results = cursor.fetchall()
        df = pd.DataFrame(results, columns=columns)
        cursor.close()
        return df
    except Exception as e:
        return f"Error running query: {str(e)}"
# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## OpenAI Sign In")
    openai_api_key = gr.Textbox(label="OpenAI API Key", type="password")
    openai_button = gr.Button("Sign In to OpenAI")
    openai_output = gr.Textbox(label="OpenAI Sign In Output", interactive=False)
    openai_button.click(sign_in_openai, inputs=openai_api_key, outputs=openai_output)

    gr.Markdown("## Snowflake Sign In")
    with gr.Row():
        username = gr.Textbox(label="Username")
        password = gr.Textbox(label="Password", type="password")
        account = gr.Textbox(label="Account")
        warehouse = gr.Textbox(label="Warehouse")
        database = gr.Textbox(label="Database")
        schema = gr.Textbox(label="Schema")
    snowflake_button = gr.Button("Sign In to Snowflake")
    snowflake_output = gr.Textbox(label="Snowflake Sign In Output", interactive=False)
    snowflake_button.click(
        sign_in_snowflake,
        inputs=[username, password, account, warehouse, database, schema],
        outputs=snowflake_output,
    )

    gr.Markdown("## Convert Text to SQL")
    natural_language_input = gr.Textbox(label="Enter your query in natural language")
    sql_output = gr.Markdown(label="Generated SQL Query and Explanation")
    text_to_sql_button = gr.Button("Get SQL Query")

    text_to_sql_button.click(
        fn=text_to_sql,
        inputs=natural_language_input,
        outputs=sql_output
    )

    gr.Markdown("## Run SQL Query")
    sql_query_input = gr.Textbox(label="Enter your SQL query here")
    run_query_button = gr.Button("Run Query")
    query_output = gr.Dataframe(label="Query Results")
    run_query_button.click(run_query, inputs=sql_query_input, outputs=query_output)

demo.launch()