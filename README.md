# AI Attendance Pro — Streamlit prototype

## Included
- Streamlit dashboard, student enrollment, camera snapshot attendance.
- OpenCV Haar face detection + LBPH face recognition.
- Deadline-based Present/Late classification and manual attendance closure to mark remaining students Absent.
- SQLite prototype database and Excel export.
- Optional Gmail API search/read and confirmed email sending.

## Important limitations
This is a **prototype**, not a production biometric system. OpenCV LBPH is a classical face recognizer and can confuse people, especially with few images, similar-looking faces, different lighting or camera angles. The app requires teacher verification. It is not guaranteed accurate and must not be used as the sole basis for high-stakes decisions.
Streamlit camera input captures a still photo, not continuous video. Streamlit Cloud local SQLite files may reset. Use managed PostgreSQL and private storage for production.
No synthetic student portraits are included in this ZIP. Enroll only authorized participants. Obtain appropriate school and parent/guardian permission, secure biometric data, and provide an alternative attendance method.

## Deploy
1. Upload all files to a GitHub repository.
2. On Streamlit Community Cloud choose New app, select the repository and set main file to `app.py`.
3. Deploy. Open Students, register at least two students and upload several clear, frontal reference photos for each.
4. Open Face Attendance and train the recognizer. Capture a photo, check the proposed identity and mark attendance.
5. After the deadline, click Close attendance to mark unmarked students absent.
6. Download Excel reports from Reports.

## Gmail OAuth setup (optional)
1. In Google Cloud Console create/select a project and enable Gmail API.
2. Configure OAuth consent screen and add your account as a test user if required.
3. Create OAuth Client ID → Desktop app; download as `credentials.json` into project root.
4. Locally install requirements and run `python scripts/auth_gmail.py`; authorize in browser. This creates `token.json`.
5. In Streamlit Cloud → App settings → Secrets add:
   [gmail]
   token_json = "PASTE COMPLETE token.json CONTENT AS A JSON STRING"
6. Reboot the app. Do not commit credentials.json, token.json or secrets.toml.
The Gmail page supports Gmail search queries such as `newer_than:7d`, `from:address@example.com`, and `subject:attendance`. Sending requires a confirmation checkbox. This is not an unrestricted autonomous AI chatbot; open-ended AI reasoning would require a separately configured LLM API.

## Local run
Windows:
    python -m venv .venv
    .venv\\Scripts\\activate
    pip install -r requirements.txt
    streamlit run app.py

## Attendance rules
- A student has at most one record per date.
- At/before deadline = Present; after deadline = Late.
- Closing attendance inserts Absent for students without a record.
- Close attendance only after the deadline. A late arrival after closure requires a manual correction feature (not included).
