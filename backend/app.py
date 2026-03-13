import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# DATABASE CONFIG 
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@localhost:5432/safai_setu'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#  UPLOAD FOLDER 
UPLOAD_FOLDER = "static/uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

#  USERS TABLE 
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # admin / incharge / worker


# COMPLAINT TABLE 
class Complaint(db.Model):
    __tablename__ = "complaint"

    id = db.Column(db.Integer, primary_key=True)

    before_image = db.Column(db.String(200))
    after_image = db.Column(db.String(200))

    location = db.Column(db.String(200))
    description = db.Column(db.String(300))

    status = db.Column(db.String(50), default="Submitted")

    incharge_id = db.Column(db.Integer)
    worker_id = db.Column(db.Integer)


# CREATE TABLES 
with app.app_context():
    db.create_all()


#  HOME 
@app.route("/")
def home():
    return "Safai Setu Backend Running"


# LOGIN 
@app.route("/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            return jsonify({
                "message": "Login successful",
                "role": user.role,
                "user_id": user.id
            })

        return jsonify({"message": "Invalid login"}), 401

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"message": "Server Error"}), 500


# SUBMIT COMPLAINT FROM CITIZEN 
@app.route("/complaint", methods=["POST"])
def complaint():

    try:

        if 'photo' not in request.files:
            return jsonify({"message": "Photo missing"}), 400

        photo = request.files['photo']

        location = request.form.get("location")
        description = request.form.get("description")

        if photo.filename == "":
            return jsonify({"message": "No selected file"}), 400

        if not location:
            return jsonify({"message": "Location missing"}), 400

        if not description:
            return jsonify({"message": "Description missing"}), 400

        filename = secure_filename(photo.filename)

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        photo.save(filepath)

        new_complaint = Complaint(
            before_image=filepath,
            location=location,
            description=description,
            status="Submitted"
        )

        db.session.add(new_complaint)
        db.session.commit()

        return jsonify({"message": "Complaint Submitted Successfully"})

    except Exception as e:
        print("COMPLAINT ERROR:", e)
        return jsonify({"message": "Server Error"}), 500


# GET ALL COMPLAINTS 
@app.route("/complaints", methods=["GET"])
def get_complaints():

    try:

        complaints = Complaint.query.all()

        result = []

        for c in complaints:

            result.append({
                "id": c.id,
                "location": c.location,
                "description": c.description,
                "status": c.status,
                "before_image": c.before_image,
                "after_image": c.after_image,
                "incharge_id": c.incharge_id,
                "worker_id": c.worker_id
            })

        return jsonify(result)

    except Exception as e:
        print("FETCH ERROR:", e)
        return jsonify({"message": "Server Error"}), 500


# ADMIN ASSIGN INCHARGE 
@app.route("/assign_incharge", methods=["POST"])
def assign_incharge():

    try:

        data = request.get_json()

        complaint_id = data.get("complaint_id")
        incharge_id = data.get("incharge_id")

        complaint = Complaint.query.get(complaint_id)

        if not complaint:
            return jsonify({"message": "Complaint not found"}), 404

        complaint.incharge_id = incharge_id
        complaint.status = "Assigned to Incharge"

        db.session.commit()

        return jsonify({"message": "Incharge assigned successfully"})

    except Exception as e:
        print("ASSIGN INCHARGE ERROR:", e)
        return jsonify({"message": "Server Error"}), 500


#  INCHARGE ASSIGN WORKER
@app.route("/assign_worker", methods=["POST"])
def assign_worker():

    try:

        data = request.get_json()

        complaint_id = data.get("complaint_id")
        worker_id = data.get("worker_id")

        complaint = Complaint.query.get(complaint_id)

        if not complaint:
            return jsonify({"message": "Complaint not found"}), 404

        complaint.worker_id = worker_id
        complaint.status = "Assigned to Worker"

        db.session.commit()

        return jsonify({"message": "Worker assigned successfully"})

    except Exception as e:
        print("ASSIGN WORKER ERROR:", e)
        return jsonify({"message": "Server Error"}), 500


#  WORKER COMPLETE COMPLAINT 
@app.route("/complete_complaint", methods=["POST"])
def complete_complaint():

    try:

        complaint_id = request.form.get("complaint_id")

        if 'photo' not in request.files:
            return jsonify({"message": "After image required"}), 400

        photo = request.files['photo']

        complaint = Complaint.query.get(complaint_id)

        if not complaint:
            return jsonify({"message": "Complaint not found"}), 404

        filename = secure_filename(photo.filename)

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        photo.save(filepath)

        complaint.after_image = filepath
        complaint.status = "Completed"

        db.session.commit()

        return jsonify({"message": "Complaint completed successfully"})

    except Exception as e:
        print("COMPLETE ERROR:", e)
        return jsonify({"message": "Server Error"}), 500
    
# UPDATE WORKER LOCATION 
@app.route("/update_worker_location", methods=["POST"])
def update_worker_location():

    data = request.get_json()

    worker_id = data.get("worker_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    return jsonify({
        "worker_id":worker_id,
        "latitude":latitude,
        "longitude":longitude
    })


#  RUN SERVER 
if __name__ == "__main__":
    app.run(debug=True, port=5001)