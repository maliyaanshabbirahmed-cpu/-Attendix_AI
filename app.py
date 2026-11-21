import streamlit as st, pandas as pd, cv2, numpy as np, io
from datetime import date, datetime, time
from attendance.db import *
from attendance.recognition import FaceEngine
from attendance.gmail_assistant import GmailAssistant

st.set_page_config(page_title="AI Attendance Pro", page_icon="🎓", layout="wide")
init_db()
st.title("🎓 AI Attendance Pro")
st.caption("Python + Streamlit classroom attendance prototype")
page = st.sidebar.radio("Navigation", ["Dashboard","Students","Face Attendance","Reports","Gmail Assistant","Settings"])

def engine():
    if "engine" not in st.session_state: st.session_state.engine = FaceEngine()
    return st.session_state.engine

if page == "Dashboard":
    students=get_students(); rows=get_attendance(date.today().isoformat())
    counts={s:sum(r["status"]==s for r in rows) for s in ["Present","Late","Absent"]}
    a,b,c,d=st.columns(4)
    a.metric("Students",len(students)); b.metric("Present",counts["Present"]); c.metric("Late",counts["Late"]); d.metric("Absent",counts["Absent"])
    st.subheader("Today's records")
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True) if rows else st.info("No attendance recorded today.")
    st.info("Start by registering students and uploading several reference face images per student.")

elif page == "Students":
    st.subheader("Register student")
    with st.form("student"):
        sid=st.text_input("Student ID"); name=st.text_input("Full name")
        ok=st.form_submit_button("Add student")
    if ok:
        try: add_student(sid.strip(),name.strip()); st.success("Student added.")
        except Exception as e: st.error(str(e))
    students=get_students()
    if students:
        st.subheader("Enroll face images")
        opts={f'{s["student_id"]} — {s["name"]}':s["student_id"] for s in students}
        chosen=st.selectbox("Student",list(opts))
        uploads=st.file_uploader("Upload 5–10 clear varied face photos",type=["jpg","jpeg","png"],accept_multiple_files=True)
        if st.button("Save reference images"):
            if not uploads: st.warning("Select images first.")
            else:
                n=0
                for f in uploads:
                    arr=np.frombuffer(f.getvalue(),np.uint8); img=cv2.imdecode(arr,cv2.IMREAD_COLOR)
                    if img is not None: save_student_image(opts[chosen],f.name,f.getvalue()); n+=1
                st.success(f"Saved {n} image(s).")
        st.dataframe(pd.DataFrame(students),use_container_width=True,hide_index=True)

elif page == "Face Attendance":
    st.warning("Prototype only: LBPH is a basic classical recognizer, not a high-assurance biometric system. Verify every suggested identity.")
    students=get_students()
    if not students: st.info("Register at least two students and upload their face images first.")
    else:
        e=engine()
        if st.button("Train / retrain face recognizer",type="primary"):
            result=e.train()
            st.success(f'Trained with {result["images"]} images and {result["identities"]} identities.') if result["ok"] else st.error(result["message"])
        settings=get_settings()
        default=time.fromisoformat(settings.get("deadline","08:00"))
        deadline=st.time_input("Attendance deadline",value=default)
        if st.button("Save deadline"): save_setting("deadline",deadline.strftime("%H:%M")); st.success("Deadline saved.")
        photo=st.camera_input("Capture student face")
        if photo:
            frame=cv2.imdecode(np.frombuffer(photo.getvalue(),np.uint8),cv2.IMREAD_COLOR)
            if st.button("Recognize and mark attendance"):
                if not e.is_trained: st.error("Train the recognizer first.")
                else:
                    result=e.predict(frame)
                    if result["student_id"] is None: st.error(result["message"])
                    else:
                        person=next((s for s in students if s["student_id"]==result["student_id"]),None)
                        if person:
                            now=datetime.now(); status="Present" if now.strftime("%H:%M")<=get_settings().get("deadline","08:00") else "Late"
                            save_attendance(person["student_id"],date.today().isoformat(),now.isoformat(timespec="seconds"),status,result["confidence"])
                            st.success(f'{person["name"]}: {status} — candidate match. Verify the face.')
                            st.caption(f'LBPH distance: {result["confidence"]:.1f}; lower is closer.')
        st.divider()
        st.write("Close attendance only after the deadline.")
        if st.button("Close attendance and mark unmarked students absent"):
            st.success(f'Marked {set_absent_for_unmarked(date.today().isoformat())} student(s) absent.')

elif page == "Reports":
    day=st.date_input("Report date",date.today()); rows=get_attendance(day.isoformat())
    if rows:
        df=pd.DataFrame(rows); st.dataframe(df,use_container_width=True,hide_index=True)
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as w: df.to_excel(w,index=False,sheet_name="Attendance")
        st.download_button("Download Excel",buf.getvalue(),f"attendance_{day}.xlsx")
    else: st.info("No attendance records for this date.")

elif page == "Gmail Assistant":
    st.subheader("Gmail assistant")
    st.write("Search/read Gmail and send email after explicit confirmation. Gmail OAuth setup is required.")
    try:
        gmail=GmailAssistant.from_secrets(st.secrets)
        st.success("Gmail connected.")
    except Exception as ex:
        gmail=None; st.info("Not connected. Follow Gmail setup in README.md.")
        st.code('[gmail]\ntoken_json = "PASTE_COMPLETE_TOKEN_JSON_AS_ONE_LINE"')
    if gmail:
        q=st.text_input("Gmail search query",placeholder="newer_than:7d or from:someone@example.com")
        if st.button("Search Gmail") and q:
            try: st.session_state.mail_results=gmail.search(q)
            except Exception as ex: st.error(str(ex))
        for m in st.session_state.get("mail_results",[]):
            with st.expander(m["subject"]+" — "+m["from"]):
                st.write(m["date"]); st.write(m["snippet"]); st.text(m["body"][:5000])
        st.divider(); st.subheader("Compose")
        to=st.text_input("To"); subject=st.text_input("Subject"); body=st.text_area("Message")
        confirm=st.checkbox("I confirm sending this email")
        if st.button("Send email"):
            if not (to and subject and body): st.error("Complete all fields.")
            elif not confirm: st.error("Confirmation is required.")
            else:
                try: gmail.send(to,subject,body); st.success("Email sent.")
                except Exception as ex: st.error(str(ex))

elif page == "Settings":
    st.subheader("System notes")
    st.write("Database: local SQLite prototype. Deadline:",get_settings().get("deadline","08:00"))
    st.warning("Streamlit Cloud local files may reset. Use managed PostgreSQL and secure object storage for production.")
    st.write("Browser camera input captures a snapshot, not continuous video. Biometric data requires appropriate authorization, consent, security, retention and deletion policies.")
