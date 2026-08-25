/* Design philosophy: teacher controls are decision surfaces, not decoration. The model's confidence and risk signals stay visible beside the human approval action. */
import { api, clearSession, currentUser } from "./api.js";
const user = currentUser();
if (!user || user.role !== "teacher") window.location.href = "index.html";
const $ = selector => document.querySelector(selector);
let assignments = [];
let submissions = [];
let activeReview = null;
const scoreClass = score =>
  score >= 70 ? "good" : score >= 50 ? "warn" : "risk";
function toast(text) {
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = text;
  $("#toast-root").append(node);
  setTimeout(() => node.remove(), 3200);
}
function renderStats() {
  const evaluated = submissions.filter(item => item.evaluation);
  const scores = evaluated.map(
    item => item.evaluation.final_score ?? item.evaluation.predicted_score
  );
  $("#stat-average").textContent = scores.length
    ? `${Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)}`
    : "—";
  $("#stat-evaluated").textContent = evaluated.length;
  $("#stat-flagged").textContent = submissions.filter(
    item => item.status === "flagged"
  ).length;
  $("#stat-assignments").textContent = assignments.length;
}
function renderAssignments() {
  $("#assignment-list").innerHTML = assignments.length
    ? assignments
        .map(
          item =>
            `<div style="padding:12px 0;border-bottom:1px solid var(--line)"><strong style="font-size:13px">${item.title}</strong><div class="small" style="margin-top:5px">${item.min_words}–${item.max_words} words · ${(item.keywords || []).length} keywords</div><div class="small" style="margin-top:5px">${item.description || "No brief description added."}</div></div>`
        )
        .join("")
    : '<div class="empty">No assignments yet. Create the first brief.</div>';
}
function renderRows() {
  const filter = $("#status-filter").value;
  const rows = submissions.filter(
    item => filter === "all" || item.status === filter
  );
  const body = $("#submissions-body");
  if (!rows.length) {
    body.innerHTML =
      '<tr><td colspan="6"><div class="empty">Nothing matches this review view.</div></td></tr>';
    return;
  }
  body.innerHTML = rows
    .map(item => {
      const score =
        item.evaluation?.final_score ?? item.evaluation?.predicted_score;
      const risk = item.evaluation?.plagiarism_risk || 0;
      return `<tr><td><strong>${item.student_name || "Student"}</strong><br><span class="small">${item.original_filename}</span></td><td>${item.assignment_title || "Assignment"}</td><td class="score ${scoreClass(score || 0)}">${score == null ? "—" : Math.round(score)}</td><td class="score ${risk >= 75 ? "risk" : risk >= 45 ? "warn" : "good"}">${Math.round(risk)}%</td><td><span class="status ${item.status}">${item.status}</span></td><td><button class="btn btn-quiet review-btn" data-id="${item.id}">Review</button></td></tr>`;
    })
    .join("");
  document
    .querySelectorAll(".review-btn")
    .forEach(button =>
      button.addEventListener("click", () =>
        openReview(Number(button.dataset.id))
      )
    );
}
function openReview(id) {
  activeReview = submissions.find(item => item.id === id);
  if (!activeReview) return;
  const studentTextEl = document.getElementById("modal-student-text");
  if (studentTextEl) {
    studentTextEl.innerText =
      activeReview.extracted_text ||
      activeReview.file_content ||
      activeReview.content ||
      "No text content available";
  }
  const result = activeReview.evaluation || {};
  $("#review-title").textContent =
    activeReview.assignment_title || "Submission";
  $("#review-subtitle").textContent =
    `${activeReview.student_name || "Student"} · ${activeReview.original_filename}`;
  $("#final-score").value = result.final_score ?? "";
  $("#teacher-comment").value = result.teacher_comment || "";
  $("#review-content").innerHTML =
    `<div class="grid" style="grid-template-columns:repeat(3,1fr);margin:18px 0"><div class="card"><div class="stat-label">Predicted</div><div class="stat-number" style="font-size:28px">${result.predicted_score == null ? "—" : Math.round(result.predicted_score)}</div></div><div class="card"><div class="stat-label">Similarity risk</div><div class="stat-number ${result.plagiarism_risk >= 75 ? "score risk" : ""}" style="font-size:28px">${Math.round(result.plagiarism_risk || 0)}%</div></div><div class="card"><div class="stat-label">Coverage</div><div class="stat-number" style="font-size:28px">${Math.round(result.keyword_coverage || 0)}%</div></div></div><div class="alert ${result.plagiarism_risk >= 75 ? "alert-error" : "alert-info"}">${result.plagiarism_risk >= 75 ? "<strong>Similarity alert:</strong> compare the flagged phrases before approving." : "<strong>Automated reading:</strong> no high-risk similarity match was recorded."}</div><h3 style="font-size:13px;margin:20px 0 8px">Automated feedback</h3><ul class="small" style="line-height:1.8;padding-left:18px">${(result.feedback || []).map(note => `<li>${note}</li>`).join("")}</ul>`;
  $("#review-modal").classList.remove("hidden");
}
async function load() {
  try {
    [assignments, submissions] = await Promise.all([
      api.assignments(),
      api.submissions(),
    ]);
    renderStats();
    renderAssignments();
    renderRows();
  } catch (error) {
    toast(error.message);
  }
}
$("#user-name").textContent = user.full_name;
$("#sidebar-name").textContent = user.full_name;
$("#today").textContent = new Date().toLocaleDateString(undefined, {
  month: "short",
  day: "numeric",
});
$("#logout").addEventListener("click", () => {
  clearSession();
  window.location.href = "index.html";
});
$("#status-filter").addEventListener("change", renderRows);
$("#assignment-open").addEventListener("click", () =>
  $("#assignment-modal").classList.remove("hidden")
);
$("#assignment-close").addEventListener("click", () =>
  $("#assignment-modal").classList.add("hidden")
);
$("#review-close").addEventListener("click", () =>
  $("#review-modal").classList.add("hidden")
);
document.querySelectorAll(".modal-backdrop").forEach(modal =>
  modal.addEventListener("click", event => {
    if (event.target === modal) modal.classList.add("hidden");
  })
);
$("#assignment-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.target.querySelector("button");
  button.disabled = true;
  button.textContent = "Creating…";
  try {
    await api.createAssignment({
      title: $("#assignment-title").value,
      description: $("#assignment-description").value,
      min_words: Number($("#assignment-min").value),
      max_words: Number($("#assignment-max").value),
      keywords: $("#assignment-keywords")
        .value.split(",")
        .map(value => value.trim())
        .filter(Boolean),
      reference_answer: $("#assignment-reference").value,
      rubric: {},
    });
    $("#assignment-modal").classList.add("hidden");
    event.target.reset();
    toast("Assignment brief created.");
    await load();
  } catch (error) {
    $("#assignment-message").innerHTML =
      `<div class="alert alert-error">${error.message}</div>`;
  } finally {
    button.disabled = false;
    button.innerHTML = "Create assignment <span>→</span>";
  }
});
$("#approval-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (!activeReview) return;
  const button = event.target.querySelector("button");
  button.disabled = true;
  button.textContent = "Saving…";
  try {
    const finalValue = $("#final-score").value.trim();
    await api.approve(activeReview.id, {
      final_score: finalValue === "" ? null : Number(finalValue),
      teacher_comment: $("#teacher-comment").value,
    });
    $("#review-modal").classList.add("hidden");
    toast("Review decision saved.");
    await load();
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.innerHTML = "Save review decision <span>→</span>";
  }
});
load();
