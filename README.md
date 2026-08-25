# Intelligent Automated Assignment & Essay Evaluation System

This project is a framework-free educational technology application for transparent assignment evaluation. The browser client uses only HTML5, CSS3, and Vanilla JavaScript ES6 modules. The backend uses Python, FastAPI, SQLAlchemy, and Uvicorn. MySQL is the intended production database; the default development configuration uses SQLite so the project can be smoke-tested without a database server.

## Project structure

```text
assignment_evaluation_system/
├── ARCHITECTURE.md
├── PRESENTATION.md
├── requirements.txt
├── database/schema.sql
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── routes/
│   └── services/
├── frontend/
│   ├── index.html
│   ├── student_dashboard.html
│   ├── teacher_dashboard.html
│   ├── css/style.css
│   └── js/
└── uploads/
```

## Local setup

Create a virtual environment and install the Python dependencies.

```bash
cd /home/ubuntu/assignment_evaluation_system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the application configuration. The following development values are sufficient for a first run.

```bash
export DATABASE_URL='sqlite:///./assignment_evaluation.db'
export JWT_SECRET='replace-with-a-long-random-development-secret'
export UPLOAD_DIR='./uploads'
export CORS_ORIGINS='http://localhost:5500,http://127.0.0.1:5500'
```

Start the API from the project root.

```bash
uvicorn backend.main:app --reload --port 8000
```

In a second terminal, serve the frontend as static files. Python's built-in static server is sufficient for development.

```bash
python3 -m http.server 5500 --directory frontend
```

Open `http://localhost:5500/index.html`. The API documentation is available at `http://localhost:8000/docs`.

## MySQL configuration

Create the production database and tables using `database/schema.sql`, then point the service at a MySQL connection string.

```bash
export DATABASE_URL='mysql+pymysql://assignment_user:strong-password@127.0.0.1:3306/assignment_evaluation'
```

Use a dedicated database user with only the required application permissions. Set a high-entropy `JWT_SECRET`, configure a trusted HTTPS origin in `CORS_ORIGINS`, and move uploaded documents to private object storage before production deployment.

## API summary

| Area | Endpoint | Purpose |
|---|---|---|
| Authentication | `POST /api/auth/register` | Register a student or teacher |
| Authentication | `POST /api/auth/login` | Return a JWT bearer token |
| Authentication | `GET /api/auth/me` | Return the authenticated user |
| Assignments | `GET /api/assignments` | List role-visible assignments |
| Assignments | `POST /api/assignments` | Create a teacher assignment |
| Assignments | `PUT /api/assignments/{id}` | Update a teacher assignment |
| Submissions | `GET /api/submissions` | List student or teacher submissions |
| Submissions | `POST /api/submissions/upload` | Upload and evaluate a PDF/TXT file |
| Submissions | `GET /api/submissions/{id}` | Read an evaluation report |
| Plagiarism | `GET /api/submissions/{id}/matches` | Inspect flagged similarity matches |
| Approval | `PATCH /api/submissions/{id}/approve` | Approve or override a final grade |

## Evaluation interpretation

The automated score is an explainable predicted score, not a replacement for teacher judgment. It combines keyword coverage at 30%, reference similarity at 30%, vocabulary richness at 15%, and word-count appropriateness at 25%. Plagiarism risk is surfaced separately and does not silently subtract marks. A similarity match is flagged when cosine similarity meets the configured threshold.

## Production considerations

The reference implementation is intentionally suitable for a university final-year project and a controlled deployment. A production rollout should add database migrations, asynchronous job processing for large files, antivirus scanning, rate limiting, audit logging, encrypted object storage, stronger content validation, automated backups, and a formal human-in-the-loop policy for academic decisions. The UI uses a direct API base of `http://localhost:8000/api`; update `frontend/js/api.js` or define `window.API_BASE` before the module loads when deploying behind another origin.
