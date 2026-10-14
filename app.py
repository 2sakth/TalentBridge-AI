import os, re
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from PyPDF2 import PdfReader

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)
CORS(app)
JWTManager(app)

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client[os.getenv("MONGO_DB", "talentbridge")]
users, jobs, applications, interviews = db.users, db.jobs, db.applications, db.interviews

def oid(v):
    return ObjectId(v)

def clean(doc):
    if not doc: return None
    doc["_id"] = str(doc["_id"])
    for k in ("job_id","candidate_id","application_id"):
        if k in doc and isinstance(doc[k], ObjectId): doc[k] = str(doc[k])
    return doc

def skills_from_text(text):
    catalog = [
        "python","javascript","react","flask","django","node.js","express",
        "mongodb","mysql","postgresql","sql","rest api","git","docker",
        "aws","html","css","bootstrap","tailwind","java","c++","pandas",
        "numpy","machine learning","fastapi"
    ]
    low = text.lower()
    return sorted({s for s in catalog if s in low})

@app.get("/api/health")
def health():
    return jsonify({"status":"ok","service":"TalentBridge AI"})

@app.post("/api/auth/register")
def register():
    data = request.get_json() or {}
    name, email, password = data.get("name"), data.get("email","").lower().strip(), data.get("password")
    role = data.get("role","candidate")
    if not name or not email or not password:
        return jsonify({"message":"Name, email and password are required"}), 400
    if role not in ("candidate","recruiter"):
        return jsonify({"message":"Invalid role"}), 400
    if users.find_one({"email":email}):
        return jsonify({"message":"Email already registered"}), 409
    uid = users.insert_one({
        "name":name, "email":email, "password":generate_password_hash(password),
        "role":role, "skills":[], "created_at":__import__("datetime").datetime.utcnow()
    }).inserted_id
    return jsonify({"message":"Account created","id":str(uid)}), 201

@app.post("/api/auth/login")
def login():
    data=request.get_json() or {}
    user=users.find_one({"email":data.get("email","").lower().strip()})
    if not user or not check_password_hash(user["password"], data.get("password","")):
        return jsonify({"message":"Invalid email or password"}),401
    token=create_access_token(identity=str(user["_id"]))
    return jsonify({"token":token,"user":clean({k:v for k,v in user.items() if k!="password"})})

@app.get("/api/me")
@jwt_required()
def me():
    u=users.find_one({"_id":oid(get_jwt_identity())})
    return jsonify(clean({k:v for k,v in u.items() if k!="password"}))

@app.put("/api/me")
@jwt_required()
def update_me():
    uid=oid(get_jwt_identity()); data=request.get_json() or {}
    allowed={k:data[k] for k in ("name","phone","location","bio","skills") if k in data}
    users.update_one({"_id":uid},{"$set":allowed})
    return jsonify({"message":"Profile updated"})

@app.get("/api/jobs")
def list_jobs():
    q=request.args.get("q","").strip()
    query={"$or":[{"title":{"$regex":q,"$options":"i"}},{"company":{"$regex":q,"$options":"i"}},{"location":{"$regex":q,"$options":"i"}}]} if q else {}
    return jsonify([clean(x) for x in jobs.find(query).sort("_id",-1)])

@app.post("/api/jobs")
@jwt_required()
def create_job():
    u=users.find_one({"_id":oid(get_jwt_identity())})
    if u.get("role")!="recruiter": return jsonify({"message":"Recruiter access required"}),403
    data=request.get_json() or {}
    required=["title","company","location","description","skills"]
    if not all(data.get(k) for k in required): return jsonify({"message":"All job fields are required"}),400
    jid=jobs.insert_one({
        "title":data["title"],"company":data["company"],"location":data["location"],
        "type":data.get("type","Full-time"),"description":data["description"],
        "skills":data["skills"],"salary":data.get("salary","Not disclosed"),
        "recruiter_id":u["_id"],"created_at":__import__("datetime").datetime.utcnow()
    }).inserted_id
    return jsonify({"message":"Job created","id":str(jid)}),201

@app.put("/api/jobs/<jid>")
@jwt_required()
def update_job(jid):
    u=users.find_one({"_id":oid(get_jwt_identity())})
    job=jobs.find_one({"_id":oid(jid)})
    if not job or job.get("recruiter_id")!=u["_id"]: return jsonify({"message":"Not allowed"}),403
    data=request.get_json() or {}
    allowed={k:data[k] for k in ("title","company","location","type","description","skills","salary") if k in data}
    jobs.update_one({"_id":oid(jid)},{"$set":allowed})
    return jsonify({"message":"Job updated"})

@app.delete("/api/jobs/<jid>")
@jwt_required()
def delete_job(jid):
    u=users.find_one({"_id":oid(get_jwt_identity())})
    job=jobs.find_one({"_id":oid(jid)})
    if not job or job.get("recruiter_id")!=u["_id"]: return jsonify({"message":"Not allowed"}),403
    jobs.delete_one({"_id":oid(jid)})
    applications.delete_many({"job_id":oid(jid)})
    return jsonify({"message":"Job deleted"})

@app.post("/api/jobs/<jid>/apply")
@jwt_required()
def apply(jid):
    uid=oid(get_jwt_identity())
    if not jobs.find_one({"_id":oid(jid)}): return jsonify({"message":"Job not found"}),404
    if applications.find_one({"job_id":oid(jid),"candidate_id":uid}): return jsonify({"message":"Already applied"}),409
    aid=applications.insert_one({
        "job_id":oid(jid),"candidate_id":uid,"status":"Applied",
        "resume_text":"","ats_score":None,"created_at":__import__("datetime").datetime.utcnow()
    }).inserted_id
    return jsonify({"message":"Application submitted","id":str(aid)}),201

@app.get("/api/applications")
@jwt_required()
def my_applications():
    uid=oid(get_jwt_identity()); u=users.find_one({"_id":uid})
    if u.get("role")=="candidate":
        rows=list(applications.find({"candidate_id":uid}))
    else:
        myjobs=[x["_id"] for x in jobs.find({"recruiter_id":uid})]
        rows=list(applications.find({"job_id":{"$in":myjobs}}))
    out=[]
    for a in rows:
        j=jobs.find_one({"_id":a["job_id"]})
        c=users.find_one({"_id":a["candidate_id"]})
        a=clean(a); a["job"]=clean(j); a["candidate"]=clean({k:v for k,v in c.items() if k!="password"}) if c else None
        out.append(a)
    return jsonify(out)

@app.put("/api/applications/<aid>/status")
@jwt_required()
def status(aid):
    data=request.get_json() or {}
    allowed=["Applied","Shortlisted","Rejected","Interview","Hired"]
    if data.get("status") not in allowed: return jsonify({"message":"Invalid status"}),400
    applications.update_one({"_id":oid(aid)},{"$set":{"status":data["status"]}})
    return jsonify({"message":"Status updated"})

@app.post("/api/ats/analyze")
@jwt_required()
def ats():
    if "resume" in request.files:
        f=request.files["resume"]
        try:
            reader=PdfReader(f)
            resume_text="\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:
            resume_text=""
    else:
        resume_text=(request.form.get("resume_text") or request.get_json(silent=True) or {}).get("resume_text","")
    jd=request.form.get("job_description") or (request.get_json(silent=True) or {}).get("job_description","")
    if not resume_text or not jd: return jsonify({"message":"Resume text/file and job description are required"}),400
    required=skills_from_text(jd); candidate=skills_from_text(resume_text)
    matched=sorted(set(required)&set(candidate)); missing=sorted(set(required)-set(candidate))
    score=round((len(matched)/len(required))*100) if required else 0
    return jsonify({"score":score,"matched_skills":matched,"missing_skills":missing,
                    "candidate_skills":candidate,"required_skills":required,
                    "recommendation":"Focus on: "+", ".join(missing) if missing else "Strong match. Prepare project examples for the interview."})

@app.post("/api/interviews")
@jwt_required()
def schedule():
    u=users.find_one({"_id":oid(get_jwt_identity())})
    if u.get("role")!="recruiter": return jsonify({"message":"Recruiter access required"}),403
    data=request.get_json() or {}
    iid=interviews.insert_one({
        "application_id":oid(data["application_id"]),"date":data["date"],
        "time":data["time"],"mode":data.get("mode","Online"),
        "meeting_link":data.get("meeting_link",""),"notes":data.get("notes","")
    }).inserted_id
    applications.update_one({"_id":oid(data["application_id"])},{"$set":{"status":"Interview"}})
    return jsonify({"message":"Interview scheduled","id":str(iid)}),201

@app.get("/api/interviews")
@jwt_required()
def interviews_list():
    uid=oid(get_jwt_identity()); u=users.find_one({"_id":uid})
    apps=list(applications.find({"candidate_id":uid})) if u.get("role")=="candidate" else []
    ids=[a["_id"] for a in apps]
    return jsonify([clean(x) for x in interviews.find({"application_id":{"$in":ids}})])

if __name__=="__main__":
    app.run(port=5001, debug=True)
