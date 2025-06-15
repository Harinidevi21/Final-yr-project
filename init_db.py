from app import app, db
from app import Verification  # Import the Verification model

with app.app_context():  # Ensure application context
    db.create_all()  # Create tables if they do not exist

    # Generate 100 unique verification records
    sample_data = [
        (f"User {i}", f"98765432{i:04d}", f"19-{(i%12)+1:02d}-199{(i%10)}", f"City {i}")
        for i in range(1, 101)
    ]

    # Insert data into the database
    for name, aadhar_no, dob, location in sample_data:
        record = Verification(name=name, aadhar_no=aadhar_no, dob=dob, location=location)
        db.session.add(record)

    db.session.commit()  # Save changes
    print("✅ Database initialized with 100 unique verification records.")
    
