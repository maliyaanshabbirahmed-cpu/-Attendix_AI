import cv2, numpy as np
from attendance.db import get_student_images,get_students
class FaceEngine:
 def __init__(self):
  self.model=None; self.labels={}; self.is_trained=False
  self.cascade=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
 def face(self,img):
  gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
  found=self.cascade.detectMultiScale(gray,1.1,5,minSize=(70,70))
  if len(found)==0: return None
  x,y,w,h=max(found,key=lambda r:r[2]*r[3])
  return cv2.equalizeHist(cv2.resize(gray[y:y+h,x:x+w],(160,160)))
 def train(self):
  if not hasattr(cv2,"face"): return {"ok":False,"message":"Install opencv-contrib-python-headless."}
  ids={s["student_id"] for s in get_students()}; xs=[]; ys=[]; self.labels={}
  for sid,path in get_student_images():
   if sid not in ids: continue
   img=cv2.imread(str(path)); f=self.face(img) if img is not None else None
   if f is None: continue
   if sid not in self.labels.values(): self.labels[len(self.labels)]=sid
   label=next(k for k,v in self.labels.items() if v==sid); xs.append(f); ys.append(label)
  if len(set(ys))<2: return {"ok":False,"message":f"Need usable frontal face images for at least 2 students. Found {len(xs)} usable images."}
  self.model=cv2.face.LBPHFaceRecognizer_create(); self.model.train(xs,np.array(ys,dtype=np.int32)); self.is_trained=True
  return {"ok":True,"images":len(xs),"identities":len(set(ys))}
 def predict(self,img):
  face=self.face(img)
  if face is None: return {"student_id":None,"message":"No clear frontal face found."}
  label,dist=self.model.predict(face)
  if label not in self.labels or dist>65: return {"student_id":None,"message":f"Unknown/uncertain face (LBPH distance {dist:.1f})."}
  return {"student_id":self.labels[label],"confidence":float(dist)}
