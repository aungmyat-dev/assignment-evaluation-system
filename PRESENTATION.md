# Intelligent Automated Assignment & Essay Evaluation System

## Slide 1 — Project overview

The project is an educational technology platform that helps teachers evaluate essays and assignments with consistent, explainable signals. Students receive faster feedback while teachers retain control over the final academic decision.

## Slide 2 — Problem statement

Manual essay evaluation is time-consuming, difficult to standardize across a class, and often provides limited diagnostic feedback. Teachers also need a practical way to identify unusually similar submissions without treating automated similarity as a final plagiarism verdict.

## Slide 3 — Proposed solution

The system accepts PDF and text submissions, extracts and normalizes their content, compares responses against teacher-provided concepts, detects similarity across submissions, and presents a score breakdown with revision feedback. A role-aware dashboard separates student progress from teacher review and approval.

## Slide 4 — Solution architecture

The browser contains only HTML5, CSS3, and Vanilla ES6 JavaScript. FastAPI provides the REST API and JWT authentication. SQLAlchemy maps the domain to MySQL, while a configurable upload directory stores source documents. NLP and scoring remain in backend services so evaluation decisions are reproducible and testable.

## Slide 5 — Technology stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript ES6 modules, Fetch API |
| Backend | Python, FastAPI, Uvicorn |
| Persistence | MySQL with SQLAlchemy and PyMySQL |
| NLP | scikit-learn TF-IDF, cosine similarity, NLTK-compatible normalization |
| Document processing | pdfplumber and plain-text extraction |
| Security | JWT bearer authentication, bcrypt password hashing, role guards |

## Slide 6 — Key features

Students can register, sign in, upload assignments, view evaluation status, inspect score components, and read feedback. Teachers can create briefs with keywords and reference material, inspect class submissions, filter similarity alerts, and approve or override final grades with a comment.

## Slide 7 — Document processing pipeline

The upload service validates the extension and file size, stores the document under a generated filename, extracts text from PDF or TXT input, lowercases and tokenizes the text, removes common stop words, and passes the normalized representation to the evaluation engine.

```text
upload → validate → store → extract → normalize → score → compare → report
```

## Slide 8 — Machine-learning algorithms

TF-IDF represents the relative importance of terms and bigrams in each document. Cosine similarity compares the direction of two TF-IDF vectors. The same approach is used for reference-answer alignment and pairwise student-submission comparison. Keyword coverage provides a direct, teacher-controlled concept signal.

## Slide 9 — Scoring algorithm

The explainable predicted score is calculated as:

```text
score = 0.30(keyword coverage)
      + 0.30(reference similarity)
      + 0.15(vocabulary richness)
      + 0.25(word-count appropriateness)
```

Plagiarism risk is presented as an independent percentage so a teacher can investigate context instead of receiving an opaque penalty.

## Slide 10 — Results and evaluation plan

A university evaluation should compare the automated score with teacher scores on a labelled sample, measure precision and recall for high-similarity alerts, record average API evaluation time, and collect student/teacher usability feedback. The transparent metrics make it possible to identify whether errors originate in extraction, concept coverage, reference alignment, or similarity detection.

## Slide 11 — Future enhancements

Potential extensions include asynchronous evaluation jobs, sentence-level evidence highlighting, multilingual lemmatization, semantic embeddings, rubric criterion scoring, secure object storage, antivirus checks, audit trails, model calibration using teacher-labelled data, and integrations with learning-management systems.

## Slide 12 — Conclusion

The system demonstrates how a lightweight, explainable NLP pipeline can support academic workflows without removing teacher judgment. Its framework-free frontend and modular FastAPI backend make the project approachable for a final-year implementation while leaving clear paths toward stronger production controls and richer language models.
