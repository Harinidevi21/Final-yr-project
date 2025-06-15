from flask import Flask, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy
import re
from googletrans import Translator
from langdetect import detect 
app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petitions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define database model
class Petition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    suggestion = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Add a status field


# Initialize Google Translator
translator = Translator()

# Detect department
def detect_department(content):
    department_keywords = {
        "Corporation": ["garbage", "drainage", "roads", "waste"],
        "Water Supply": ["water", "pipeline", "tap", "leak"],
        "Electricity": ["power", "electricity", "voltage", "transformer"],
        "Health": ["hospital", "clinic", "ambulance", "doctor"],
        "Education": ["school", "college", "university", "teacher"]
    }
    for dept, keywords in department_keywords.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE):
                return dept
    return "General"

# Categorize petition using sentiment (simplified for now)
def categorize_petition(content):
    # Placeholder for sentiment analysis
    if "urgent" in content.lower():
        return "Urgent"
    else:
        return "Normal"

# AI-based summarization (simplified for now)
def summarize_content(content):
    if len(content.split()) < 30:
        return content
    return content[:60] + "..."  # Simple truncation for long content

# Provide suggestions
def provide_suggestion(department):
    suggestions = {
        "Corporation": "Report to the local municipal office.",
        "Water Supply": "Contact the water board helpline.",
        "Electricity": "Call the electricity board emergency number.",
        "Health": "Visit the nearest health center.",
        "Education": "Notify the local education officer.",
        "General": "Submit the petition to the general grievance cell."
    }
    return suggestions.get(department, "No specific suggestion available.")

import asyncio
from googletrans import Translator

translator = Translator()

# Function to translate Tamil to English
async def translate_to_english(content):
    if detect(content) == 'ta':  # Check if the text is in Tamil
        translated = await translator.translate(content, src='ta', dest='en')
        return translated.text
    return content

def translate(content):
    # Run the async translate function in a separate event loop
    return asyncio.run(translate_to_english(content))

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        content = request.form.get('content', '')

        # Call the synchronous translation function
        content = translate(content)

        summary = summarize_content(content)
        department = detect_department(content)
        category = categorize_petition(content)
        suggestion = provide_suggestion(department)

        # Save to database
        petition = Petition(
            content=content,
            summary=summary,
            department=department,
            category=category,
            suggestion=suggestion
        )
        db.session.add(petition)
        db.session.commit()

        result = {
            "summary": summary,
            "department": department,
            "category": category,
            "suggestion": suggestion
        }

    return render_template('mainindex.html', result=result)

@app.route('/update_status/<int:petition_id>', methods=['POST'])
def update_status(petition_id):
    action = request.form.get('action')

    # Fetch the petition from the database
    petition = Petition.query.get(petition_id)
    if petition:
        if action == "Complete":
            petition.status = "Completed"  # Set status as 'Completed'
        elif action == "Reject":
            petition.status = "Rejected"  # Set status as 'Rejected'

        # Commit the changes to the database
        db.session.commit()

    return redirect('/view')  # Redirect back to the petitions view page


@app.route('/view')
def view_db():
    petitions = Petition.query.all()
    return render_template('mainadmin.html', petitions=petitions)

if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5000)
