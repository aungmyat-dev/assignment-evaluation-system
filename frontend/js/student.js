/* Design philosophy: student data is presented as an editorial reading surface — one primary story, then the measurable evidence behind it. */
import { api, clearSession, currentUser } from "./api.js";

const user = currentUser();
if (!user || user.role !== "student") window.location.href = "index.html";
const $ = selector => document.querySelector(selector);
let assignments = [];
let submissions = [];
const formatDate = value =>
  value
    ? new Date(value).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "—";
function toast(text) {
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = text;
  $("#toast-root").append(node);
  setTimeout(() => node.remove(), 3200);
}
function scoreClass(score) {
  return score >= 70 ? "good" : score >= 50 ? "warn" : "risk";
}
function renderStats() {
  const evaluated = submissions.filter(item => item.evaluation);
  const scores = evaluated.map(
    item => item.evaluation.final_score ?? item.evaluation.predicted_score
  );
  $("#stat-submissions").textContent = submissions.length;
  $("#stat-average").textContent = scores.length
    ? `${Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)}`
    : "—";
  $("#stat-review").textContent = submissions.filter(
    item => item.status === "flagged"
  ).length;
  $("#stat-latest").textContent = scores.length
    ? `${Math.round(scores[0])}`
    : "—";
}
function renderRows() {
  const body = $("#submissions-body");
  if (!submissions.length) {
    body.innerHTML =
      '<tr><td colspan="5"><div class="empty">No submissions yet. Upload your first piece of work to begin the evaluation trail.</div></td></tr>';
    return;
  }
  body.innerHTML = submissions
    .map(item => {
      const score =
        item.evaluation?.final_score ?? item.evaluation?.predicted_score;
      return `<tr><td><strong>${item.assignment_title || "Assignment"}</strong><br><span class="small">${item.original_filename}</span></td><td>${formatDate(item.submitted_at)}</td><td><span class="status ${item.status}">${item.status}</span></td><td class="score ${scoreClass(score || 0)}">${score == null ? "—" : Math.round(score)}</td><td><button class="btn btn-quiet view-feedback" data-id="${item.id}">Inspect</button></td></tr>`;
    })
    .join("");
  document
    .querySelectorAll(".view-feedback")
    .forEach(button =>
      button.addEventListener("click", () =>
        showFeedback(Number(button.dataset.id))
      )
    );
}
function showFeedback(id) {
  const item = submissions.find(entry => entry.id === id);
  if (!item?.evaluation) return;
  const result = item.evaluation;
  $("#feedback-title").textContent =
    `${item.assignment_title} · ${formatDate(item.evaluated_at)}`;
  $("#feedback-content").innerHTML =
    `<div class="metric"><label>Predicted score</label><strong class="score ${scoreClass(result.predicted_score)}">${Math.round(result.predicted_score)} / 100</strong><div class="progress"><span style="width:${result.predicted_score}%"></span></div></div><div class="metric"><label>Keyword coverage</label><strong>${Math.round(result.keyword_coverage)}%</strong><div class="progress"><span style="width:${result.keyword_coverage}%"></span></div></div><div class="metric"><label>Reference similarity</label><strong>${Math.round(result.reference_similarity)}%</strong><div class="progress"><span style="width:${result.reference_similarity}%"></span></div></div><div class="metric"><label>Vocabulary richness</label><strong>${Math.round(result.vocabulary_richness)}%</strong><div class="progress"><span style="width:${Math.min(result.vocabulary_richness, 100)}%"></span></div></div><h3 style="font-size:13px;margin:24px 0 8px">Revision notes</h3><ul class="small" style="line-height:1.8;padding-left:18px">${(result.feedback || []).map(note => `<li>${note}</li>`).join("")}</ul>${result.teacher_comment ? `<div class="alert alert-info" style="margin-top:16px"><strong>Teacher note:</strong> ${result.teacher_comment}</div>` : ""}`;
  $("#feedback").scrollIntoView({ behavior: "smooth", block: "start" });
}
function fillAssignments() {
  $("#assignment-select").innerHTML =
    assignments
      .map(item => `<option value="${item.id}">${item.title}</option>`)
      .join("") || '<option value="">No assignments available</option>';
}
async function load() {
  try {
    [assignments, submissions] = await Promise.all([
      api.assignments(),
      api.submissions(),
    ]);
    renderStats();
    renderRows();
    fillAssignments();
    if (submissions[0]) showFeedback(submissions[0].id);
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
$("#upload-open").addEventListener("click", () =>
  $("#upload-modal").classList.remove("hidden")
);
$("#upload-close").addEventListener("click", () =>
  $("#upload-modal").classList.add("hidden")
);
$("#upload-modal").addEventListener("click", event => {
  if (event.target.id === "upload-modal")
    $("#upload-modal").classList.add("hidden");
});
$("#upload-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.target.querySelector("button");
  const message = $("#upload-message");
  button.disabled = true;
  button.textContent = "Reading and evaluating…";
  message.innerHTML = "";
  try {
    await api.uploadSubmission(
      Number($("#assignment-select").value),
      $("#submission-file").files[0]
    );
    $("#upload-modal").classList.add("hidden");
    event.target.reset();
    toast("Submission evaluated and added to your history.");
    await load();
  } catch (error) {
    message.innerHTML = `<div class="alert alert-error">${error.message}</div>`;
  } finally {
    button.disabled = false;
    button.innerHTML = "Evaluate submission <span>→</span>";
  }
});
load();
