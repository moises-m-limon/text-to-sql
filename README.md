# Data A.N.A.L.Y.S.T.S.

This project uses **Gradio** to create a UI that interacts with a **Snowflake** database using **OpenAI's GPT-4** to convert natural language queries into SQL.

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- OpenAI API key (sign up at [OpenAI](https://beta.openai.com/signup/))
- Snowflake account credentials

### Step 1: Install Dependencies
Below are the required packages:

```bash
gradio
pandas
snowflake-connector-python
snowflake-sqlalchemy
langchain
langchain_community
openai
```
Install all required packages from the requirements.txt file:
```bash
pip install -r requirements.txt
```
### Step 2: Run the Application
Activate the virtual environment (if not already activated).
```bash
python main.py
```
This will launch the Gradio UI in your browser.

# How to Use
- OpenAI Sign In: Enter your OpenAI API key and sign in.
- Snowflake Sign In: Enter your Snowflake credentials (username, password, account, warehouse, database, schema).
- Convert Natural Language to SQL: Enter a natural language query, click "Get SQL Query", and see the SQL query and explanation.
- Run SQL Query: Enter a SQL query and execute it to view the results.

