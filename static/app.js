// Global State
const state = {
  currentStep: 1,
  jdText: "",
  studentData: {
    full_name: "",
    email: "",
    phone: "",
    location: "",
    linkedin: "",
    github: "",
    target_role: "",
    summary: "",
    skills: [],
    experience: [],
    projects: [],
    education: [],
    certifications: [],
    raw_text: ""
  },
  generatedResume: null,
  sampleData: null,
  isEditing: false
};

// DOM Content Loaded
document.addEventListener("DOMContentLoaded", async () => {
  initEventListeners();
  await loadSampleData();
  
  // Set default sample buttons
  document.getElementById("btn-sample-swe").addEventListener("click", () => applySample("software_engineer"));
  document.getElementById("btn-sample-da").addEventListener("click", () => applySample("data_analyst"));
});

// Initialize UI Event Listeners
function initEventListeners() {
  const jdInput = document.getElementById("jd-text-input");
  jdInput.addEventListener("input", () => {
    state.jdText = jdInput.value;
    updateWordCount(jdInput.value);
    previewDetectedJdSkills(jdInput.value);
  });

  // Skills input enter key
  const skillInput = document.getElementById("skill-tag-input");
  skillInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkillFromInput();
    }
  });

  // Drag & Drop for CV Upload
  const dropzone = document.getElementById("cv-dropzone");
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
      handleCvFile(files[0]);
    }
  });
}

// Load Curated Sample Data from Server
async function loadSampleData() {
  try {
    const res = await fetch("/api/sample-data");
    state.sampleData = await res.json();
  } catch (err) {
    console.warn("Could not load sample data:", err);
  }
}

// Apply Sample Role (Software Engineer or Data Analyst)
function applySample(key) {
  if (!state.sampleData || !state.sampleData[key]) return;
  const sample = state.sampleData[key];

  // Set JD
  state.jdText = sample.jd_text;
  document.getElementById("jd-text-input").value = sample.jd_text;
  updateWordCount(sample.jd_text);
  previewDetectedJdSkills(sample.jd_text);

  // Set Student Data
  const cv = sample.student_cv;
  state.studentData = { ...cv };
  populateProfileForm(cv);

  showToast(`Loaded sample: ${sample.title}`, "info");
  goToStep(1);
}

// Navigation between Steps (1, 2, 3)
function goToStep(stepNumber) {
  state.currentStep = stepNumber;

  // Update Nav Bar UI
  [1, 2, 3].forEach(step => {
    const navItem = document.getElementById(`step-nav-step-${step}` || `step-nav-${step}`);
    const section = document.getElementById(`step-${step}`);
    if (navItem) {
      navItem.classList.remove("active", "completed");
      if (step === stepNumber) {
        navItem.classList.add("active");
      } else if (step < stepNumber) {
        navItem.classList.add("completed");
      }
    }
    if (section) {
      section.style.display = (step === stepNumber) ? "block" : "none";
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function validateAndGoToStep(stepNumber) {
  if (stepNumber === 2) {
    const text = document.getElementById("jd-text-input").value.trim();
    if (!text || text.length < 30) {
      showToast("Please enter or fetch a valid Job Description first (at least 30 characters).", "warning");
      return;
    }
    state.jdText = text;
  }
  goToStep(stepNumber);
}

// Mode toggle for JD (Text vs URL)
function switchJdMode(mode) {
  document.getElementById("tab-jd-text").classList.toggle("active", mode === "text");
  document.getElementById("tab-jd-url").classList.toggle("active", mode === "url");
  document.getElementById("panel-jd-text").style.display = (mode === "text") ? "block" : "none";
  document.getElementById("panel-jd-url").style.display = (mode === "url") ? "block" : "none";
}

// Fetch Job Description from URL
async function fetchJdFromUrl() {
  const urlInput = document.getElementById("jd-url-input");
  const url = urlInput.value.trim();
  if (!url) {
    showToast("Please enter a valid job posting URL.", "warning");
    return;
  }

  const btn = document.getElementById("btn-fetch-url");
  const spinner = btn.querySelector(".spinner");
  const btnText = btn.querySelector(".btn-text");

  spinner.style.display = "inline-block";
  btnText.textContent = "Scraping...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/scrape-jd", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    const data = await res.json();

    if (data.success && data.text) {
      state.jdText = data.text;
      document.getElementById("jd-text-input").value = data.text;
      updateWordCount(data.text);
      previewDetectedJdSkills(data.text);
      switchJdMode("text");
      showToast(`Successfully extracted job details: "${data.title}"`, "success");
      if (data.warning) {
        showToast(data.warning, "warning");
      }
    } else {
      showToast(data.error || "Failed to fetch text from this URL. Try copying and pasting the text.", "danger");
    }
  } catch (err) {
    showToast("Error connecting to server. Please paste the JD directly.", "danger");
  } finally {
    spinner.style.display = "none";
    btnText.textContent = "Extract Job Details";
    btn.disabled = false;
  }
}

function updateWordCount(text) {
  const words = text ? text.trim().split(/\s+/).filter(Boolean).length : 0;
  document.getElementById("jd-word-count").textContent = `${words} words`;
}

function previewDetectedJdSkills(text) {
  const box = document.getElementById("jd-detected-box");
  const container = document.getElementById("jd-detected-tags");
  if (!text || text.length < 50) {
    box.style.display = "none";
    return;
  }

  // Common tech keywords to quickly preview
  const sampleKeywords = [
    "python", "javascript", "typescript", "react", "node.js", "sql", "postgresql",
    "mysql", "docker", "aws", "git", "rest", "api", "html", "css", "c++", "java",
    "tableau", "pandas", "machine learning", "agile", "scrum", "cloud"
  ];

  const lower = text.toLowerCase();
  const matched = sampleKeywords.filter(k => lower.includes(k));

  if (matched.length) {
    container.innerHTML = matched.map(m => `<span class="skill-tag">${m.toUpperCase()}</span>`).join("");
    box.style.display = "block";
  } else {
    box.style.display = "none";
  }
}

// Handle CV File Upload (PDF, DOCX, TXT)
function handleCvFileUpload(event) {
  const file = event.target.files[0];
  if (file) handleCvFile(file);
}

async function handleCvFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const statusBar = document.getElementById("upload-status-bar");
  const fileNameDisp = document.getElementById("uploaded-file-name");

  fileNameDisp.textContent = `Parsing ${file.name}...`;
  statusBar.style.display = "flex";

  try {
    const res = await fetch("/api/parse-cv", {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (data.success && data.parsed) {
      fileNameDisp.textContent = file.name;
      const parsed = data.parsed;

      // Update state
      state.studentData.full_name = parsed.full_name || state.studentData.full_name;
      state.studentData.email = parsed.email || state.studentData.email;
      state.studentData.phone = parsed.phone || state.studentData.phone;
      state.studentData.linkedin = parsed.linkedin || state.studentData.linkedin;
      state.studentData.github = parsed.github || state.studentData.github;
      state.studentData.target_role = parsed.target_role || state.studentData.target_role;
      state.studentData.summary = parsed.summary || state.studentData.summary;
      state.studentData.skills = parsed.skills.length ? parsed.skills : state.studentData.skills;
      state.studentData.experience = parsed.experience.length ? parsed.experience : state.studentData.experience;
      state.studentData.projects = parsed.projects.length ? parsed.projects : state.studentData.projects;
      state.studentData.education = parsed.education.length ? parsed.education : state.studentData.education;
      state.studentData.certifications = parsed.certifications.length ? parsed.certifications : state.studentData.certifications;
      state.studentData.raw_text = parsed.raw_text;

      // Populate interactive form
      populateProfileForm(state.studentData);
      showToast(`Parsed CV successfully! Extracted ${parsed.skills.length} skills.`, "success");
    } else {
      showToast(data.detail || "Could not parse CV file.", "danger");
      statusBar.style.display = "none";
    }
  } catch (err) {
    showToast("Error uploading file: " + err.message, "danger");
    statusBar.style.display = "none";
  }
}

function clearUploadedCv(e) {
  e.stopPropagation();
  document.getElementById("cv-file-input").value = "";
  document.getElementById("upload-status-bar").style.display = "none";
}

// Profile Tab Switching
function switchProfileTab(tabName) {
  const tabs = ['contact', 'skills', 'experience', 'projects', 'education'];
  tabs.forEach(t => {
    const btn = document.querySelector(`.ptab-btn:nth-child(${tabs.indexOf(t) + 1})`);
    const content = document.getElementById(`ptab-${t}`);
    if (btn) btn.classList.toggle("active", t === tabName);
    if (content) content.style.display = (t === tabName) ? "block" : "none";
  });
}

// Populate Interactive Profile Form
function populateProfileForm(data) {
  document.getElementById("prof-name").value = data.full_name || "";
  document.getElementById("prof-role").value = data.target_role || "";
  document.getElementById("prof-email").value = data.email || "";
  document.getElementById("prof-phone").value = data.phone || "";
  document.getElementById("prof-location").value = data.location || "";
  document.getElementById("prof-linkedin").value = data.linkedin || "";
  document.getElementById("prof-github").value = data.github || "";
  document.getElementById("prof-summary").value = data.summary || "";

  // Render skills chips
  renderSkillsChips(data.skills || []);

  // Render experience cards
  renderExperienceItems(data.experience || []);

  // Render project cards
  renderProjectItems(data.projects || []);

  // Education & Certs
  document.getElementById("prof-education").value = (data.education || []).join("\n\n");
  document.getElementById("prof-certs").value = (data.certifications || []).join("\n");
}

function loadSampleCvData() {
  if (state.sampleData && state.sampleData.software_engineer) {
    const sample = state.sampleData.software_engineer.student_cv;
    state.studentData = { ...sample };
    populateProfileForm(sample);
    showToast("Loaded sample student profile.", "info");
  }
}

// Skills Tag Operations
function renderSkillsChips(skills) {
  state.studentData.skills = skills;
  const container = document.getElementById("student-skills-chips");
  document.getElementById("skill-count").textContent = skills.length;

  container.innerHTML = skills.map((s, idx) => `
    <span class="chip">
      ${s}
      <span class="chip-remove" onclick="removeSkill(${idx})">&times;</span>
    </span>
  `).join("");
}

function addSkillFromInput() {
  const input = document.getElementById("skill-tag-input");
  const val = input.value.trim().replace(/^,+|,+$/g, '');
  if (!val) return;

  const newSkills = val.split(',').map(s => s.trim()).filter(Boolean);
  const current = state.studentData.skills || [];
  
  newSkills.forEach(s => {
    if (!current.some(c => c.toLowerCase() === s.toLowerCase())) {
      current.push(s);
    }
  });

  renderSkillsChips(current);
  input.value = "";
}

function removeSkill(idx) {
  state.studentData.skills.splice(idx, 1);
  renderSkillsChips(state.studentData.skills);
}

// Experience Items List
function renderExperienceItems(expList) {
  const container = document.getElementById("experience-items-list");
  if (!expList || !expList.length) {
    container.innerHTML = `<p class="text-muted" style="font-size: 0.85rem; margin-bottom: 12px;">No work experience entries yet. Click below to add an internship or role.</p>`;
    return;
  }

  container.innerHTML = expList.map((item, idx) => {
    const textVal = (typeof item === 'string') ? item : `${item.header || ''}\n${(item.bullets || []).map(b => '- ' + b).join('\n')}`;
    return `
      <div class="repeatable-item">
        <div class="item-header-row">
          <span class="item-header-title">Experience #${idx + 1}</span>
          <button class="btn-icon" onclick="removeExperienceField(${idx})" title="Remove item">&times;</button>
        </div>
        <textarea class="form-control" rows="4" onchange="updateExperienceField(${idx}, this.value)">${textVal}</textarea>
      </div>
    `;
  }).join("");
}

function addExperienceField() {
  if (!state.studentData.experience) state.studentData.experience = [];
  state.studentData.experience.push("Software Engineering Intern | Tech Company (Summer 2024)\n- Developed core features using Python and React.\n- Collaborated with engineering team in daily standups and code reviews.");
  renderExperienceItems(state.studentData.experience);
}

function updateExperienceField(idx, value) {
  state.studentData.experience[idx] = value;
}

function removeExperienceField(idx) {
  state.studentData.experience.splice(idx, 1);
  renderExperienceItems(state.studentData.experience);
}

// Projects Items List
function renderProjectItems(projList) {
  const container = document.getElementById("project-items-list");
  if (!projList || !projList.length) {
    container.innerHTML = `<p class="text-muted" style="font-size: 0.85rem; margin-bottom: 12px;">No projects added yet. Click below to add your technical projects.</p>`;
    return;
  }

  container.innerHTML = projList.map((item, idx) => {
    const textVal = (typeof item === 'string') ? item : `${item.header || ''}\n${(item.bullets || []).map(b => '- ' + b).join('\n')}`;
    return `
      <div class="repeatable-item">
        <div class="item-header-row">
          <span class="item-header-title">Project #${idx + 1}</span>
          <button class="btn-icon" onclick="removeProjectField(${idx})" title="Remove item">&times;</button>
        </div>
        <textarea class="form-control" rows="4" onchange="updateProjectField(${idx}, this.value)">${textVal}</textarea>
      </div>
    `;
  }).join("");
}

function addProjectField() {
  if (!state.studentData.projects) state.studentData.projects = [];
  state.studentData.projects.push("Personal Portfolio Web App | React, Node.js, Tailwind\n- Designed responsive user interface with modern component architecture.\n- Deployed to cloud hosting with continuous deployment.");
  renderProjectItems(state.studentData.projects);
}

function updateProjectField(idx, value) {
  state.studentData.projects[idx] = value;
}

function removeProjectField(idx) {
  state.studentData.projects.splice(idx, 1);
  renderProjectItems(state.studentData.projects);
}

// ==================== ATS GENERATION & SCORECARD ====================

// Generate ATS-Tailored Resume
async function generateAtsResume() {
  // Sync fields from inputs to state
  state.studentData.full_name = document.getElementById("prof-name").value.trim();
  state.studentData.target_role = document.getElementById("prof-role").value.trim();
  state.studentData.email = document.getElementById("prof-email").value.trim();
  state.studentData.phone = document.getElementById("prof-phone").value.trim();
  state.studentData.location = document.getElementById("prof-location").value.trim();
  state.studentData.linkedin = document.getElementById("prof-linkedin").value.trim();
  state.studentData.github = document.getElementById("prof-github").value.trim();
  state.studentData.summary = document.getElementById("prof-summary").value.trim();

  const eduText = document.getElementById("prof-education").value.trim();
  state.studentData.education = eduText ? eduText.split("\n\n").filter(Boolean) : [];

  const certText = document.getElementById("prof-certs").value.trim();
  state.studentData.certifications = certText ? certText.split("\n").filter(Boolean) : [];

  if (!state.jdText || state.jdText.length < 30) {
    showToast("Please provide a Job Description in Step 1.", "warning");
    goToStep(1);
    return;
  }

  const btn = document.getElementById("btn-generate");
  const spinner = btn.querySelector(".spinner");
  const btnText = btn.querySelector(".btn-text");

  spinner.style.display = "inline-block";
  btnText.textContent = "Synthesizing ATS Resume...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/generate-ats-resume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jd_text: state.jdText,
        student_data: state.studentData
      })
    });

    const data = await res.json();
    if (data.success && data.resume) {
      state.generatedResume = data.resume;
      
      // Render Scorecard and Live Resume
      renderScorecard(data.resume.ats_score, data.resume.original_ats_score);
      renderLiveResume(data.resume);

      showToast("ATS Resume Generated Successfully!", "success");
      goToStep(3);
    } else {
      showToast(data.detail || "Failed to generate resume.", "danger");
    }
  } catch (err) {
    showToast("Error: " + err.message, "danger");
  } finally {
    spinner.style.display = "none";
    btnText.textContent = "Generate ATS Resume & Score \u2192";
    btn.disabled = false;
  }
}

// Render ATS Scorecard
function renderScorecard(atsScore, originalScore) {
  const score = atsScore.overall_score || 0;
  
  // Update gauge text
  document.getElementById("gauge-score-val").textContent = score;

  // Animate SVG gauge ring
  const circle = document.getElementById("score-ring");
  const circumference = 2 * Math.PI * 68; // ~427.25
  const offset = circumference - (score / 100) * circumference;
  circle.style.strokeDashoffset = offset;

  // Set ring color
  let strokeColor = "#4f46e5";
  if (score >= 85) strokeColor = "#10b981";
  else if (score >= 70) strokeColor = "#4f46e5";
  else if (score >= 50) strokeColor = "#f59e0b";
  else strokeColor = "#ef4444";
  circle.setAttribute("stroke", strokeColor);

  // Badge
  const badge = document.getElementById("score-badge");
  badge.textContent = atsScore.rating || "ATS Evaluated";
  badge.className = `badge badge-${atsScore.badge_color || 'primary'}`;

  // Before vs After
  const beforeVal = originalScore ? originalScore.overall_score : Math.max(35, score - 38);
  document.getElementById("score-before-val").textContent = `${beforeVal}%`;
  document.getElementById("score-after-val").textContent = `${score}%`;

  // Breakdown Bars
  const bd = atsScore.breakdown || {};
  document.getElementById("metric-kw-val").textContent = `${bd.keyword_match || 0}%`;
  document.getElementById("bar-kw").style.width = `${bd.keyword_match || 0}%`;

  document.getElementById("metric-skills-val").textContent = `${bd.skills_alignment || 0}%`;
  document.getElementById("bar-skills").style.width = `${bd.skills_alignment || 0}%`;

  document.getElementById("metric-action-val").textContent = `${bd.action_verbs || 0}%`;
  document.getElementById("bar-action").style.width = `${bd.action_verbs || 0}%`;

  document.getElementById("metric-format-val").textContent = `${bd.formatting_health || 0}%`;
  document.getElementById("bar-format").style.width = `${bd.formatting_health || 0}%`;

  // Matched Keywords
  const matchedList = atsScore.matched_keywords || [];
  document.getElementById("count-matched").textContent = matchedList.length;
  document.getElementById("chips-matched").innerHTML = matchedList.map(k => `
    <span class="kw-chip kw-chip-matched">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
      ${k}
    </span>
  `).join("") || `<span class="text-muted" style="font-size: 0.75rem;">No direct skills matched yet</span>`;

  // Missing Keywords
  const missingList = atsScore.missing_keywords || [];
  document.getElementById("count-missing").textContent = missingList.length;
  document.getElementById("chips-missing").innerHTML = missingList.map(k => `
    <span class="kw-chip kw-chip-missing">
      ${k}
      <button class="kw-add-btn" onclick="injectMissingKeyword('${k}')" title="Add to skills &amp; resume">+</button>
    </span>
  `).join("") || `<span class="text-success" style="font-size: 0.75rem;">All major JD keywords included!</span>`;

  // Recommendations
  const recList = atsScore.recommendations || [];
  document.getElementById("recommendations-list").innerHTML = recList.map(r => `
    <li class="rec-item">
      <span class="rec-bullet">&bull;</span>
      <span>${r}</span>
    </li>
  `).join("") || `<li class="rec-item text-success">Excellent alignment! Resume is ATS ready.</li>`;
}

// Render Live ATS Resume Paper
function renderLiveResume(resume) {
  const contact = resume.contact || {};
  document.getElementById("res-disp-name").textContent = contact.full_name || "Candidate Name";
  document.getElementById("res-disp-title").textContent = contact.target_title || "Target Professional Role";

  const contactParts = [
    contact.email,
    contact.phone,
    contact.location,
    contact.linkedin,
    contact.github
  ].filter(Boolean);
  document.getElementById("res-disp-contact").textContent = contactParts.join("  •  ");

  // Summary
  document.getElementById("res-disp-summary").textContent = resume.summary || "";

  // Skills
  const skillsContainer = document.getElementById("res-disp-skills");
  const categorized = resume.skills_categorized || {};
  let skillsHtml = "";
  for (const [category, items] of Object.entries(categorized)) {
    if (items && items.length) {
      skillsHtml += `
        <div class="res-skill-row">
          <strong>•  ${category}:</strong> ${items.join(", ")}
        </div>
      `;
    }
  }
  skillsContainer.innerHTML = skillsHtml;

  // Experience
  const expContainer = document.getElementById("res-disp-experience");
  const expList = resume.experience || [];
  expContainer.innerHTML = expList.map(exp => `
    <div class="res-entry">
      <div class="res-entry-header">${exp.header || ''}</div>
      <ul class="res-bullets-list">
        ${(exp.bullets || []).map(b => `<li>${b}</li>`).join("")}
      </ul>
    </div>
  `).join("");

  // Projects
  const projContainer = document.getElementById("res-disp-projects");
  const projList = resume.projects || [];
  projContainer.innerHTML = projList.map(proj => `
    <div class="res-entry">
      <div class="res-entry-header">${proj.header || ''}</div>
      <ul class="res-bullets-list">
        ${(proj.bullets || []).map(b => `<li>${b}</li>`).join("")}
      </ul>
    </div>
  `).join("");

  // Education
  const eduContainer = document.getElementById("res-disp-education");
  const eduList = resume.education || [];
  eduContainer.innerHTML = eduList.map(edu => `<div class="res-edu-item">${edu}</div>`).join("");

  // Certifications
  const certContainer = document.getElementById("res-disp-cert-container");
  const certsList = resume.certifications || [];
  if (certsList.length) {
    certContainer.style.display = "block";
    document.getElementById("res-disp-certs").innerHTML = certsList.map(c => `<div class="res-cert-item">• ${c}</div>`).join("");
  } else {
    certContainer.style.display = "none";
  }
}

// Toggle In-line Editing on the Resume Paper
function toggleInlineEdit(enabled) {
  state.isEditing = enabled;
  const paper = document.getElementById("resume-paper-target");
  paper.setAttribute("data-editable", enabled ? "true" : "false");

  const editables = paper.querySelectorAll("[contenteditable]");
  editables.forEach(el => {
    el.setAttribute("contenteditable", enabled ? "true" : "false");
  });

  if (enabled) {
    showToast("In-place editing enabled. Click any section on the resume to edit directly!", "info");
    paper.addEventListener("input", debounceRecalculateScore, false);
  } else {
    paper.removeEventListener("input", debounceRecalculateScore, false);
  }
}

let debounceTimer = null;
function debounceRecalculateScore() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    const resumeText = document.getElementById("resume-paper-target").innerText;
    try {
      const res = await fetch("/api/recalculate-score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          jd_text: state.jdText,
          skills: state.studentData.skills
        })
      });
      const data = await res.json();
      if (data.success && data.score) {
        renderScorecard(data.score, state.generatedResume ? state.generatedResume.original_ats_score : null);
      }
    } catch (err) {
      console.error("Score recalculation error:", err);
    }
  }, 600);
}

// Inject Missing Keyword into Resume and Skills
async function injectMissingKeyword(keyword) {
  // Add to state skills
  if (!state.studentData.skills.includes(keyword)) {
    state.studentData.skills.push(keyword);
    renderSkillsChips(state.studentData.skills);
  }

  // Add into the live preview skills row
  const skillsContainer = document.getElementById("res-disp-skills");
  const firstRow = skillsContainer.querySelector(".res-skill-row");
  if (firstRow) {
    firstRow.innerHTML += `, ${keyword}`;
  }

  showToast(`Added "${keyword}" to resume competencies!`, "success");
  
  // Trigger score recalculation
  debounceRecalculateScore();
}

// Download Word (.docx)
async function downloadWordDocx() {
  if (!state.generatedResume) {
    showToast("Please generate a resume first.", "warning");
    return;
  }

  try {
    showToast("Generating ATS Word document...", "info");
    const res = await fetch("/api/download-docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume: state.generatedResume })
    });

    if (!res.ok) throw new Error("Failed to build Word document");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const candName = (state.generatedResume.contact.full_name || "Candidate").replace(/\s+/g, "_");
    a.download = `ATS_Resume_${candName}.docx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
    showToast("Word document downloaded successfully!", "success");
  } catch (err) {
    showToast("Error downloading Word doc: " + err.message, "danger");
  }
}

// Print or Save as PDF
function printResume() {
  window.print();
}

// Copy Plain Text for Application Forms (Taleo, Workday text boxes)
function copyPlainTextResume() {
  const paper = document.getElementById("resume-paper-target");
  const plainText = paper.innerText;
  
  navigator.clipboard.writeText(plainText).then(() => {
    showToast("Clean ATS plain text copied to clipboard!", "success");
  }).catch(() => {
    showToast("Could not copy text automatically. Please select and copy.", "warning");
  });
}

// Toast Notifications Helper
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";

  let icon = "";
  if (type === "success") {
    toast.style.background = "#065f46";
    icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  } else if (type === "warning") {
    toast.style.background = "#92400e";
    icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
  } else if (type === "danger") {
    toast.style.background = "#991b1b";
    icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
  } else {
    toast.style.background = "#1e293b";
    icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
  }

  toast.innerHTML = `${icon}<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
