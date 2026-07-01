# services/grading-service/app/main.py
import logging
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from services.common import settings, configure_logging, register_exception_handlers
from services.common.middleware import RateLimitMiddleware, RequestLoggingMiddleware

# Initialize structured logging
configure_logging()
logger = logging.getLogger(__name__)

# Base application with configuration settings loaded
app = FastAPI(
    title="HR-Copilot Grading & Report Service",
    description="Evaluation engines generating final scoring matrices and candidate feedback report sheets.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Centralized exception handlers registration
register_exception_handlers(app)

# Security and request logs middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptItem(BaseModel):
    stage: str
    question: str
    response: str
    score: float
    feedback: str

class GradeRequest(BaseModel):
    session_id: str
    candidate_name: str
    job_title: str
    transcript: List[TranscriptItem]


@app.post("/api/v1/grade")
def grade_interview(req: GradeRequest):
    logger.info(f"Received grading request for session: {req.session_id}")
    
    # Calculate overall average score
    if not req.transcript:
        overall_score = 0.0
    else:
        overall_score = round(sum(item.score for item in req.transcript) / len(req.transcript), 1)

    # Simple logic mapping skill groups
    tech_skills = {}
    behavioral_skills = {"Communication": 7.0, "Problem Solving": 7.0}
    
    for item in req.transcript:
        if item.stage in ["MCQ", "CODING"]:
            tech_skills[item.stage] = item.score
        else:
            behavioral_skills[item.stage] = item.score

    # Determine hiring recommendation verdict
    if overall_score >= 8.0:
        verdict = "STRONG_HIRE"
    elif overall_score >= 6.0:
        verdict = "HIRE"
    elif overall_score >= 4.0:
        verdict = "NO_HIRE"
    else:
        verdict = "STRONG_NO_HIRE"

    # Save details structure
    report_data = {
        "session_id": req.session_id,
        "candidate_name": req.candidate_name,
        "job_title": req.job_title,
        "overall_score": overall_score,
        "technical_skills_matrix": tech_skills,
        "behavioral_skills_matrix": behavioral_skills,
        "summary_verdict": verdict
    }

    # Generate candidate scorecard PDF
    # We place temporary files under a dedicated folder in the workspace to follow permissions
    temp_dir = os.path.join("/tmp", "reports")
    os.makedirs(temp_dir, exist_ok=True)
    pdf_filename = os.path.join(temp_dir, f"scorecard_{req.session_id}.pdf")
    
    try:
        generate_pdf_report(pdf_filename, report_data, req.transcript)
        logger.info(f"Evaluation report generated successfully at: {pdf_filename}")
    except Exception as e:
        logger.error(f"Failed to generate scorecard PDF: {e}")
        raise HTTPException(status_code=500, detail="Error generating PDF report scorecard")

    return {
        "report": report_data,
        "pdf_download_url": f"/api/v1/reports/download/{req.session_id}"
    }


@app.get("/api/v1/reports/download/{session_id}")
def download_report(session_id: str):
    pdf_path = f"/tmp/reports/scorecard_{session_id}.pdf"
    if not os.path.exists(pdf_path):
        logger.warning(f"Download rejected. Report not found for session: {session_id}")
        raise HTTPException(status_code=404, detail="Scorecard PDF report not found.")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"Scorecard_{session_id}.pdf")


def generate_pdf_report(filename: str, report: Dict[str, Any], transcript: List[TranscriptItem]):
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Palette Styling
    primary_color = colors.HexColor("#1A365D")   # Deep navy
    secondary_color = colors.HexColor("#2B6CB0") # Medium blue
    text_color = colors.HexColor("#2D3748")      # Charcoal
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=primary_color,
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        textColor=text_color,
        leading=14
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=secondary_color,
        spaceBefore=15,
        spaceAfter=8
    )

    elements = []
    
    # Title
    elements.append(Paragraph(f"HR-Copilot Interview Evaluation", title_style))
    elements.append(Spacer(1, 10))
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Candidate Name:</b>", body_style), Paragraph(report["candidate_name"], body_style),
         Paragraph("<b>Date:</b>", body_style), Paragraph("July 1, 2026", body_style)],
        [Paragraph("<b>Target Job Profile:</b>", body_style), Paragraph(report["job_title"], body_style),
         Paragraph("<b>Overall Score:</b>", body_style), Paragraph(f"<b>{report['overall_score']}/10.0</b>", body_style)],
        [Paragraph("<b>Hiring Verdict:</b>", body_style), Paragraph(f"<font color='green'><b>{report['summary_verdict']}</b></font>", body_style),
         Paragraph("<b>Session ID:</b>", body_style), Paragraph(report["session_id"][:8], body_style)]
    ]
    
    t = Table(meta_data, colWidths=[120, 180, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Skills Matrix Headers
    elements.append(Paragraph("Evaluated Skill Matrix Details", h2_style))
    
    skill_data = [["Skill Category", "Score / 10.0"]]
    for k, v in report["technical_skills_matrix"].items():
        skill_data.append([f"Technical: {k}", f"{v}/10.0"])
    for k, v in report["behavioral_skills_matrix"].items():
        skill_data.append([f"Behavioral: {k}", f"{v}/10.0"])
        
    st = Table(skill_data, colWidths=[300, 200])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(st)
    elements.append(Spacer(1, 20))
    
    # Transcripts Summary details
    elements.append(Paragraph("Question & Answer Log Details", h2_style))
    for index, item in enumerate(transcript):
        elements.append(Paragraph(f"<b>Round {index+1} ({item.stage})</b>", body_style))
        elements.append(Paragraph(f"<b>Q:</b> {item.question}", body_style))
        elements.append(Paragraph(f"<b>A:</b> {item.response}", body_style))
        elements.append(Paragraph(f"<i>Feedback Score: {item.score}/10 - {item.feedback}</i>", body_style))
        elements.append(Spacer(1, 10))
        
    doc.build(elements)


# System Health and Probe Endpoints
@app.get("/health", tags=["System"])
@app.get("/live", tags=["System"])
def liveness_check():
    """
    Liveness probe ensuring the web server process is running.
    """
    return {"status": "healthy", "service": "grading-service"}


@app.get("/ready", tags=["System"])
def readiness_check():
    """
    Readiness probe validating underlying resource availability.
    Since grading-service is pure compute/stateless, it is ready if liveness check passes.
    """
    return {"status": "ready", "service": "grading-service"}


@app.get("/version", tags=["System"])
def version():
    """
    Returns API version.
    """
    return {"version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
