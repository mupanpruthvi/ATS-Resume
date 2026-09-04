# ResumeForge ATS - AI Resume Generator & Job Description Matcher

[![Live Demo](https://img.shields.io/badge/Live_Demo-resume--forge--ats.onrender.com-success?style=for-the-badge&logo=render)](https://resume-forge-ats.onrender.com)
[![GitHub Stars](https://img.shields.io/github/stars/mupanpruthvi/ATS-Resume?style=for-the-badge)](https://github.com/mupanpruthvi/ATS-Resume)

🌐 **Live Application URL**: [https://resume-forge-ats.onrender.com](https://resume-forge-ats.onrender.com)

ResumeForge ATS is a modern web application designed for students and job seekers to:
1. **Paste Job Descriptions or Job Links** from any career site (LinkedIn, Indeed, company portals, etc.) to automatically extract requirements, target role titles, and core skills.
2. **Upload Existing CVs** (.pdf, .docx, .txt) with automatic section parsing OR **type/edit details directly** (skills, internships, key projects, education, certifications).
3. **Generate ATS-Optimized Resumes** tailored specifically to the target Job Description with standard single-column ATS layouts, quantified bullet points, and strong action verbs.
4. **View Comprehensive ATS Match Score & Intelligence Dashboard**:
   - Overall ATS score (0–100%) with visual radial gauge and rating badge.
   - Before vs. After score comparison (shows score improvement from old CV to tailored resume).
   - Granular breakdown: Keyword Overlap %, Hard Skills Alignment %, Action Verbs & Impact Metrics %, and ATS Formatting Health %.
   - Interactive Keyword Inspector: Matched JD skills in green and missing JD skills in amber with **1-click "+" button to instantly add them into the resume**.
   - Actionable recommendations to maximize interview callbacks.
5. **Multiple Export Formats**:
   - **Print / Save as PDF**: Clean, standard A4/Letter ATS single-page/two-page resume printout.
   - **Download Word (.docx)**: Machine-scannable Word document formatted to ATS standards (standard margins, clean headings, no tables/graphics).
   - **Copy Plain Text**: Clean plain-text resume formatted for easy pasting into Taleo, Workday, or Greenhouse application boxes.
   - **In-Place Live Editing**: Click any line on the resume preview to edit text in real time with instant ATS score recalculation.

---

## 🚀 Live Cloud Deployment

The application is deployed and publicly accessible 24/7 at:
👉 **[https://resume-forge-ats.onrender.com](https://resume-forge-ats.onrender.com)**

Anyone in the world can access and use the tool directly from their web browser without any installation!



---

## Quick Start Guide

### 1. Requirements
- Python 3.10+ (Tested on Python 3.14)
- Dependencies installed: `fastapi`, `uvicorn`, `beautifulsoup4`, `pypdf`, `python-docx`, `requests`, `python-multipart`

### 2. Running the Application
From the project folder, simply run:

```bash
py run.py
```

This will automatically find an available port (defaults to 8000), start the FastAPI server, and launch your default web browser to:
`http://127.0.0.1:8000`

Alternatively, you can run directly with Uvicorn:

```bash
py -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

---

## Project Structure

```
Project/
├── server.py              # FastAPI server with REST API endpoints & static serving
├── ats_engine.py          # ATS scoring algorithms, keyword analyzer, and resume tailoring
├── parsers.py             # PDF & DOCX text extraction, JD URL scraper, and section parser
├── run.py                 # One-click launcher script with browser launch
├── test_ats.py            # Unit test suite for parsers, ATS scoring, and DOCX generation
├── test_api.py            # Integration test suite for all FastAPI endpoints
└── static/
    ├── index.html         # Modern 3-step wizard interface & dual-panel workspace
    ├── styles.css         # Responsive styling, ATS score gauges, and print stylesheet
    └── app.js             # Client state management, URL scraper, live editor & exports
```

---

## How to Test Ready-Made Samples
In the top-right header, click **"Full Stack SWE"** or **"Data Analyst"** to instantly populate a real-world Job Description and a matching student profile to test the ATS generation and scoring workflow in one click!
