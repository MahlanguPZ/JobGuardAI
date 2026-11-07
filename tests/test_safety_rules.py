from ml_model import predict
def test_upfront_fee_is_high_concern():
 r=predict("Pay a registration fee of R350 now to secure your job.")
 assert r["safety_level"]=="High concern"
 assert "Upfront payment" in r["warnings"]
def test_banking_request_is_flagged():
 r=predict("WhatsApp your banking details and ID copy before the interview.")
 assert "Banking information requested" in r["warnings"]
def test_secrecy_is_flagged():
 r=predict("Come alone to an isolated location. Do not tell anyone.")
 assert "Secrecy or unsafe meeting request" in r["warnings"]
def test_no_claim_of_verification():
 r=predict("Developer vacancy at a company with normal interview process.")
 assert "NOT" in r["disclaimer"]
