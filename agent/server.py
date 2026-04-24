import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import shutil
import yaml
import markdown
import re

from agent.onboard import onboard_user
# We will use subprocess to call the agent so we don't hit import errors running in FastAPI async context
import subprocess

app = FastAPI(title="career-ops local UI")
ROOT = Path(__file__).parent.parent

# ─── HTML TEMPLATES ────────────────────────────────────────────────────────

ONBOARDING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Career Agents Onboarding</title>
    <script src="https://unpkg.com/feather-icons"></script>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --primary: #3fb950;
            --primary-hover: #2ea043;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            background-color: var(--bg-color); 
            color: var(--text-main); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            overflow: hidden;
        }
        .container { 
            background-color: var(--card-bg); 
            border: 1px solid var(--border-color); 
            padding: 50px 40px; 
            border-radius: 16px; 
            width: 100%; 
            max-width: 550px; 
            text-align: center; 
            box-shadow: 0 8px 24px rgba(0,0,0,0.5); 
            position: relative;
        }
        h1 { margin-top: 0; color: var(--text-main); font-size: 28px; }
        .emoji-title { font-size: 48px; margin-bottom: 10px; color: var(--accent); }
        .emoji-title svg { width: 48px; height: 48px; stroke-width: 1.5; }
        p { color: var(--text-muted); margin-bottom: 30px; font-size: 16px; line-height: 1.5; }
        
        .upload-area {
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            padding: 40px 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 25px;
            background-color: rgba(48, 54, 61, 0.2);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .upload-area:hover {
            border-color: var(--primary);
            background-color: rgba(63, 185, 80, 0.05);
        }
        .upload-icon { margin-bottom: 10px; color: var(--text-muted); }
        .upload-icon svg { width: 32px; height: 32px; }
        input[type="file"] { display: none; }
        
        .submit-btn { 
            background-color: var(--primary); 
            color: #fff; 
            padding: 14px 24px; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: 600; 
            font-size: 16px; 
            border: none; 
            width: 100%; 
            transition: background-color 0.2s; 
            box-shadow: 0 4px 12px rgba(63, 185, 80, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .submit-btn:hover { background-color: var(--primary-hover); }
        .submit-btn:disabled { background-color: var(--border-color); color: var(--text-muted); cursor: not-allowed; box-shadow: none; }
        
        #file-name { margin-top: 15px; font-weight: 500; color: var(--accent); display: flex; align-items: center; gap: 8px; }
        
        /* Loading Animation */
        #loading-view { display: none; }
        .loader-container { margin: 40px 0; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(88, 166, 255, 0.2);
            border-top: 4px solid var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .loading-text { margin-top: 20px; font-size: 18px; color: var(--text-main); font-weight: 500; }
        .loading-subtext { color: var(--text-muted); font-size: 14px; margin-top: 8px; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

        /* Error nudge */
        .nudge {
            background-color: rgba(248, 81, 73, 0.1);
            color: #ff7b72;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 20px;
            display: none;
            border: 1px solid rgba(248, 81, 73, 0.4);
            animation: shake 0.4s ease-in-out;
        }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
    </style>
</head>
<body>

<div class="container" id="main-view">
    <div class="emoji-title"><i data-feather="target"></i></div>
    <h1>Career Agents Setup</h1>
    <p>Let's get your AI job search pipeline ready. Upload your resume and we'll automatically generate your profile and configuration.</p>
    
    <div class="nudge" id="error-nudge">Oops! Please select a resume file first.</div>
    
    <form id="upload-form" onsubmit="submitForm(event)">
        <label class="upload-area" id="drop-area">
            <div class="upload-icon"><i data-feather="file-text"></i></div>
            <div style="font-weight: 500; color: var(--text-main);">Click to browse or drag your resume here</div>
            <div style="font-size: 13px; color: var(--text-muted); margin-top: 8px;">Supports PDF, DOCX, or TXT</div>
            <input type="file" id="resume" name="file" accept=".pdf,.docx,.txt" onchange="updateFileName()">
            <div id="file-name"></div>
        </label>
        
        <button type="submit" class="submit-btn" id="submit-btn" disabled>Launch Pipeline <i data-feather="rocket"></i></button>
    </form>
</div>

<div class="container" id="loading-view">
    <div class="emoji-title" style="color: var(--primary);"><i data-feather="star"></i></div>
    <h1>Structuring your profile...</h1>
    <div class="loader-container">
        <div class="spinner"></div>
    </div>
    <div class="loading-text" id="status-main">Extracting experience and skills</div>
    <div class="loading-subtext" id="status-sub">Reading document with PyMuPDF...</div>
</div>

<script>
    feather.replace();
    
    function updateFileName() {
        const input = document.getElementById('resume');
        const fileNameDiv = document.getElementById('file-name');
        const submitBtn = document.getElementById('submit-btn');
        const nudge = document.getElementById('error-nudge');
        
        if (input.files && input.files.length > 0) {
            fileNameDiv.innerHTML = "Selected: <b>" + input.files[0].name + "</b> <i data-feather='check' style='width: 16px; height: 16px; margin-left: 4px;'></i>";
            feather.replace();
            submitBtn.disabled = false;
            nudge.style.display = 'none';
        } else {
            fileNameDiv.innerHTML = "";
            submitBtn.disabled = true;
        }
    }

    async function submitForm(event) {
        event.preventDefault();
        const input = document.getElementById('resume');
        if (!input.files || input.files.length === 0) {
            document.getElementById('error-nudge').style.display = 'block';
            return;
        }
        
        // Switch to loading view
        document.getElementById('main-view').style.display = 'none';
        document.getElementById('loading-view').style.display = 'block';
        
        // Fun text rotation for loader
        const texts = [
            ["Analyzing your career trajectory", "Calling OpenAI..."],
            ["Generating your markdown CV", "Formatting sections..."],
            ["Detecting target roles", "Building configuration..."],
            ["Finalizing setup", "Almost there..."]
        ];
        let i = 0;
        const interval = setInterval(() => {
            if (i < texts.length) {
                document.getElementById('status-main').innerText = texts[i][0];
                document.getElementById('status-sub').innerText = texts[i][1];
                i++;
            }
        }, 2000);
        
        const formData = new FormData();
        formData.append('file', input.files[0]);
        
        try {
            const response = await fetch('/upload', { method: 'POST', body: formData });
            clearInterval(interval);
            
            if (response.ok) {
                document.getElementById('status-main').innerText = "Complete! Redirecting...";
                document.getElementById('status-main').style.color = "#3fb950";
                document.getElementById('status-sub').innerText = "Taking you to the dashboard";
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);
            } else {
                const err = await response.text();
                document.getElementById('main-view').style.display = 'block';
                document.getElementById('loading-view').style.display = 'none';
                const nudge = document.getElementById('error-nudge');
                nudge.innerText = "Error analyzing resume: " + err;
                nudge.style.display = 'block';
            }
        } catch (error) {
            clearInterval(interval);
            document.getElementById('main-view').style.display = 'block';
            document.getElementById('loading-view').style.display = 'none';
            document.getElementById('error-nudge').innerText = "Connection error. Please try again.";
            document.getElementById('error-nudge').style.display = 'block';
        }
    }
</script>

</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Career Agents Dashboard</title>
    <script src="https://unpkg.com/feather-icons"></script>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --primary: #3fb950;
            --primary-hover: #2ea043;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            background-color: var(--bg-color); 
            color: var(--text-main); 
            margin: 0; 
            padding: 0;
        }
        .header {
            background-color: var(--card-bg);
            border-bottom: 1px solid var(--border-color);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { margin: 0; font-size: 24px; display: flex; align-items: center; gap: 10px; }
        .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        
        .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
        }
        .card h2 { margin-top: 0; font-size: 18px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
        
        .profile-stat { margin-bottom: 16px; }
        .profile-stat label { display: block; color: var(--text-muted); font-size: 13px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        .profile-stat div { font-size: 16px; font-weight: 500; }
        
        .tag { background-color: rgba(63, 185, 80, 0.1); color: var(--primary); padding: 4px 10px; border-radius: 20px; font-size: 13px; display: inline-block; margin: 0 6px 6px 0; border: 1px solid rgba(63, 185, 80, 0.4); }
        
        .input-group { display: flex; gap: 10px; margin-bottom: 10px; }
        .input-group input { flex: 1; padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-color); background-color: var(--bg-color); color: var(--text-main); font-size: 15px; }
        .input-group input:focus { outline: none; border-color: var(--primary); }
        .btn { background-color: var(--primary); color: #fff; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 15px; border: none; transition: background-color 0.2s; white-space: nowrap; display: flex; align-items: center; gap: 8px; }
        .btn:hover { background-color: var(--primary-hover); }
        .btn:disabled { background-color: var(--border-color); cursor: not-allowed; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid var(--border-color); }
        th { color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
        td { font-size: 14px; }
        tr:last-child td { border-bottom: none; }
        
        /* Interactive rows */
        tbody tr { cursor: pointer; transition: background-color 0.2s; }
        tbody tr:hover { background-color: rgba(63, 185, 80, 0.05); }
        
        #eval-status { display: none; margin-top: 15px; font-size: 14px; color: var(--primary); padding: 12px; background: rgba(63, 185, 80, 0.1); border-radius: 6px; border: 1px solid rgba(63, 185, 80, 0.4); align-items: center; gap: 10px; }
        .spinner-small {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(88, 166, 255, 0.2);
            border-top: 2px solid var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>

<div class="header">
    <h1><i data-feather="briefcase"></i> Career Agents Dashboard</h1>
    <div style="color: var(--text-muted);">{{ candidate_email }}</div>
</div>

<div class="container">
    <div class="grid">
        <!-- Left Column -->
        <div class="left-col">
            <div class="card" style="margin-bottom: 24px;">
                <h2><i data-feather="user"></i> Candidate Profile</h2>
                <div class="profile-stat">
                    <label>Name</label>
                    <div>{{ candidate_name }}</div>
                </div>
                <div class="profile-stat">
                    <label>Location</label>
                    <div>{{ candidate_location }}</div>
                </div>
                <div class="profile-stat" style="margin-bottom: 0;">
                    <label>Target Roles</label>
                    <div style="margin-top: 8px;">
                        {{ target_roles_html }}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2><i data-feather="search"></i> Evaluate New Job</h2>
                <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 15px;">Paste a job URL to run the evaluation and update tracker.</p>
                <form id="eval-form" onsubmit="submitEval(event)">
                    <div class="input-group">
                        <input type="url" id="job-url" placeholder="https://boards.greenhouse.io/..." required>
                        <button type="submit" class="btn" id="eval-btn"><i data-feather="play"></i> Evaluate</button>
                    </div>
                </form>
                <div id="eval-status">
                    <div class="spinner-small" id="eval-spinner"></div>
                    <span id="eval-text">Agent running auto-pipeline...</span>
                </div>
            </div>
        </div>
        
        <!-- Right Column -->
        <div class="right-col">
            <div class="card">
                <h2><i data-feather="bar-chart-2"></i> Application Tracker</h2>
                <div style="overflow-x: auto;">
                    {{ tracker_html }}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Initialize icons
    feather.replace();

    // Make table rows clickable
    document.addEventListener("DOMContentLoaded", () => {
        const rows = document.querySelectorAll("tbody tr");
        rows.forEach(row => {
            row.addEventListener("click", () => {
                // Find the Report column text
                let reportId = "";
                // Usually the Report column is the 8th column (index 7) based on tracker format
                const cells = row.querySelectorAll("td");
                if (cells.length > 7) {
                    reportId = cells[7].innerText.trim();
                    // Strip markdown link brackets if any e.g. [001](reports/001.md)
                    reportId = reportId.replace(/\\[.*\\]\\(.*\\)/, ""); 
                    // remove brackets if rendered as plain text
                    reportId = reportId.replace(/[\\[\\]]/g, ""); 
                    
                    if (reportId && reportId.endsWith(".md")) {
                        window.location.href = "/report/" + reportId;
                    }
                }
            });
        });
    });

    async function submitEval(event) {
        event.preventDefault();
        const url = document.getElementById('job-url').value;
        if (!url) return;
        
        const btn = document.getElementById('eval-btn');
        const status = document.getElementById('eval-status');
        const spinner = document.getElementById('eval-spinner');
        const text = document.getElementById('eval-text');
        
        btn.disabled = true;
        btn.innerHTML = "<div class='spinner-small' style='border-top-color: white;'></div> Running...";
        status.style.display = "flex";
        spinner.style.display = "block";
        text.innerText = "Agent running auto-pipeline... this may take a minute.";
        status.style.color = "#58a6ff";
        status.style.borderColor = "rgba(88, 166, 255, 0.4)";
        status.style.backgroundColor = "rgba(88, 166, 255, 0.1)";
        
        try {
            const formData = new FormData();
            formData.append('url', url);
            
            const response = await fetch('/evaluate', { method: 'POST', body: formData });
            
            if (response.ok) {
                spinner.style.display = "none";
                text.innerText = "Evaluation complete! Reloading tracker...";
                status.style.color = "#3fb950";
                status.style.borderColor = "rgba(63, 185, 80, 0.4)";
                status.style.backgroundColor = "rgba(63, 185, 80, 0.1)";
                setTimeout(() => window.location.reload(), 1500);
            } else {
                const err = await response.text();
                spinner.style.display = "none";
                text.innerText = "Error: " + err;
                status.style.color = "#f85149";
                status.style.borderColor = "rgba(248, 81, 73, 0.4)";
                status.style.backgroundColor = "rgba(248, 81, 73, 0.1)";
                btn.disabled = false;
                btn.innerHTML = "<i data-feather='play'></i> Evaluate";
                feather.replace();
            }
        } catch (error) {
            spinner.style.display = "none";
            text.innerText = "Connection error.";
            btn.disabled = false;
            btn.innerHTML = "<i data-feather='play'></i> Evaluate";
            feather.replace();
        }
    }
</script>

</body>
</html>
"""

REPORT_VIEW_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report: {{ report_id }}</title>
    <script src="https://unpkg.com/feather-icons"></script>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --primary: #3fb950;
            --primary-hover: #2ea043;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            background-color: var(--bg-color); 
            color: var(--text-main); 
            margin: 0; 
            padding: 0;
        }
        .header {
            background-color: var(--card-bg);
            border-bottom: 1px solid var(--border-color);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { margin: 0; font-size: 20px; display: flex; align-items: center; gap: 10px; }
        .back-link { color: var(--accent); text-decoration: none; font-size: 14px; margin-right: 20px; display: flex; align-items: center; gap: 4px; }
        .back-link:hover { text-decoration: underline; }
        
        .container { max-width: 1000px; margin: 40px auto; padding: 0 20px; }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }
        
        .actions {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .btn { 
            background-color: var(--card-bg); 
            color: var(--text-main); 
            padding: 10px 18px; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: 500; 
            font-size: 14px; 
            border: 1px solid var(--border-color); 
            transition: all 0.2s; 
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn:hover { background-color: #21262d; border-color: #8b949e; }
        .btn-primary { background-color: var(--primary); color: white; border-color: var(--primary); }
        .btn-primary:hover { background-color: var(--primary-hover); border-color: var(--primary-hover); }
        
        .markdown-body { font-size: 15px; line-height: 1.6; }
        .markdown-body h1, .markdown-body h2, .markdown-body h3 { border-bottom: 1px solid var(--border-color); padding-bottom: 8px; margin-top: 30px; }
        .markdown-body h1 { margin-top: 0; }
        .markdown-body strong { color: #fff; }
        .markdown-body pre { background: #010409; padding: 16px; border-radius: 6px; overflow-x: auto; border: 1px solid var(--border-color); }
        .markdown-body code { background: rgba(110,118,129,0.4); padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%; }
        .markdown-body pre code { background: none; padding: 0; }
        .markdown-body blockquote { margin: 0; padding: 0 1em; color: var(--text-muted); border-left: 0.25em solid var(--border-color); }
    </style>
</head>
<body>

<div class="header">
    <div style="display: flex; align-items: center;">
        <a href="/dashboard" class="back-link"><i data-feather="arrow-left" style="width: 16px; height: 16px;"></i> Back to Dashboard</a>
        <h1><i data-feather="file-text"></i> {{ report_id }}</h1>
    </div>
    <div class="actions" style="margin-bottom:0; padding-bottom:0; border:none;">
        <a href="/download/report/{{ report_id }}" class="btn"><i data-feather="download"></i> Download Report (.md)</a>
        <a href="/download/pdf/{{ pdf_id }}" class="btn btn-primary" id="pdf-btn"><i data-feather="download"></i> Download Resume (.pdf)</a>
    </div>
</div>

<div class="container">
    <div class="card">
        <div class="markdown-body">
            {{ report_html }}
        </div>
    </div>
</div>

<script>
    feather.replace();
    
    if ("{{ pdf_id }}" === "not_found") {
        const btn = document.getElementById("pdf-btn");
        btn.style.opacity = "0.5";
        btn.style.pointerEvents = "none";
        btn.innerHTML = "<i data-feather='x'></i> PDF Not Available";
        feather.replace();
    }
</script>

</body>
</html>
"""

# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    profile_path = ROOT / "config" / "profile.yml"
    # If already onboarded, maybe redirect to dashboard immediately?
    # Actually, let's keep it simple. If they are at /, they can re-onboard.
    return HTMLResponse(content=ONBOARDING_HTML)

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    temp_dir = Path("/tmp/career_ops_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / file.filename
    
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        model = os.getenv("CAREER_OPS_MODEL", "gpt-4o")
        onboard_user(str(temp_file_path), model_name=model)
        return {"status": "success"}
    except Exception as e:
        return HTMLResponse(status_code=500, content=f"Internal Error: {str(e)}")

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    profile_path = ROOT / "config" / "profile.yml"
    if not profile_path.exists():
        return RedirectResponse(url="/")
        
    # Read Profile
    with open(profile_path, "r") as f:
        profile_data = yaml.safe_load(f) or {}
    
    candidate = profile_data.get("candidate", {})
    name = candidate.get("full_name", "Unknown Candidate")
    email = candidate.get("email", "N/A")
    location = candidate.get("location", "N/A")
    roles = candidate.get("target_roles", [])
    
    roles_html = "".join([f'<span class="tag">{r}</span>' for r in roles]) if roles else "<span style='color:#888'>No roles specified</span>"
    
    # Read Tracker
    tracker_path = ROOT / "data" / "applications.md"
    tracker_html = "<p style='color:#888'>No applications tracked yet.</p>"
    if tracker_path.exists():
        with open(tracker_path, "r") as f:
            tracker_md = f.read()
            # Basic markdown table to HTML converter
            html = markdown.markdown(tracker_md, extensions=['tables'])
            # Add some clean empty state if it's just the header
            if len(tracker_md.strip().split('\n')) <= 3:
                tracker_html = "<p style='color:#888'>Tracker is empty. Evaluate a job to add it here.</p>"
            else:
                tracker_html = html

    # Hydrate template
    html_content = DASHBOARD_HTML.replace("{{ candidate_name }}", name)
    html_content = html_content.replace("{{ candidate_email }}", email)
    html_content = html_content.replace("{{ candidate_location }}", location)
    html_content = html_content.replace("{{ target_roles_html }}", roles_html)
    html_content = html_content.replace("{{ tracker_html }}", tracker_html)
    
    return HTMLResponse(content=html_content)

import sys

@app.post("/evaluate")
async def evaluate_job(url: str = Form(...)):
    try:
        # Run agent/main.py via subprocess to avoid asyncio/Langchain event loop conflicts
        print(f"Running auto-pipeline for: {url}")
        
        # Bulletproof python path detection
        venv_python = ROOT / ".venv" / "bin" / "python"
        python_exe = str(venv_python) if venv_python.exists() else sys.executable
        
        process = subprocess.Popen(
            [python_exe, "agent/main.py", url],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=180) # 3 mins max
        
        if process.returncode != 0:
            return HTMLResponse(status_code=500, content=f"Evaluation failed. stderr: {stderr}")
            
        return {"status": "success", "output": stdout}
    except subprocess.TimeoutExpired:
        return HTMLResponse(status_code=504, content="Evaluation timed out.")
    except Exception as e:
        return HTMLResponse(status_code=500, content=f"Internal Error: {str(e)}")

@app.get("/report/{report_id}", response_class=HTMLResponse)
async def view_report(report_id: str):
    report_path = ROOT / "reports" / report_id
    if not report_path.exists():
        return HTMLResponse(status_code=404, content=f"Report not found: {report_id}")
        
    with open(report_path, "r", encoding="utf-8") as f:
        md_content = f.read()
        
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # Check if PDF exists. The PDF usually has the same base name.
    pdf_id = report_id.replace(".md", ".pdf")
    pdf_path = ROOT / "output" / pdf_id
    # Alternatively the pdf might be named cv-tanuj-... but auto-pipeline generates PDF based on company slug.
    # Actually, pdf generated by run_pdf uses cv-{name}-{company}-{date}.pdf
    # Let's search output directory for a file containing the company slug from the report ID.
    actual_pdf_id = "not_found"
    # Extract slug: 004-emergent-labs-2026-04-23.md -> emergent-labs
    parts = report_id.split("-")
    if len(parts) > 2:
        slug_parts = [p for p in parts if not p.isdigit()]
        # simple check: just list output dir and see if any file contains the slug
        output_dir = ROOT / "output"
        if output_dir.exists():
            for f in output_dir.glob("*.pdf"):
                if slug_parts[0] in f.name:
                    actual_pdf_id = f.name
                    break
    
    content = REPORT_VIEW_HTML.replace("{{ report_id }}", report_id)
    content = content.replace("{{ report_html }}", html)
    content = content.replace("{{ pdf_id }}", actual_pdf_id)
    
    return HTMLResponse(content=content)

from fastapi.responses import FileResponse

@app.get("/download/report/{report_id}")
async def download_report(report_id: str):
    report_path = ROOT / "reports" / report_id
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path=report_path, filename=report_id, media_type='text/markdown')

@app.get("/download/pdf/{pdf_id}")
async def download_pdf(pdf_id: str):
    pdf_path = ROOT / "output" / pdf_id
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path=pdf_path, filename=pdf_id, media_type='application/pdf')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
