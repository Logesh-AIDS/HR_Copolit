# Stage 4 Transition Plan: Resume Upload & Document Management

This document outlines the transition plan and integration roadmap for linking the Stage 3 Identity & Access Management (IAM) module with **Stage 4: Resume Upload & Document Management**.

---

## 1. Context & Objectives

In Stage 4, the platform will support:
- Uploading PDF/DOCX resumes (Candidate).
- Extracting and parsing resume text (using SpaCy and vector databases).
- Storing documents in secure Object Storage (e.g., S3/Local simulated storage).
- Restricting document access based on user role (e.g. recruiters can read candidate resumes, but candidates can only view or delete their own resume).

The core authentication system built in Stage 3 acts as the gatekeeper for all document management operations.

---

## 2. Route Guard Integration

All REST endpoints in Stage 4 will utilize the security dependencies exposed in `services/common/auth`:

### Candidate Resume Upload
- **Route**: `POST /api/v1/resumes/upload`
- **Guard**: `Depends(RequireRole(["CANDIDATE"]))`
- **Implementation**:
  ```python
  from fastapi import APIRouter, Depends, UploadFile
  from services.common.auth import get_current_user, UserIdentity, RequireRole
  
  router = APIRouter(prefix="/resumes", tags=["Resumes"])
  
  @router.post("/upload")
  def upload_resume(
      file: UploadFile,
      current_user: UserIdentity = Depends(get_current_user),
      _ = Depends(RequireRole(["CANDIDATE"]))
  ):
      # Access user information securely via current_user.id
      candidate_id = current_user.id
      # Save file linked to candidate_id in database and storage...
  ```

### Recruiter Resume View
- **Route**: `GET /api/v1/resumes/{candidate_id}`
- **Guard**: `Depends(RequirePermission("resumes:view"))` or `Depends(RequireRole(["RECRUITER", "ADMINISTRATOR", "HIRING_MANAGER"]))`
- **Implementation**:
  Enforces that recruiters can search and view parsed resumes, while blocking candidates from viewing other applicants' documents.

---

## 3. Document Linkage in Database

In the SQLAlchemy schema, uploaded files and parsed metadata are linked directly to user accounts:

```sql
ALTER TABLE candidates 
    ADD CONSTRAINT fk_candidate_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

This link ensures:
1. **Self-Service Integrity**: When a candidate updates their profile or resume, they only mutate database entries corresponding to their `user_id` context.
2. **GDPR / Compliance Soft Delete**: When a candidate deletes their account (`DELETE /api/v1/profile/delete`), the cascade logic automatically flags their profiles and resume links as soft-deleted.

---

## 4. Key Security Rules for Stage 4

1. **Signed URLs for Resume Access**: Instead of making resume files publicly accessible in Object Storage, the service will generate short-lived signed URLs (e.g. 5 minutes expiry) only after verifying that the requesting user's `UserIdentity` is authorized.
2. **File Size and Type Limits**: The upload API must validate that file sizes do not exceed 5MB and extensions are strictly constrained to `.pdf`, `.docx`, and `.doc` to prevent Denial of Service (DoS) and malicious script execution.
3. **Payload Sanitization**: During extraction, text parsed from documents must be sanitized before passing it to vector indexes or database logs to mitigate injection vulnerabilities.
