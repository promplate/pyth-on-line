"""
Sanic Example Demo Script

This script demonstrates how to use the Sanic web framework example
in the Pythonline environment.

To run this demo:
1. Copy and paste this code into the playground
2. Run it to see the Sanic framework in action
"""

# First, let's import our Sanic example
from examples.sanic_example import (
    Sanic, 
    create_example_app, 
    demo_sanic_app, 
    show_sanic_features
)

# Show what Sanic features are demonstrated
print("Welcome to the Sanic Web Framework Example! 🌊")
print("=" * 50)
show_sanic_features()

print("\n" + "=" * 50)
print("🚀 Now let's run the demo...")

# Run the main demo
await demo_sanic_app()

print("\n" + "=" * 50)
print("🎯 Creating your own Sanic app:")
print("=" * 50)

# Create a new Sanic app from scratch
app = Sanic("my_custom_app")

@app.get("/")
async def home(request):
    return "Welcome to my custom Sanic app!"

@app.get("/api/status")
async def status(request):
    return {"status": "running", "app": app.name}

@app.post("/api/echo")
async def echo(request):
    return {"received": request.body, "method": request.method}

# Test the custom app
print("Testing custom app:")
response = await app.handle_request("GET", "/", "", {})
print(f"GET /: {response.body}")

response = await app.handle_request("GET", "/api/status", "", {})
print(f"GET /api/status: {response.body}")

response = await app.handle_request("POST", "/api/echo", "", {}, "Hello Sanic!")
print(f"POST /api/echo: {response.body}")

print("\n✨ Try modifying the routes above to experiment with Sanic!")
print("💡 Remember: This is a simplified version for browser environments.")
print("🔗 Learn more about real Sanic at: https://sanic.dev/")