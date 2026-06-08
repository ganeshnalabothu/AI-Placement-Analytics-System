from flask import Flask, render_template, request
import os
import PyPDF2
import sqlite3
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
def create_database():
    conn = sqlite3.connect("placement_data.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            branch TEXT,
            skills TEXT,
            score INTEGER,
            company TEXT,
            company_match_score INTEGER,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()
create_database()


def extract_text_from_pdf(file_path):
    text = ""

    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text

    return text.lower()


@app.route("/", methods=["GET", "POST"])
def home():

    score = None
    suggestions = []
    name = ""
    detected_skills = []
    company_match_score = None
    missing_skills = []
    recommended_companies = []
    strength_level = ""

    if request.method == "POST":

        name = request.form["name"]
        branch = request.form["branch"]
        skills = request.form["skills"].lower()
        company = request.form.get("company", "").lower()

        resume_text = ""

        resume = request.files.get("resume")

        if resume and resume.filename != "":

            file_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                resume.filename
            )

            resume.save(file_path)

            resume_text = extract_text_from_pdf(file_path)

        score = 30

        required_skills = {
            "python": 15,
            "dsa": 15,
            "data structures": 15,
            "sql": 10,
            "dbms": 10,
            "flask": 10,
            "html": 5,
            "css": 5,
            "javascript": 5,
            "oops": 10,
            "os": 5,
            "cn": 5,
            "machine learning": 10,
            "pandas": 5,
            "numpy": 5
        }

        company_requirements = {
            "infosys": ["python", "sql", "dbms", "aptitude"],
            "tcs": ["java", "oops", "dbms", "aptitude"],
            "accenture": ["python", "sql", "communication", "aptitude"],
            "cognizant": ["java", "sql", "oops", "aptitude"],
            "wipro": ["java", "sql", "communication", "aptitude"],
            "capgemini": ["python", "sql", "dbms", "communication"],
            "deloitte": ["sql", "communication", "aptitude", "python"],
            "ibm": ["python", "sql", "dbms", "cloud"],
            "bosch": ["c", "c++", "oops", "dbms"],
            "hyundai": ["python", "sql", "dbms", "communication"],
            "amazon": ["python", "dsa", "algorithms", "system design"],
            "microsoft": ["dsa", "oops", "os", "system design"],
            "google": ["dsa", "algorithms", "os", "dbms"],
            "walmart": ["java", "dsa", "sql", "system design"],
            "flipkart": ["dsa", "java", "python", "sql"],
            "atlassian": ["dsa", "java", "system design", "cloud"],
            "oracle": ["java", "sql", "dbms", "oops"],
            "zoho": ["dsa", "c", "java", "sql"],
            "adobe": ["dsa", "algorithms", "oops", "system design"],
            "salesforce": ["java", "sql", "dbms", "communication"],
            "amd": ["c++", "os", "computer architecture", "dsa"],
            "infor": ["java", "sql", "dbms", "dsa"],
            "odoo": ["python", "postgresql", "html", "css"],
            "broadridge": ["java", "sql", "dbms", "dsa"],
            "meru data": ["python", "sql", "cloud", "communication"]
        }

        found_skills = []

        # Detect skills
        for skill, marks in required_skills.items():

            if skill in skills or skill in resume_text:

                score += marks
                found_skills.append(skill)
                detected_skills.append(skill)

        if score > 100:
            score = 100
        if score >= 90:
            strength_level = "Excellent"
        elif score >= 70:
            strength_level = "Good"
        elif score >= 50:
            strength_level = "Average"
        else:
            strength_level = "Needs Improvement"

        # Recommended companies
        for comp, req_skills in company_requirements.items():

            match_count = 0

            for skill in req_skills:

                if (
                    skill in found_skills
                    or skill in resume_text
                    or skill in skills
                ):
                    match_count += 1

            match_score = int(
                (match_count / len(req_skills)) * 100
            )

            if match_score >= 50:
                recommended_companies.append(
                    (comp, match_score)
                )

        recommended_companies.sort(
            key=lambda x: x[1],
            reverse=True
        )

        recommended_companies = recommended_companies[:5]

        # Selected company analysis
        if company in company_requirements:

            required_for_company = company_requirements[company]

            matched_count = 0

            for skill in required_for_company:

                if (
                    skill in found_skills
                    or skill in resume_text
                    or skill in skills
                ):
                    matched_count += 1
                else:
                    missing_skills.append(skill)

            company_match_score = int(
                (matched_count / len(required_for_company)) * 100
            )

        else:

            company_match_score = 0

            missing_skills.append(
                "Company not available apply for companies like tcs,wipro,accenture,infosys,capgemini,deloitte,ibm,bosch,hyundai,amazon,microsoft,google,walmart,flipkart,atlassian,oracle,zoho"
            )
        conn = sqlite3.connect("placement_data.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO students
            (name, branch, skills, score, company, company_match_score, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            branch,
            skills,
            score,
            company,
            company_match_score,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        # Suggestions
        if "python" not in found_skills:
            suggestions.append("Learn Python strongly")

        if (
            "dsa" not in found_skills
            and "data structures" not in found_skills
        ):
            suggestions.append(
                "Improve Data Structures and Algorithms"
            )

        if (
            "sql" not in found_skills
            and "dbms" not in found_skills
        ):
            suggestions.append(
                "Practice SQL and DBMS"
            )

        if "flask" not in found_skills:
            suggestions.append(
                "Add Flask project experience"
            )

        if len(suggestions) == 0:
            suggestions.append("Excellent profile")
            suggestions.append("Start mock interviews")
            suggestions.append("Add this project to your resume")

    return render_template(
        "index.html",
        score=score,
        suggestions=suggestions,
        name=name,
        detected_skills=detected_skills,
        company_match_score=company_match_score,
        missing_skills=missing_skills,
        recommended_companies=recommended_companies,
        strength_level=strength_level

    )
@app.route("/admin")
def admin():
    search = request.args.get("search", "")

    conn = sqlite3.connect("placement_data.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM students
            WHERE name LIKE ? OR company LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("SELECT * FROM students")

    records = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(score) FROM students")
    average_score = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(score) FROM students")
    highest_score = cursor.fetchone()[0]

    conn.close()

    if average_score is None:
        average_score = 0

    if highest_score is None:
        highest_score = 0

    return render_template(
        "admin.html",
        records=records,
        total_students=total_students,
        average_score=round(average_score, 2),
        highest_score=highest_score,
        search=search
    )


if __name__ == "__main__":
    app.run(debug=True)