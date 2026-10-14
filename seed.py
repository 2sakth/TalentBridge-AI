from app import db, users, jobs
from werkzeug.security import generate_password_hash
from datetime import datetime
db.drop_collection("users"); db.drop_collection("jobs")
r=users.insert_one({"name":"Demo Recruiter","email":"recruiter@talentbridge.com","password":generate_password_hash("Recruiter@123"),"role":"recruiter","skills":[],"created_at":datetime.utcnow()})
c=users.insert_one({"name":"Demo Candidate","email":"candidate@talentbridge.com","password":generate_password_hash("Candidate@123"),"role":"candidate","skills":["Python","React","Flask","SQL"],"created_at":datetime.utcnow()})
jobs.insert_many([
 {"title":"Python Full Stack Developer","company":"TechNova","location":"Coimbatore","type":"Full-time","description":"Build APIs and responsive applications using Python Flask React MongoDB REST API Git.","skills":["Python","Flask","React","MongoDB","REST API","Git"],"salary":"₹4-7 LPA","recruiter_id":r.inserted_id,"created_at":datetime.utcnow()},
 {"title":"React Developer","company":"CloudMint","location":"Coimbatore / Remote","type":"Full-time","description":"Develop React interfaces with JavaScript HTML CSS REST API Git.","skills":["React","JavaScript","HTML","CSS","REST API","Git"],"salary":"₹3-6 LPA","recruiter_id":r.inserted_id,"created_at":datetime.utcnow()}
])
print("Seeded. recruiter@talentbridge.com / Recruiter@123")
