import base64,json
from email.mime.text import MIMEText
from email.utils import parseaddr
class GmailAssistant:
 @classmethod
 def from_secrets(cls,secrets):
  from google.oauth2.credentials import Credentials
  from googleapiclient.discovery import build
  from google.auth.transport.requests import Request
  token=secrets["gmail"]["token_json"]
  info=json.loads(token)
  creds=Credentials.from_authorized_user_info(info)
  if creds.expired and creds.refresh_token: creds.refresh(Request())
  if not creds.valid: raise RuntimeError("OAuth token invalid; regenerate it using scripts/auth_gmail.py.")
  obj=cls(); obj.service=build("gmail","v1",credentials=creds,cache_discovery=False); return obj
 def search(self,q):
  listing=self.service.users().messages().list(userId="me",q=q,maxResults=10).execute()
  out=[]
  for item in listing.get("messages",[]):
   m=self.service.users().messages().get(userId="me",id=item["id"],format="full").execute()
   h={x["name"].lower():x["value"] for x in m.get("payload",{}).get("headers",[])}
   out.append({"subject":h.get("subject","(No subject)"),"from":h.get("from",""),"date":h.get("date",""),"snippet":m.get("snippet",""),"body":self.body(m.get("payload",{}))})
  return out
 def body(self,p):
  data=p.get("body",{}).get("data")
  if data: return base64.urlsafe_b64decode(data+"==").decode(errors="replace")
  for part in p.get("parts",[]):
   result=self.body(part)
   if result: return result
  return ""
 def send(self,to,subject,body):
  _,addr=parseaddr(to)
  if "@" not in addr: raise ValueError("Invalid recipient email.")
  msg=MIMEText(body,"plain","utf-8"); msg["to"]=addr; msg["subject"]=subject
  raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
  self.service.users().messages().send(userId="me",body={"raw":raw}).execute()
