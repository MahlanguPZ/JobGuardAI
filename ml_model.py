import csv
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
BASE=Path(__file__).resolve().parent
MODEL=None
def train():
    with (BASE/'data/jobs.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
    model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2))),('lr',LogisticRegression(class_weight='balanced',random_state=42,max_iter=1000))])
    model.fit([r['text'] for r in rows],[int(r['fraud']) for r in rows])
    return model
def predict(text):
    global MODEL
    if MODEL is None: MODEL=train()
    probability=float(MODEL.predict_proba([text])[0,1])
    phrases=['registration fee','pay upfront','deposit required','send money','guaranteed income','whatsapp only','processing fee']
    warnings=[p for p in phrases if p in text.lower()]
    return {'label':'Potentially fraudulent' if probability>=0.5 else 'Likely legitimate','risk_percent':round(probability*100,1),'warnings':warnings,'model':'Trained TF-IDF + Logistic Regression','disclaimer':'Educational prototype trained on illustrative examples. Not a verified fraud decision.'}
if __name__=='__main__':
    print('Model trained:',len(train().named_steps['lr'].coef_[0]),'features')
