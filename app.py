import os,sqlite3
from pathlib import Path
from datetime import datetime,timezone
from flask import Flask,request,jsonify,render_template
from ml_model import predict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=25000
DB=Path(os.environ.get('JOBGUARD_DB',str(Path(__file__).parent/'jobguard.db')))
def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
with db() as c:c.execute('CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY, created_at TEXT, title TEXT, label TEXT, risk_percent REAL)')
@app.get('/')
def home():return render_template('index.html')
@app.get('/api/health')
def health():return jsonify(status='ok',storage='SQLite',ml='TF-IDF + Logistic Regression')
@app.post('/api/analyze')
def analyze():
 d=request.get_json(silent=True) or {};title=str(d.get('title','')).strip();desc=str(d.get('description','')).strip()
 if not 1<=len(title)<=120 or not 30<=len(desc)<=8000:return jsonify(error='Title: 1-120 characters. Description: 30-8000 characters.'),400
 result=predict(title+' '+desc)
 with db() as c:c.execute('INSERT INTO scans(created_at,title,label,risk_percent) VALUES (?,?,?,?)',(datetime.now(timezone.utc).isoformat(),title,result['label'],result['risk_percent']))
 return jsonify(result)
@app.post('/api/match')
def match():
 d=request.get_json(silent=True) or {};cv=str(d.get('cv','')).strip();job=str(d.get('job','')).strip()
 if not 20<=len(cv)<=8000 or not 20<=len(job)<=8000:return jsonify(error='CV and job must each be 20-8000 characters.'),400
 v=TfidfVectorizer(stop_words='english',ngram_range=(1,2)).fit_transform([cv,job])
 return jsonify(similarity_percent=round(float(cosine_similarity(v[:1],v[1:])[0,0])*100,1),note='Similarity is not a hiring recommendation.')
@app.get('/api/history')
def history():
 with db() as c:rows=c.execute('SELECT * FROM scans ORDER BY id DESC LIMIT 20').fetchall()
 return jsonify([dict(r) for r in rows])
@app.errorhandler(413)
def large(_):return jsonify(error='Request too large'),413
if __name__=='__main__':app.run(host='127.0.0.1',port=5000,debug=False)
