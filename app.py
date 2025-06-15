from tokenize import Comment
from distro import like
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import spacy
from datetime import datetime
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_DOMAIN'] = 'localhost'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


nlp = spacy.load("en_core_web_sm")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Petition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(100), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    likes = db.relationship("Like", backref="petition", lazy="dynamic")
    repeat_count = db.Column(db.Integer, default=1)  # Removed content_hash

    def increment_repeat_count(self):
        self.repeat_count += 1
        db.session.commit()


# Verification Model
class Verification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    aadhar_no = db.Column(db.String(12), unique=True, nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(100), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    petition_id = db.Column(db.Integer, db.ForeignKey("petition.id"), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    petition_id = db.Column(db.Integer, db.ForeignKey("petition.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/index')
def home():
    return render_template('index.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration Successful. Please Login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# User Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid Credentials", "danger")
    return render_template('login.html')


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.route("/adminlogin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True  # Store session data
            flash("Login successful!", "success")
            return redirect(url_for("show_petitions"))

        flash("Invalid username or password!", "danger")

    return render_template("admin_login.html")

@app.route('/comment_petition/<int:petition_id>', methods=['POST'])
@login_required
def comment_petition(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    comment_text = request.form.get("comment")

    if not comment_text.strip():
        flash("Comment cannot be empty!", "danger")
        return redirect(url_for('view_petitions'))

    comment = Comment(text=comment_text, user_id=current_user.id, petition_id=petition_id)
    db.session.add(comment)
    db.session.commit()
    flash("Comment added successfully!", "success")
    return redirect(url_for('view_petitions'))

@app.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    if request.method == 'POST':
        name = request.form['name']
        aadhar_no = request.form['aadhar_no']
        dob = request.form['dob']
        location = request.form['location']

        # Check verification
        verification = Verification.query.filter_by(name=name, aadhar_no=aadhar_no, dob=dob, location=location).first()
        if verification:
            # ✅ Retrieve petition data from session
            petition_data = session.get("petition_data")

            if petition_data:
                new_petition = Petition(
                    file_name=petition_data.get("file_name"),
                    is_public=petition_data.get("is_public"),
                    category=petition_data.get("category"),
                    upload_time=datetime.utcnow(),  # Add this if missing in the model
                    user_id=current_user.id,  # Add this if Petition model has user_id
                    verified=True
                )
                db.session.add(new_petition)
                db.session.commit()
                session.pop("petition_data", None)

                flash("Petition Verified & Submitted Successfully!", "success")
                return redirect(url_for('home'))
            else:
                flash("No petition found for submission!", "danger")
        else:
            flash("Verification Failed! Check Your Details.", "danger")

    return render_template('verify.html')



# View Public Petitions
@app.route('/petitions')
def view_petitions():
    petitions = Petition.query.filter_by(is_public=True, verified=True).all()

    print("Fetched Petitions:", petitions)  # Debugging line

    if not petitions:
        print("No petitions found!")  # If petitions are missing, this will be printed

    return render_template('petitions.html', petitions=petitions)



# Function to categorize petition content
def categorize_petition(content):
    keywords = {
        "urgent": ["immediate", "emergency", "critical", "severe", "urgent"],
        "fast": ["quick", "rapid", "fast", "soon"],
    }
    
    doc = nlp(content.lower())

    for token in doc:
        if token.text in keywords["urgent"]:
            return "Urgent"
        elif token.text in keywords["fast"]:
            return "Fast"
    
    return "Normal"


import fitz 
@app.route("/upload_petition", methods=["GET", "POST"])
@login_required
def upload_petition():
    if request.method == "POST":
        file = request.files.get("file")
        is_public = request.form.get("is_public") == "on"

        if not file:
            flash("No file selected!", "danger")
            return redirect(url_for("upload_petition"))

        file_ext = file.filename.rsplit(".", 1)[-1].lower()
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        content = ""

        try:
            if file_ext == "txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            elif file_ext == "pdf":
                doc = fitz.open(file_path)
                content = "\n".join([page.get_text() for page in doc])
            else:
                flash("Unsupported file format! Upload TXT or PDF.", "danger")
                return redirect(url_for("upload_petition"))
        except Exception as e:
            flash(f"Error reading file: {e}", "danger")
            return redirect(url_for("upload_petition"))

        if not content.strip():
            flash("Uploaded file is empty or unreadable!", "danger")
            return redirect(url_for("upload_petition"))

        # Compare based on file_name and user_id (or optionally content if stored)
        existing_petition = Petition.query.filter_by(
            user_id=current_user.id,
            file_name=file.filename
        ).first()

        if existing_petition:
            existing_petition.increment_repeat_count()
            flash(f"Duplicate petition uploaded! Repeat count: {existing_petition.repeat_count}", "warning")
            return redirect(url_for("upload_petition"))

        category = categorize_petition(content)

        new_petition = Petition(
            user_id=current_user.id,
            file_name=file.filename,
            is_public=is_public,
            category=category,
            verified=False
        )
        db.session.add(new_petition)
        db.session.commit()

        session["petition_data"] = {
            "file_name": file.filename,
            "is_public": is_public,
            "category": category,
        }

        flash(f"File uploaded successfully! Proceed to verification.", "info")
        return redirect(url_for("verify"))

    return render_template("upload_petition.html")

@app.route("/like_petition", methods=["POST"])
def like_petition():
    petition_id = request.args.get("petition_id")
    user_id = current_user.id  # Make sure the user is logged in

    if not petition_id:
        return "Petition ID is required", 400

    # Check if the user already liked this petition
    existing_like = Like.query.filter_by(user_id=user_id, petition_id=petition_id).first()
    if existing_like:
        return "Already liked", 400

    # Add new like
    like = Like(user_id=user_id, petition_id=petition_id)
    db.session.add(like)
    db.session.commit()

    return redirect(url_for("view_petitions"))


@app.route("/add_comment/<int:petition_id>", methods=["POST"])
def add_comment(petition_id):
    if "user_id" not in session:
        flash("You need to log in to comment.", "warning")
        return redirect(url_for("login"))

    comment_text = request.form.get("comment_text")
    if not comment_text:
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for("view_petitions"))

    new_comment = Comment(petition_id=petition_id, user_id=session["user_id"], text=comment_text, user_name=session["user_name"])
    db.session.add(new_comment)
    db.session.commit()


@app.route("/view_petitions")
def show_petitions():
    urgent_petitions = Petition.query.filter_by(category="Urgent").all()
    fast_petitions = Petition.query.filter_by(category="Fast").all()
    normal_petitions = Petition.query.filter_by(category="Normal").all()

    return render_template(
        "view_petitions.html",
        urgent_petitions=urgent_petitions,
        fast_petitions=fast_petitions,
        normal_petitions=normal_petitions,
    )



# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context(): 
        db.create_all()
    app.run(debug=True, port=5001)

