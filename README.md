# TalentBridge AI

Portfolio-grade recruitment platform built with React + Flask + MongoDB + JWT.

## Features
- Candidate and recruiter authentication
- JWT protected routes
- Job CRUD for recruiters
- Candidate job search and applications
- Application status workflow
- ATS-style skill matching and score
- Interview scheduling API
- Candidate dashboard
- Responsive React UI
- PDF resume text extraction endpoint

## Run
### Backend with Docker
1. Install Docker Desktop.
2. From this folder run:
   `docker compose up --build`
3. Seed demo data:
   `docker compose exec backend python seed.py`

### Frontend
`cd frontend`
`npm install`
`npm run dev`

Open the Vite URL shown in the terminal.

Demo recruiter:
`recruiter@talentbridge.com` / `Recruiter@123`

Demo candidate:
`candidate@talentbridge.com` / `Candidate@123`

## Interview explanation
React handles the UI. Flask exposes REST endpoints. MongoDB stores users, jobs and applications. JWT identifies the logged-in user on protected routes. The ATS endpoint extracts known skills from resume/JD text, compares the sets and calculates a transparent percentage score.
