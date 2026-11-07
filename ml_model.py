"""Explainable prototype: model estimate PLUS independent safety rules.
Never interpret a low score as verification of an employer or location.
"""
import csv,re
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
BASE=Path(__file__).resolve().parent
MODEL=None

# Patterns and weights are manually defined risk signals, NOT learned facts.
RULES=[
 ("Upfront payment",r"\b(registration|application|processing|placement|training|uniform|medical|background check)\s+(fee|payment|deposit)\b|\bpay\s+(?:an?\s+)?(?:upfront|advance|deposit|fee)\b|\bsend\s+(?:r\s*\d+|money|cash)\b",5),
 ("Banking information requested",r"\b(bank(?:ing)?\s+(?:details|account|card)|card\s+(?:number|details)|pin\s+(?:number|code)|otp|one.time.password)\b",4),
 ("Identity documents requested through chat",r"\b(?:send|share|whatsapp|dm|message)\b.{0,65}\b(?:id\s+(?:number|copy|document)|passport|identity\s+document)\b",3),
 ("Guaranteed job or income",r"\b(?:guaranteed\s+(?:employment|job|income|salary)|no\s+interview\s+(?:required|needed)|instant\s+hiring)\b",3),
 ("Urgency or pressure",r"\b(?:pay\s+(?:today|now|immediately)|act\s+now|limited\s+(?:positions|slots)|apply\s+immediately|urgent\s+hiring)\b",1),
 ("Messaging-only recruitment",r"\b(?:whatsapp\s+only|telegram\s+only|contact\s+only\s+(?:via|on)\s+whatsapp|no\s+official\s+(?:email|website))\b",2),
 ("Unrealistic earnings claims",r"\b(?:earn\s+r\s*[0-9,]+\s+(?:daily|per\s+day|weekly|per\s+week)|make\s+thousands\s+daily|easy\s+money)\b",2),
 ("Secrecy or unsafe meeting request",r"\b(?:do\s+not\s+tell\s+anyone|keep\s+(?:this|it)\s+secret|come\s+alone|meet\s+(?:at|in)\s+(?:an?\s+)?(?:isolated|secret|undisclosed)\s+(?:place|location)|do\s+not\s+contact\s+the\s+company)\b",4),
 ("Personal details before verification",r"\b(?:before\s+(?:the\s+)?interview|to\s+secure\s+(?:your\s+)?position)\b.{0,70}\b(?:bank|id|passport|payment|deposit)\b",3),
]
def train():
 with (BASE/'data/jobs.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
 model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2))),('lr',LogisticRegression(class_weight='balanced',random_state=42,max_iter=1000))])
 model.fit([r['text'] for r in rows],[int(r['fraud']) for r in rows])
 return model
def predict(text):
 global MODEL
 if MODEL is None:MODEL=train()
 model_probability=float(MODEL.predict_proba([text])[0,1])
 flags=[{'reason':name,'weight':weight} for name,pattern,weight in RULES if re.search(pattern,text,re.I|re.S)]
 points=sum(f['weight'] for f in flags)
 # Explicit rule-based safety gate: model never cancels a high-severity warning.
 level='High concern' if points>=5 or model_probability>=0.8 else ('Review carefully' if points>=2 or model_probability>=0.5 else 'No obvious warning signs found')
 return {'label':level,'risk_percent':round(model_probability*100,1),
         'model_risk_percent':round(model_probability*100,1),
         'rule_points':points,'warnings':[f['reason'] for f in flags],
         'warning_details':flags,
         'safety_level':level,
         'model':'TF-IDF + Logistic Regression with independent safety-rule screening',
         'disclaimer':'Model score is NOT a verified probability of fraud. No flags does NOT mean safe. Verify employer and interview location independently.'}
