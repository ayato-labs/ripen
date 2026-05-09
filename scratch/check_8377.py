
import httpx

def check_dashboard():
    url = "http://localhost:8377/dashboard"
    print(f"Checking dashboard at {url}...")
    try:
        response = httpx.get(url)
        print(f"Status: {response.status_code}")
        # If it returns 200, it's our server.
        # If it returns 401, it's our server with Auth.
        # If it returns 404, it might be an OLD version of our server.
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_dashboard()
