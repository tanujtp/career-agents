import os
import sys
import shutil
from pathlib import Path

# Try to import document parsers
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

def parse_resume(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found at: {file_path}")
    
    ext = path.suffix.lower()
    text = ""
    
    if ext == ".pdf":
        if not fitz:
            raise ImportError("PyMuPDF (fitz) is not installed. Please install pymupdf.")
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
    elif ext == ".docx":
        if not Document:
            raise ImportError("python-docx is not installed. Please install python-docx.")
        doc = Document(path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif ext in (".txt", ".md"):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError(f"Unsupported file extension: {ext}. Please provide a PDF, DOCX, or TXT file.")
        
    return text.strip()

def onboard_user(resume_path: str, model_name: str = "gpt-4o"):
    print(f"Reading resume from: {resume_path}")
    resume_text = parse_resume(resume_path)
    
    if not resume_text:
        print("Failed to extract any text from the resume.")
        sys.exit(1)
        
    print("Resume parsed successfully. Generating profile and CV markdown using LLM...")
    
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    
    # 1. Generate cv.md
    cv_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert career advisor. Convert the following raw resume text into a clean, well-structured Markdown document. Include standard sections like Summary, Experience, Projects, Education, and Skills. Do not add any conversational text or formatting outside the markdown itself."),
        ("user", "{resume}")
    ])
    
    cv_result = llm.invoke(cv_prompt.format_messages(resume=resume_text))
    cv_md_path = ROOT / "cv.md"
    cv_text = cv_result.content.strip()
    if cv_text.startswith("```markdown"):
        cv_text = cv_text[11:]
    if cv_text.startswith("```"):
        cv_text = cv_text[3:]
    if cv_text.endswith("```"):
        cv_text = cv_text[:-3]
    with open(cv_md_path, "w", encoding="utf-8") as f:
        f.write(cv_text.strip())
    print(f"✅ Created {cv_md_path.relative_to(ROOT)}")
    
    # 2. Extract profile info
    profile_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a data extractor. Extract the candidate's Full Name, Email, Location, and guess 3 Target Roles based on their experience. Output valid YAML ONLY with this exact structure:\ncandidate:\n  full_name: string\n  email: string\n  location: string\n  target_roles:\n    - string\n    - string\n    - string\ncompensation:\n  target_range: 'TBD'\nDo not wrap in markdown tags like ```yaml, just output the raw YAML."),
        ("user", "{resume}")
    ])
    
    profile_result = llm.invoke(profile_prompt.format_messages(resume=resume_text))
    yaml_text = profile_result.content.strip().replace("```yaml", "").replace("```", "").strip()
    
    # Create config dir if needed
    config_dir = ROOT / "config"
    config_dir.mkdir(exist_ok=True)
    
    profile_yml_path = config_dir / "profile.yml"
    with open(profile_yml_path, "w", encoding="utf-8") as f:
        f.write(yaml_text)
    print(f"✅ Created {profile_yml_path.relative_to(ROOT)}")
    
    # 3. Setup other basic files if they don't exist
    modes_dir = ROOT / "modes"
    modes_dir.mkdir(exist_ok=True)
    profile_md_path = modes_dir / "_profile.md"
    if not profile_md_path.exists():
        template_path = modes_dir / "_profile.template.md"
        if template_path.exists():
            shutil.copy(template_path, profile_md_path)
            print(f"✅ Created {profile_md_path.relative_to(ROOT)} from template")
            
    portals_yml_path = ROOT / "portals.yml"
    if not portals_yml_path.exists():
        template_path = ROOT / "templates" / "portals.example.yml"
        if template_path.exists():
            shutil.copy(template_path, portals_yml_path)
            print(f"✅ Created {portals_yml_path.relative_to(ROOT)} from template")
            
    # Tracker
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    tracker_path = data_dir / "applications.md"
    if not tracker_path.exists():
        with open(tracker_path, "w", encoding="utf-8") as f:
            f.write("# Applications Tracker\n\n| # | Date | Company | Role | Score | Status | PDF | Report | Notes |\n|---|------|---------|------|-------|--------|-----|--------|-------|\n")
        print(f"✅ Created {tracker_path.relative_to(ROOT)}")

    print("\n🎉 Onboarding Complete! Your profile has been generated.")
    print("You can edit config/profile.yml or cv.md if you'd like to refine anything.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python onboard.py <path_to_resume>")
        sys.exit(1)
        
    onboard_user(sys.argv[1])
