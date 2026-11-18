import io
from unittest.mock import patch
from app import app

def test_jobs_missing_credentials(monkeypatch):
 monkeypatch.delenv('ADZUNA_APP_ID',raising=False)
 monkeypatch.delenv('ADZUNA_APP_KEY',raising=False)
 assert app.test_client().get('/api/jobs?title=developer').status_code==503

def test_jobs_invalid_search():
 assert app.test_client().get('/api/jobs?title=x').status_code==400

def test_docx_upload():
 from docx import Document
 doc=Document();doc.add_paragraph('Python developer experienced in SQL, Flask and API integrations.')
 buf=io.BytesIO();doc.save(buf);buf.seek(0)
 res=app.test_client().post('/api/match-file',data={'cv':(buf,'cv.docx'),'job':'Seeking a Python developer with Flask and SQL experience.'},content_type='multipart/form-data')
 assert res.status_code==200 and 'similarity_percent' in res.json

def test_doc_rejected():
 res=app.test_client().post('/api/match-file',data={'cv':(io.BytesIO(b'fake'),'cv.doc'),'job':'Seeking a Python developer with Flask and SQL experience.'},content_type='multipart/form-data')
 assert res.status_code==400
