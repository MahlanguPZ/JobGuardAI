import os
from pathlib import Path
os.environ['JOBGUARD_DB']=str(Path(__file__).parent/'test.db')
from app import app
def test_home():assert app.test_client().get('/').status_code==200
def test_health():assert app.test_client().get('/api/health').status_code==200
def test_validation():assert app.test_client().post('/api/analyze',json={'title':'A','description':'short'}).status_code==400
def test_scan():
 r=app.test_client().post('/api/analyze',json={'title':'Remote work','description':'Earn R5000 daily. Pay registration fee immediately.'})
 assert r.status_code==200 and 0<=r.json['risk_percent']<=100
def test_history():assert app.test_client().get('/api/history').status_code==200
def test_match():
 r=app.test_client().post('/api/match',json={'cv':'Python and SQL backend development experience','job':'Python SQL developer needed for backend services'})
 assert r.status_code==200 and 0<=r.json['similarity_percent']<=100
