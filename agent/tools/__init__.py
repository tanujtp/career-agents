from .file_tools import (
    read_cv,
    read_profile,
    read_article_digest,
    read_applications_tracker,
    read_scan_history,
    read_cv_template,
    read_file,
    save_report,
    write_tracker_tsv,
    write_cv_html,
    get_next_report_number,
    get_today,
)
from .web_tools import fetch_job_posting, search_web
from .bash_tools import generate_pdf, merge_tracker, run_portal_scan, verify_pipeline

ALL_TOOLS = [
    read_cv,
    read_profile,
    read_article_digest,
    read_applications_tracker,
    read_scan_history,
    read_cv_template,
    read_file,
    save_report,
    write_tracker_tsv,
    write_cv_html,
    get_next_report_number,
    get_today,
    fetch_job_posting,
    search_web,
    generate_pdf,
    merge_tracker,
    run_portal_scan,
    verify_pipeline,
]
