from app import app

def test_demo_location_match():
 client=app.test_client()
 result=client.post('/api/location-check',json={'address':'Manchester House, cnr Von Weiligh & Pritchard Street'})
 assert result.status_code==200
 assert result.json['matched'] is True
 assert result.json['demo_only'] is True

def test_no_match_is_not_safe_verdict():
 client=app.test_client()
 result=client.post('/api/location-check',json={'address':'123 Completely Different Road'})
 assert result.status_code==200
 assert result.json['matched'] is False
 assert 'does not verify' in result.json['note']
