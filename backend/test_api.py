import urllib.request, urllib.error, json

req1 = urllib.request.Request(
    'http://127.0.0.1:8000/api/admin/login',
    data=json.dumps({"username": "admin", "password": "password123"}).encode(),
    headers={'Content-Type': 'application/json'}
)

try:
    res1 = urllib.request.urlopen(req1)
    token = json.loads(res1.read().decode())["access_token"]
    
    req2 = urllib.request.Request(
        'http://127.0.0.1:8000/api/admin/orders?status=ONGOING',
        headers={'Authorization': f'Bearer {token}'}
    )
    res2 = urllib.request.urlopen(req2)
    print("Orders:", res2.read().decode())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
except Exception as e:
    print('Error:', e)
