import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post('http://localhost:8000/api/v1/auth/login', json={'email':'test_flow@example.com','password':'testpassword123'})
        t = r.json()['access_token']
        h = {'Authorization': f'Bearer {t}'}
        r = await c.get('http://localhost:8000/api/v1/interviews/interviews/5f36c3ea-4f39-47b8-8ccf-2e5431403c28', headers=h)
        i = r.json()
        q = i['questions'][0]
        print('QID:', q['id'])
        r = await c.post(f'http://localhost:8000/api/v1/interviews/interviews/questions/{q["id"]}/answer', json={'transcript': 'Test answer', 'duration_seconds': 60}, headers=h)
        print('Status:', r.status_code)
        print('Body:', r.text[:500])

asyncio.run(test())