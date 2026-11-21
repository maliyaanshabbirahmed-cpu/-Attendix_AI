import sqlite3
from pathlib import Path
from datetime import datetime
BASE=Path(__file__).resolve().parents[1]; DATA=BASE/"data"; IMG=DATA/"student_images"; IMG.mkdir(parents=True,exist_ok=True)
DB=DATA/"attendance.db"
def connect():
 c=sqlite3.connect(DB,timeout=30); c.row_factory=sqlite3.Row; return c
def init_db():
 with connect() as c:
  c.execute("CREATE TABLE IF NOT EXISTS students(student_id TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT)")
  c.execute("""CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY,student_id TEXT,attendance_date TEXT,marked_at TEXT,status TEXT,confidence REAL,UNIQUE(student_id,attendance_date))""")
  c.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)")
  c.execute("INSERT OR IGNORE INTO settings VALUES('deadline','08:00')")
def add_student(sid,name):
 if not sid or not name: raise ValueError("Student ID and name are required.")
 with connect() as c: c.execute("INSERT INTO students VALUES(?,?,?)",(sid,name,datetime.now().isoformat()))
def get_students():
 with connect() as c: return [dict(x) for x in c.execute("SELECT * FROM students ORDER BY student_id")]
def save_student_image(sid,filename,raw):
 safe="".join(x for x in filename if x.isalnum() or x in "._-")[:60] or "face.jpg"
 folder=IMG/sid; folder.mkdir(exist_ok=True)
 (folder/(datetime.now().strftime("%Y%m%d_%H%M%S_%f")+"_"+safe)).write_bytes(raw)
def get_student_images():
 return [(d.name,p) for d in IMG.iterdir() if d.is_dir() for p in d.iterdir() if p.suffix.lower() in (".jpg",".jpeg",".png")]
def save_attendance(sid,day,marked,status,confidence):
 with connect() as c:
  c.execute("""INSERT INTO attendance(student_id,attendance_date,marked_at,status,confidence) VALUES(?,?,?,?,?)
  ON CONFLICT(student_id,attendance_date) DO UPDATE SET marked_at=excluded.marked_at,status=excluded.status,confidence=excluded.confidence""",(sid,day,marked,status,confidence))
def get_attendance(day):
 with connect() as c: return [dict(x) for x in c.execute("SELECT a.student_id,s.name,a.marked_at,a.status,a.confidence FROM attendance a JOIN students s USING(student_id) WHERE attendance_date=? ORDER BY s.name",(day,))]
def get_settings():
 with connect() as c: return {x["key"]:x["value"] for x in c.execute("SELECT * FROM settings")}
def save_setting(k,v):
 with connect() as c: c.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,v))
def set_absent_for_unmarked(day):
 n=0
 with connect() as c:
  for s in get_students():
   n+=c.execute("INSERT OR IGNORE INTO attendance(student_id,attendance_date,marked_at,status) VALUES(?,?,NULL,'Absent')",(s["student_id"],day)).rowcount
 return n
