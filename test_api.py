import io
from fastapi.testclient import TestClient
from server import app, SAMPLE_DATA

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "ResumeForge" in response.text
    print("[+] GET / passed.")

def test_sample_data():
    response = client.get("/api/sample-data")
    assert response.status_code == 200
    data = response.json()
    assert "software_engineer" in data
    assert "data_analyst" in data
    print("[+] GET /api/sample-data passed.")

def test_generate_resume_endpoint():
    swe_sample = SAMPLE_DATA["software_engineer"]
    payload = {
        "jd_text": swe_sample["jd_text"],
        "student_data": swe_sample["student_cv"]
    }
    response = client.post("/api/generate-ats-resume", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    resume = res["resume"]
    assert "ats_score" in resume
    assert resume["ats_score"]["overall_score"] >= 60
    print(f"[+] POST /api/generate-ats-resume passed. Overall score: {resume['ats_score']['overall_score']}%")

    # Test DOCX download
    docx_res = client.post("/api/download-docx", json={"resume": resume})
    assert docx_res.status_code == 200
    assert len(docx_res.content) > 1000
    print(f"[+] POST /api/download-docx passed. File size: {len(docx_res.content)} bytes.")

def test_recalculate_score_endpoint():
    swe_sample = SAMPLE_DATA["software_engineer"]
    payload = {
        "resume_text": "Alex Rivera - Software Engineer\nSkills: Python, React, SQL, Docker, AWS, PostgreSQL\nExperience: Built microservices using Python and Docker.",
        "jd_text": swe_sample["jd_text"],
        "skills": ["Python", "React", "Docker", "AWS", "SQL"]
    }
    response = client.post("/api/recalculate-score", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "overall_score" in res["score"]
    print(f"[+] POST /api/recalculate-score passed. Score: {res['score']['overall_score']}%")

def test_cv_upload_endpoint():
    # Test uploading a plain text resume
    sample_cv_text = """John Doe
john.doe@email.com | +1 (555) 123-4567 | San Francisco, CA | linkedin.com/in/johndoe
Target Role: Software Engineer

Professional Summary
Passionate software engineer with hands-on experience in full-stack web applications.

Skills
Python, JavaScript, React, Node.js, SQL, Git, Docker

Experience
Software Engineer Intern - Tech Corp (2024 - Present)
- Developed REST APIs and improved database performance by 25%.
- Implemented frontend components using React.

Education
B.S. in Computer Science - University of California (2021 - 2025)
"""
    files = {
        "file": ("resume.txt", sample_cv_text.encode("utf-8"), "text/plain")
    }
    response = client.post("/api/parse-cv", files=files)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    parsed = res["parsed"]
    assert parsed["full_name"] == "John Doe"
    assert parsed["email"] == "john.doe@email.com"
    assert "Python" in parsed["skills"] or "python" in [s.lower() for s in parsed["skills"]]
    print(f"[+] POST /api/parse-cv passed. Extracted: {parsed['full_name']} with {len(parsed['skills'])} skills.")

if __name__ == "__main__":
    print("\n--- Testing FastAPI Endpoints ---")
    test_root()
    test_sample_data()
    test_generate_resume_endpoint()
    test_recalculate_score_endpoint()
    test_cv_upload_endpoint()
    print("\n[ALL API TESTS PASSED!]\n")
