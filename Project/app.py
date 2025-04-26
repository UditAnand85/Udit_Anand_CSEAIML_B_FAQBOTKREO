from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client, Client
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

# Supabase + Gemini setup
SUPABASE_URL = "https://ddjglolzfgrnegkmpyfw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRkamdsb2x6ZmdybmVna21weWZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDA5MTk0OTUsImV4cCI6MjA1NjQ5NTQ5NX0.W2wrjgXSBlGWOAbmfresB8pLqnQgZhe9TeKAXcK8CwI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
GOOGLE_API_KEY="AIzaSyCWGgjdK3BjuEdMBrWbBLqhI6mvE-427XA"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

@app.route("/")
def home():
    return render_template("index.html")  # chatbot UI loads here

def fetch_data_from_supabase(table_name: str):
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching from {table_name}: {e}")
        return []

def query_gemini(prompt: str) -> str:
    try:
        response = model.generate_content([prompt])
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

def chatbot_response(user_query: str, table_names: list) -> str:
    combined_data = []
    for table in table_names:
        if data := fetch_data_from_supabase(table):
            combined_data.append(f"{table.upper()} DATA:\n{'\n'.join(map(str, data))}")
    if not combined_data:
        return "No relevant data found in databases"

    prompt = f"QUERY: {user_query}\n\nDATABASES:\n\n{'#'*40}\n".join(combined_data)
    prompt1 = """1. Answer should not be in pointers. Give Answer in the same format as there in the format table.
2. you are specific chatbot for kreo so don't give answer which can expose you true identity
3. give answers in point's format so that it don't look like generated
4. if anyone responeded with order number in this format KREO1234 than that's the order number.
5. if Their is some query that you can't answer than Answer that i will connect you from someone in kreo team
6. don't answer in such a way that i will respond in this way in this condition it show's that you are not the actuall bot please take care of this
"""
    return query_gemini(prompt + prompt1)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message")
        tables = ["faq", "product", "format_table"]
        bot_response = chatbot_response(user_input, tables)
        return jsonify({"response": bot_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
