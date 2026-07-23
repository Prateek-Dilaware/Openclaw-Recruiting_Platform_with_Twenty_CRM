import httpx

HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImU1Yjk5YTU0LWNlNDYtNDMxOC05ZDBkLWY4NWM3ODVmZjMyZSJ9.eyJzdWIiOiI3YjJmYTIwYi0zY2Q1LTQzYjMtYjM3MC01OGY4NjViZDUyNjUiLCJ0eXBlIjoiQVBJX0tFWSIsIndvcmtzcGFjZUlkIjoiN2IyZmEyMGItM2NkNS00M2IzLWIzNzAtNThmODY1YmQ1MjY1IiwiaWF0IjoxNzgzNTk2NTM1LCJleHAiOjQ5MzcxOTY1MzQsImp0aSI6IjkzOTRmODdjLTJmNzQtNDkzNi04OGI3LTMwM2JiZjQ1NzI4NyJ9.zB95ZEzTPAj1Epe5cEPdQWHv9jjAc1GomGy0lxjPnm4UfltVMpBQYvxqsS3k3VRu-wvP-lPpjooccPo1Dz6ECQ",
    "Content-Type": "application/json"
}
CRM_BASE = "http://localhost:3000/rest"

def run():
    print("Fetching existing webhooks...")
    res = httpx.get(f"{CRM_BASE}/webhooks", headers=HEADERS)
    webhooks = res.json()
    print(f"Found {len(webhooks)} webhooks.")
    
    for wh in webhooks:
        print(f"Deleting webhook: {wh['id']} ({wh['targetUrl']})")
        httpx.delete(f"{CRM_BASE}/webhooks/{wh['id']}", headers=HEADERS)
        
    target_url = "http://host.docker.internal:8000/api/v1/webhooks"
    print(f"Creating new webhook targeting: {target_url}")
    create_res = httpx.post(f"{CRM_BASE}/webhooks", headers=HEADERS, json={
        "targetUrl": target_url
    })
    print("Status Code:", create_res.status_code)
    print("Response:", create_res.json())

if __name__ == "__main__":
    run()
