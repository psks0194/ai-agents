# /// script
# dependencies = ["httpx"]
# ///

import httpx

response = httpx.get("https://httpbin.org/get")
print(response.json())