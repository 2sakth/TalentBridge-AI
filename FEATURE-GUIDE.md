# TalentBridge AI — Feature Guide

## Included working features
- Candidate/recruiter registration and login
- Hashed passwords and JWT authentication
- Recruiter job create/edit/delete
- Public job search by title, company or location
- Candidate applications with duplicate-application prevention
- Application status updates
- ATS-style skill matching with matched/missing skills and transparent percentage score
- PDF text extraction endpoint for resumes
- Interview scheduling API
- Candidate dashboard and application list
- MongoDB seed script and Docker Compose

## Run
1. Install Docker Desktop and Node.js.
2. In this folder: `docker compose up --build`
3. In another terminal: `docker compose exec backend python seed.py`
4. `cd frontend && npm install && npm run dev`
5. Demo recruiter: `recruiter@talentbridge.com` / `Recruiter@123`
6. Demo candidate: `candidate@talentbridge.com` / `Candidate@123`

## Honest scope
This is a portfolio MVP. Test the full flow locally. ATS matching is rule-based, not a trained ML model. Production deployment would require stronger validation, authorization checks on status updates, tests, rate limiting, logging, secure secret management and privacy controls.
