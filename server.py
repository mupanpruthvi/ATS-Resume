import io
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from parsers import (
    extract_text_from_pdf,
    extract_text_from_docx,
    scrape_job_description,
    parse_resume_sections,
    clean_text
)
from ats_engine import (
    calculate_ats_score,
    generate_ats_tailored_resume,
    generate_docx_resume,
    analyze_job_description
)

app = FastAPI(title="ATS Resume Generator & Matcher", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str

class GenerateRequest(BaseModel):
    jd_text: str
    student_data: Dict[str, Any]

class RecalculateRequest(BaseModel):
    resume_text: str
    jd_text: str
    skills: Optional[List[str]] = []

# Sample Job Descriptions and Matching Student Profiles
SAMPLE_DATA = {
    "software_engineer": {
        "title": "Junior Full Stack Software Engineer",
        "company": "CloudScale Innovations",
        "jd_text": """Role: Junior Full Stack Software Engineer
Location: Hybrid / Remote

About The Role:
We are seeking an enthusiastic Junior Full Stack Engineer to join our core product engineering team. You will build and scale customer-facing web applications, contribute to microservices architecture, and integrate cutting-edge APIs.

Key Responsibilities:
• Design, implement, and maintain responsive front-end user interfaces using React, TypeScript, and modern CSS/Tailwind.
• Develop robust, high-performance back-end RESTful APIs and microservices using Python (FastAPI/Django) and Node.js.
• Write clean, testable, and maintainable code adhering to Agile, TDD, and CI/CD best practices.
• Optimize relational databases (PostgreSQL, MySQL) and caching systems (Redis) for high throughput.
• Collaborate with cross-functional teams in daily stand-ups, code reviews, and architectural discussions.
• Containerize services using Docker and assist in deploying onto AWS cloud infrastructure.

Required Qualifications & Skills:
• Bachelor’s degree in Computer Science, Software Engineering, or related technical field (or equivalent practical experience).
• Strong proficiency in Python, JavaScript, and TypeScript.
• Practical experience with React.js, HTML5, CSS3, and RESTful APIs.
• Familiarity with SQL and relational databases such as PostgreSQL or MySQL.
• Experience using Git and GitHub for collaborative version control.
• Understanding of containerization concepts using Docker.
• Excellent problem-solving, communication, and team collaboration skills.

Nice to Have:
• Experience with cloud platforms (AWS / GCP / Azure).
• Familiarity with CI/CD pipelines (GitHub Actions) and automated unit testing.
• Knowledge of NoSQL databases like MongoDB or Redis.""",
        "student_cv": {
            "full_name": "Alex Rivera",
            "email": "alex.rivera@cs.university.edu",
            "phone": "+1 (555) 432-8765",
            "location": "Boston, MA",
            "linkedin": "linkedin.com/in/alexrivera-dev",
            "github": "github.com/alexrivera",
            "target_role": "Junior Full Stack Engineer",
            "summary": "Recent Computer Science graduate with hands-on experience building full-stack web applications using React, Python, and SQL. Passionate about writing clean, efficient code and developing scalable cloud solutions.",
            "skills": [
                "Python", "JavaScript", "React", "HTML5", "CSS3", "SQL", "PostgreSQL",
                "Git", "GitHub", "FastAPI", "Docker", "RESTful APIs", "Problem Solving"
            ],
            "education": [
                "B.S. in Computer Science | Northeastern University (2021 - 2025)\nGPA: 3.8/4.0 | Dean's Honors List\nRelevant Coursework: Algorithms & Data Structures, Database Systems, Web Development, Object-Oriented Design"
            ],
            "experience": [
                "Software Engineering Intern | NextWave Labs (May 2024 - Aug 2024)\n- Developed responsive frontend user features using React and REST APIs for client dashboard.\n- Built backend Python API endpoints to process user authentication and profile management.\n- Participated in weekly Agile scrums and peer code reviews."
            ],
            "projects": [
                "DevConnect Web Platform | React, Python, FastAPI, PostgreSQL\n- Engineered a developer networking platform allowing users to share technical repositories and collaborate.\n- Integrated JWT authentication and optimized database queries, reducing API response times by 32%.\n- Deployed application using Docker containers on cloud hosting.",
                "E-Commerce Micro-Store | JavaScript, HTML5, CSS3, Node.js\n- Built an interactive product catalog with search filtering, cart persistence, and checkout workflow.\n- Achieved 98+ Lighthouse performance score and full mobile responsiveness."
            ],
            "certifications": [
                "AWS Certified Cloud Practitioner (Foundational)",
                "Meta Front-End Developer Professional Certificate"
            ]
        }
    },
    "data_analyst": {
        "title": "Associate Data Analyst",
        "company": "InsightIQ Analytics",
        "jd_text": """Role: Associate Data Analyst
Location: New York, NY (Hybrid)

About the Job:
InsightIQ is looking for a detail-driven Data Analyst to transform complex datasets into actionable business intelligence reports. You will work closely with product managers and business stakeholders to uncover key insights.

Responsibilities:
• Collect, clean, and transform raw structured and unstructured data using Python, Pandas, and SQL.
• Design, develop, and maintain automated interactive dashboards in Tableau and Power BI.
• Formulate statistical tests, regression analysis, and cohort retention metrics to drive business decisions.
• Write complex SQL queries, CTEs, and window functions to query Snowflake and BigQuery data warehouses.
• Build automated ETL data pipelines and validate data integrity across reporting systems.
• Present data findings and executive summaries to department leaders.

Requirements:
• Degree in Data Science, Statistics, Mathematics, Economics, or Computer Science.
• Proficient in SQL (complex joins, aggregations, window functions).
• Hands-on programming proficiency in Python (Pandas, NumPy, Matplotlib, Seaborn).
• Experience building dashboards in Tableau, Power BI, or Looker.
• Strong foundation in statistical analysis, hypothesis testing, and exploratory data analysis.
• Exceptional analytical thinking and communication skills.""",
        "student_cv": {
            "full_name": "Priya Sharma",
            "email": "priya.sharma@analytics.edu",
            "phone": "+1 (555) 789-1234",
            "location": "New York, NY",
            "linkedin": "linkedin.com/in/priyasharma-data",
            "github": "github.com/priyasharma-analytics",
            "target_role": "Associate Data Analyst",
            "summary": "Data Analyst with a solid mathematical foundation and expertise in Python data wrangling, advanced SQL query design, and interactive dashboard creation. Skilled in turning raw data into strategic insights.",
            "skills": [
                "Python", "SQL", "Pandas", "NumPy", "Tableau", "Power BI", "Data Analysis",
                "Data Visualization", "Matplotlib", "Seaborn", "Excel", "Git", "Problem Solving"
            ],
            "education": [
                "B.S. in Data Analytics & Statistics | Columbia University (2021 - 2025)\nRelevant Coursework: Applied Statistics, Database Management, Python for Data Science, Business Analytics"
            ],
            "experience": [
                "Data Analytics Intern | MarketMetrics (June 2024 - Dec 2024)\n- Cleaned and prepared large customer transaction datasets comprising over 200,000 records using Python and Pandas.\n- Designed 4 automated Tableau dashboards tracking weekly KPI performance for executive stakeholders.\n- Formulated cohort analysis that identified an 18% improvement opportunity in user retention."
            ],
            "projects": [
                "Customer Churn Prediction & Analysis | Python, Pandas, Scikit-learn, SQL\n- Conducted exploratory data analysis on a 50k customer dataset to determine leading churn factors.\n- Built predictive classification model achieving 84% precision and created actionable recommendations report.",
                "E-Commerce Sales Performance Dashboard | Tableau, SQL, Excel\n- Built an interactive multi-tab dashboard visualizing revenue trends, profit margins, and regional distribution.\n- Automated data refresh workflow reducing weekly report preparation time by 5 hours."
            ],
            "certifications": [
                "Google Data Analytics Professional Certificate",
                "Tableau Desktop Specialist"
            ]
        }
    }
}

@app.get("/api/sample-data")
async def get_sample_data():
    """Returns curated sample JDs and matching student profiles."""
    return SAMPLE_DATA

@app.post("/api/scrape-jd")
async def scrape_jd(payload: ScrapeRequest):
    """Scrapes job description text from a URL."""
    if not payload.url:
        raise HTTPException(status_code=400, detail="URL is required")
    result = scrape_job_description(payload.url)
    return result

@app.post("/api/parse-cv")
async def parse_cv(file: UploadFile = File(...)):
    """Upload and parse an existing CV file (PDF, DOCX, TXT)."""
    filename = file.filename.lower()
    content = await file.read()
    
    if filename.endswith(".pdf"):
        raw_text = extract_text_from_pdf(content)
    elif filename.endswith(".docx"):
        raw_text = extract_text_from_docx(content)
    elif filename.endswith(".txt"):
        raw_text = clean_text(content.decode("utf-8", errors="ignore"))
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Please upload .pdf, .docx, or .txt file.")
        
    parsed = parse_resume_sections(raw_text)
    return {
        "success": True,
        "filename": file.filename,
        "parsed": parsed
    }

@app.post("/api/generate-ats-resume")
async def generate_resume(payload: GenerateRequest):
    """
    Generates an ATS-tailored resume based on the Job Description and student data.
    Computes ATS score, keyword breakdown, and tailored sections.
    """
    if not payload.jd_text or len(payload.jd_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Job description text is required.")
        
    tailored_resume = generate_ats_tailored_resume(payload.student_data, payload.jd_text)
    return {
        "success": True,
        "resume": tailored_resume
    }

@app.post("/api/recalculate-score")
async def recalculate_score(payload: RecalculateRequest):
    """Recalculates the ATS score when user manually edits their resume."""
    score = calculate_ats_score(payload.resume_text, payload.jd_text, payload.skills)
    return {
        "success": True,
        "score": score
    }

@app.post("/api/download-docx")
async def download_docx(payload: Dict[str, Any]):
    """Generates and downloads an ATS-compliant Word (.docx) document."""
    resume_data = payload.get("resume")
    if not resume_data:
        raise HTTPException(status_code=400, detail="Resume data is required.")
        
    docx_stream = generate_docx_resume(resume_data)
    filename = f"ATS_Resume_{resume_data.get('contact', {}).get('full_name', 'Candidate').replace(' ', '_')}.docx"
    
    return StreamingResponse(
        docx_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# Static directory for frontend assets
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serves the main application page."""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>ATS Resume Generator Backend Ready</h1>")
