import os,sqlite3,io,json,re,unicodedata,hmac,secrets
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
from flask import Flask,request,jsonify,render_template,redirect,url_for,session,flash
from ml_model import predict
import retraining
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
app=Flask(__name__)

app.secret_key = os.environ.get("JOBGUARD_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("JOBGUARD_HTTPS", "0") == "1"

app.config['MAX_CONTENT_LENGTH']=6*1024*1024
DB=Path(os.environ.get('JOBGUARD_DB',str(Path(__file__).parent/'jobguard.db')))
@contextmanager
def db():
 c=sqlite3.connect(DB)
 c.row_factory=sqlite3.Row
 try:
  yield c
  c.commit()
 except BaseException:
  c.rollback()
  raise
 finally:
  c.close()
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY, created_at TEXT, title TEXT, label TEXT, risk_percent REAL)')
 retraining.setup(c)
# Presentation-only address examples. These are NOT verified incident reports.
DEMO_LOCATIONS = [
 ('ILPA House, CNR Commissioner & Von Weiligh Str', 'Johannesburg', 'Gauteng'),
 ('Manchester House, CNR Von Weilligh & Pritchard Str', 'Johannesburg', 'Gauteng'),
 ('The great experience, Curthberths of Chambers Building', 'Unspecified', 'Unspecified'),
]
def normalize_address(value):
 value=unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower()
 value=re.sub(r'\b(cnr|corner)\b',' ',value)
 value=re.sub(r'\b(str|street)\b',' ',value)
 value=value.replace('weilligh','weiligh')
 value=re.sub(r'[^a-z0-9]+',' ',value)
 return ' '.join(value.split())
with db() as c:
 c.execute("""CREATE TABLE IF NOT EXISTS location_cautions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 address TEXT NOT NULL UNIQUE,
 normalized_address TEXT NOT NULL,
 city TEXT,
 province TEXT,
 verification_status TEXT NOT NULL DEFAULT 'demo_unverified',
 source_reference TEXT NOT NULL DEFAULT 'User-supplied presentation example',
 created_at TEXT NOT NULL
 )""")
 for address,city,province in DEMO_LOCATIONS:
  c.execute("""INSERT OR IGNORE INTO location_cautions
   (address,normalized_address,city,province,verification_status,source_reference,created_at)
   VALUES (?,?,?,?,?,?,?)""",
   (address,normalize_address(address),city,province,'demo_unverified',
    'User-supplied presentation example',datetime.now(timezone.utc).isoformat()))

@app.post('/api/location-check')
def location_check():
 payload=request.get_json(silent=True) or {}
 address=payload.get('address','')
 if not isinstance(address,str) or not 5<=len(address.strip())<=300:
  return jsonify(error='Enter an interview address (5–300 characters).'),400
 normalized=normalize_address(address)
 with db() as c:
  rows=c.execute('SELECT address,normalized_address,verification_status FROM location_cautions').fetchall()
 matches=[dict(r) for r in rows if normalize_address(r['address'])==normalized]
 return jsonify(
  matched=bool(matches),
  status='DEMO RECORD MATCH — NOT VERIFIED' if matches else 'NO DEMO RECORD FOUND',
  note=('The entered address matches a user-supplied demonstration record. '
        'This is not evidence that the address, building or its occupants are unsafe.'
        if matches else
        'No match in the small demonstration database. This does not verify that a location is safe.'),
  advice='Confirm the employer independently, verify the venue and share interview details with someone you trust.',
  demo_only=True)

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
@app.get('/api/jobs')
def jobs():
 title=request.args.get('title','').strip()
 location=request.args.get('location','').strip()
 if not 2<=len(title)<=100 or len(location)>100:
  return jsonify(error='Enter a job title (2-100 characters) and optional location.'),400
 app_id=os.environ.get('ADZUNA_APP_ID','').strip()
 app_key=os.environ.get('ADZUNA_APP_KEY','').strip()
 if not app_id or not app_key:
  return jsonify(error='Adzuna credentials missing. Set ADZUNA_APP_ID and ADZUNA_APP_KEY in Render environment.'),503
 params={'app_id':app_id,'app_key':app_key,'what':title,'results_per_page':10,'content-type':'application/json'}
 if location:params['where']=location
 url='https://api.adzuna.com/v1/api/jobs/za/search/1?'+urlencode(params)
 try:
  req=Request(url,headers={'User-Agent':'JobGuardAI/1.0','Accept':'application/json'})
  with urlopen(req,timeout=15) as resp: payload=json.load(resp)
 except HTTPError as e:
  return jsonify(error=f'Adzuna rejected the request (HTTP {e.code}). Check credentials and API access.'),502
 except (URLError,TimeoutError,ValueError) as e:
  return jsonify(error='Could not retrieve Adzuna jobs. Please try again.'),502
 results=[]
 for item in payload.get('results',[]):
  results.append({'id':str(item.get('id','')),'title':item.get('title',''),
   'company':(item.get('company') or {}).get('display_name','Not specified'),
   'location':(item.get('location') or {}).get('display_name','South Africa'),
   'description':item.get('description',''),
   'url':item.get('redirect_url','')})
 return jsonify(jobs=results,count=len(results),source='Adzuna South Africa')

@app.post('/api/match-file')
def match_file():
 from pypdf import PdfReader
 from docx import Document
 uploaded=request.files.get('cv')
 job=request.form.get('job','').strip()
 if not uploaded or not uploaded.filename:return jsonify(error='Please select a PDF or DOCX CV.'),400
 if not 20<=len(job)<=8000:return jsonify(error='Job requirements must contain 20-8000 characters.'),400
 ext=Path(uploaded.filename).suffix.lower()
 if ext not in ('.pdf','.docx'):
  return jsonify(error='Supported uploads: PDF (.pdf) and Word (.docx). Convert older .doc files to .docx first.'),400
 data=uploaded.read()
 if not data or len(data)>5*1024*1024:return jsonify(error='CV must be between 1 byte and 5 MB.'),400
 try:
  if ext=='.pdf':
   reader=PdfReader(io.BytesIO(data))
   if len(reader.pages)>30:return jsonify(error='CV exceeds 30 pages.'),400
   cv='\\n'.join(page.extract_text() or '' for page in reader.pages)
  else:
   document=Document(io.BytesIO(data))
   cv='\\n'.join(p.text for p in document.paragraphs)
   for table in document.tables:
    cv+='\\n'+'\\n'.join(' '.join(cell.text for cell in row.cells) for row in table.rows)
 except Exception:
  return jsonify(error='Unable to read CV. Ensure the file is a valid, unencrypted PDF or DOCX.'),400
 cv=cv.strip()
 if len(cv)<20:return jsonify(error='Not enough extractable text. Scanned-image PDFs need OCR; please use a text-based PDF or DOCX.'),400
 cv=cv[:15000]
 v=TfidfVectorizer(stop_words='english',ngram_range=(1,2)).fit_transform([cv,job])
 score=round(float(cosine_similarity(v[:1],v[1:])[0,0])*100,1)
 return jsonify(similarity_percent=score,extracted_characters=len(cv),
  note='Text similarity only; not a hiring decision. Uploaded CV is processed in memory and not saved.')

@app.post('/api/feedback')
def feedback():
 d=request.get_json(silent=True) or {}
 title=d.get('title','');desc=d.get('description','');label=d.get('reported_label')
 if not isinstance(title,str) or not 1<=len(title.strip())<=120:
  return jsonify(error='Title must be 1-120 characters.'),400
 if not isinstance(desc,str) or not 30<=len(desc.strip())<=8000:
  return jsonify(error='Description must be 30-8000 characters.'),400
 if type(label) is not int or label not in (0,1):
  return jsonify(error='reported_label must be 0 (legitimate) or 1 (suspicious).'),400
 if d.get('consent') is not True:
  return jsonify(error='Consent is required to store this advert for review.'),400
 with db() as c:
  cur=c.execute("""INSERT INTO training_feedback
   (created_at,title,description,reported_label,status)
   VALUES (?,?,?,?,'pending')""",
   (retraining.now(),title.strip(),desc.strip(),label))
  feedback_id=cur.lastrowid
 return jsonify(id=feedback_id,status='pending',message='Feedback received for review; it will not train the model automatically.'),201

@app.get('/api/admin/feedback')
def admin_feedback():
 if not retraining.authorized(request):return jsonify(error='Administrator token required.'),401
 with db() as c:
  rows=c.execute("""SELECT id,created_at,title,description,reported_label,status
   FROM training_feedback WHERE status='pending' ORDER BY id LIMIT 100""").fetchall()
  count=c.execute("SELECT COUNT(*) FROM training_feedback WHERE status='approved'").fetchone()[0]
 return jsonify(pending=[dict(r) for r in rows],approved_since_last_update=count)

@app.post('/api/admin/feedback/<int:feedback_id>/review')
def admin_review(feedback_id):
 if not retraining.authorized(request):return jsonify(error='Administrator token required.'),401
 d=request.get_json(silent=True) or {}
 decision=d.get('decision')
 if decision not in ('approve','reject'):
  return jsonify(error='decision must be approve or reject.'),400
 with db() as c:
  c.execute('BEGIN IMMEDIATE')
  row=c.execute('SELECT id FROM training_feedback WHERE id=? AND status=\'pending\'',(feedback_id,)).fetchone()
  if not row:return jsonify(error='Pending feedback not found.'),404
  c.execute("UPDATE training_feedback SET status=?,reviewed_at=? WHERE id=?",
            ('approved' if decision=='approve' else 'rejected',retraining.now(),feedback_id))
  update=retraining.attempt_retrain(c) if decision=='approve' else {"triggered":False}
 return jsonify(review_status=decision,model_update=update)

@app.get('/api/admin/model-status')
def admin_model_status():
 if not retraining.authorized(request):return jsonify(error='Administrator token required.'),401
 with db() as c:
  count=c.execute("SELECT COUNT(*) FROM training_feedback WHERE status='approved'").fetchone()[0]
  updates=c.execute("SELECT * FROM model_updates ORDER BY id DESC LIMIT 5").fetchall()
 return jsonify(approved_since_last_update=count,retraining_threshold=retraining.THRESHOLD,
                recent_updates=[dict(r) for r in updates])

@app.get('/api/history')
def history():
 with db() as c:rows=c.execute('SELECT * FROM scans ORDER BY id DESC LIMIT 20').fetchall()
 return jsonify([dict(r) for r in rows])
@app.errorhandler(413)
def large(_):return jsonify(error='Request too large'),413



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None

    if request.method == 'POST':
        supplied = request.form.get('token', '')
        expected = os.environ.get('JOBGUARD_ADMIN_TOKEN', '')

        if expected and hmac.compare_digest(supplied, expected):
            session.clear()
            session['admin'] = True
            session['csrf_token'] = secrets.token_urlsafe(32)
            return redirect(url_for('admin_dashboard'))

        error = 'Invalid administrator token.'

    return render_template('admin_login.html', error=error)


@app.get('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    with db() as c:
        pending = c.execute(
            "SELECT id,created_at,title,description,reported_label "
            "FROM training_feedback WHERE status='pending' ORDER BY id LIMIT 100"
        ).fetchall()

        count = c.execute(
            "SELECT COUNT(*) FROM training_feedback WHERE status='approved'"
        ).fetchone()[0]

        updates = c.execute(
            "SELECT * FROM model_updates ORDER BY id DESC LIMIT 5"
        ).fetchall()

    return render_template(
        'admin_dashboard.html',
        pending=pending,
        count=count,
        threshold=retraining.THRESHOLD,
        updates=updates,
        csrf_token=session['csrf_token'],
    )


@app.post('/admin/review/<int:feedback_id>')
def admin_review_page(feedback_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    supplied = request.form.get('csrf_token', '')

    if not hmac.compare_digest(
        supplied,
        session.get('csrf_token', ''),
    ):
        return 'Invalid request.', 403

    decision = request.form.get('decision')

    if decision not in ('approve', 'reject'):
        return 'Invalid decision.', 400

    with db() as c:
        c.execute('BEGIN IMMEDIATE')

        row = c.execute(
            "SELECT id FROM training_feedback WHERE id=? AND status='pending'",
            (feedback_id,),
        ).fetchone()

        if not row:
            return 'Feedback not found.', 404

        c.execute(
            "UPDATE training_feedback SET status=?,reviewed_at=? WHERE id=?",
            (
                'approved' if decision == 'approve' else 'rejected',
                retraining.now(),
                feedback_id,
            ),
        )

        if decision == 'approve':
            retraining.attempt_retrain(c)

    return redirect(url_for('admin_dashboard'))


@app.post('/admin/logout')
def admin_logout():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if not hmac.compare_digest(
        request.form.get('csrf_token', ''),
        session.get('csrf_token', ''),
    ):
        return 'Invalid request.', 403

    session.clear()
    return redirect(url_for('home'))

if __name__=='__main__':app.run(host='127.0.0.1',port=5000,debug=False)

