# Intelligent Automated Assignment & Essay Evaluation System

## Architectural overview

The system uses a layered architecture that keeps the browser client independent from the FastAPI service. The frontend is composed only of HTML5, CSS3, and ES6 modules. The backend exposes JSON REST endpoints and owns authentication, persistence, file processing, NLP scoring, plagiarism analysis, and teacher approval workflows.

```text
+----------------------+       HTTPS / JSON + multipart       +-------------------------+
|  Vanilla JS client   | <----------------------------------> | FastAPI application     |
|  HTML5 + CSS3        |                                      |                         |
|                      |                                      |  Auth / role guards     |
|  Login / register    |                                      |  Assignment routes      |
|  Student dashboard   |                                      |  Submission routes      |
|  Teacher dashboard   |                                      |  Reporting routes       |
+----------+-----------+                                      +------------+------------+
           |                                                               |
           | browser localStorage JWT                                     |
           v                                                               v
+----------------------+                                      +-------------------------+
|  Responsive UI       |                                      | Domain services        |
|  Score cards         |                                      |                         |
|  Rubric forms        |                                      | PDF/text extraction     |
|  Plagiarism alerts   |                                      | NLP preprocessing       |
|  Approval controls   |                                      | TF-IDF + cosine         |
+----------------------+                                      | weighted scoring       |
                                                              +------------+------------+
                                                                           |
                                             +-----------------------------+------------------+
                                             |                                                |
                                             v                                                v
                                  +----------------------+                         +-------------------+
                                  | MySQL database       |                         | Upload storage    |
                                  | users                |                         | local filesystem  |
                                  | assignments          |                         | object storage*  |
                                  | submissions          |                         +-------------------+
                                  | evaluation_results   |
                                  | plagiarism_matches  |
                                  +----------------------+

* The reference implementation uses a configurable local upload directory. It can be replaced
  by S3-compatible storage without changing the domain model.
```

## Request workflow

1. A user registers or logs in. The API verifies the password hash and returns a short-lived JWT containing the user identifier and role.
2. A teacher creates an assignment with a reference answer, rubric criteria, keyword list, and word-count boundaries.
3. A student uploads a PDF or text document. The API validates the extension and size, stores the file, extracts text, and creates a `processing` submission record.
4. The evaluation service normalizes the text, compares it to the teacher's reference material, computes rubric and language metrics, and compares it with earlier submissions for plagiarism risk.
5. The API stores the score breakdown and similarity matches, then returns the submission as `evaluated` or `flagged` when the similarity threshold is exceeded.
6. Students can view their feedback report. Teachers can filter flagged submissions and approve or override the final grade.

## Evaluation model

The baseline score is intentionally transparent and explainable. The weighted components are keyword coverage (30%), reference similarity (30%), vocabulary richness (15%), and word-count appropriateness (25%). A separate plagiarism risk value is reported rather than silently reducing academic marks. Teachers remain the final authority through the approval and override workflow.

## Security boundaries

Authentication is implemented with JWT bearer tokens. Role checks are enforced server-side for every teacher-only and student-only endpoint. Uploaded files are written with generated names, constrained by an allowlist, and never interpreted as executable content. The API should be deployed behind TLS, with a strong production `JWT_SECRET`, restricted CORS origins, and a private upload directory.

## Deployment topology

For development, run Uvicorn on port 8000 and serve `frontend/` with any static file server. For production, place an HTTPS reverse proxy in front of Uvicorn, configure MySQL, use a managed object store for uploads, and serve the frontend from the same origin or a separately configured trusted origin.
