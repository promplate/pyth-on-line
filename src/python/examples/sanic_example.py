"""
Sanic Web Framework Example for Pyth-on-Line

This example demonstrates basic Sanic concepts that can work in a browser environment.
Note: This is a simplified version since full Sanic server functionality requires 
networking capabilities that may not be available in Pyodide.
"""

import asyncio
from typing import Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass
class Request:
    """Simplified request object similar to Sanic's request"""
    method: str
    path: str
    query: Dict[str, Any]
    headers: Dict[str, str]
    body: str = ""
    
    @property
    def args(self):
        """Query parameters as dict"""
        return self.query
    
    @property
    def json(self):
        """Parse JSON body (simplified)"""
        if self.body:
            import json
            return json.loads(self.body)
        return None


@dataclass
class Response:
    """Simplified response object"""
    body: str
    status: int = 200
    headers: Dict[str, str] = None
    content_type: str = "text/plain"
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        self.headers.setdefault("Content-Type", self.content_type)


class Sanic:
    """
    Simplified Sanic app class for demonstration purposes.
    
    This mimics basic Sanic functionality but runs in a browser environment.
    """
    
    def __init__(self, name: str = "sanic_app"):
        self.name = name
        self.routes: Dict[str, Dict[str, Callable]] = {}
        self.middleware: list = []
        
    def route(self, path: str, methods: list = None):
        """Decorator to register routes"""
        if methods is None:
            methods = ["GET"]
            
        def decorator(func):
            for method in methods:
                if path not in self.routes:
                    self.routes[path] = {}
                self.routes[path][method.upper()] = func
            return func
        return decorator
    
    def get(self, path: str):
        """Convenience decorator for GET routes"""
        return self.route(path, ["GET"])
    
    def post(self, path: str):
        """Convenience decorator for POST routes"""
        return self.route(path, ["POST"])
    
    def put(self, path: str):
        """Convenience decorator for PUT routes"""
        return self.route(path, ["PUT"])
    
    def delete(self, path: str):
        """Convenience decorator for DELETE routes"""
        return self.route(path, ["DELETE"])
    
    async def handle_request(self, method: str, path: str, query: str = "", headers: Dict[str, str] = None, body: str = ""):
        """
        Handle a request and return a response.
        This simulates how Sanic would process requests.
        """
        if headers is None:
            headers = {}
            
        # Parse query parameters
        parsed_query = parse_qs(query) if query else {}
        
        # Create request object
        request = Request(
            method=method.upper(),
            path=path,
            query=parsed_query,
            headers=headers,
            body=body
        )
        
        # Find matching route
        if path in self.routes and request.method in self.routes[path]:
            handler = self.routes[path][request.method]
            
            try:
                # Call the handler
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(request)
                else:
                    result = handler(request)
                
                # Handle different return types
                if isinstance(result, Response):
                    return result
                elif isinstance(result, str):
                    return Response(body=result, content_type="text/html")
                elif isinstance(result, dict):
                    import json
                    return Response(
                        body=json.dumps(result, indent=2),
                        content_type="application/json"
                    )
                else:
                    return Response(body=str(result))
                    
            except Exception as e:
                return Response(
                    body=f"Internal Server Error: {str(e)}",
                    status=500
                )
        else:
            return Response(
                body=f"Not Found: {request.method} {path}",
                status=404
            )
    
    def middleware(self, middleware_type: str = "request"):
        """Decorator to register middleware"""
        def decorator(func):
            self.middleware.append((middleware_type, func))
            return func
        return decorator


# Example Sanic application
def create_example_app():
    """Create a sample Sanic application with various route examples"""
    
    app = Sanic("example_app")
    
    @app.get("/")
    async def hello_world(request):
        """Basic hello world endpoint"""
        return "Hello, World! This is a Sanic app running in Pyodide!"
    
    @app.get("/hello/<name>")
    async def hello_name(request):
        """Route with path parameter (simplified)"""
        # Note: Path parameters would need more complex routing in a real implementation
        return f"Hello, {request.path.split('/')[-1]}!"
    
    @app.get("/json")
    async def json_response(request):
        """JSON response example"""
        return {
            "message": "This is a JSON response",
            "app": app.name,
            "method": request.method,
            "path": request.path,
            "timestamp": "2024-01-01T00:00:00Z"  # Simplified for demo
        }
    
    @app.get("/query")
    async def query_params(request):
        """Example showing query parameter handling"""
        name = request.args.get("name", ["Anonymous"])[0]
        age = request.args.get("age", ["Unknown"])[0]
        
        return {
            "message": f"Hello {name}!",
            "age": age,
            "all_params": dict(request.args)
        }
    
    @app.post("/echo")
    async def echo_post(request):
        """Echo back the request data"""
        return {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "body": request.body,
            "json": request.json
        }
    
    return app


# Demonstration functions
async def demo_sanic_app():
    """
    Demonstrate the Sanic app functionality.
    This shows how the simplified Sanic implementation works.
    """
    print("🚀 Creating Sanic app...")
    app = create_example_app()
    
    print(f"📱 App name: {app.name}")
    print(f"🛣️  Registered routes: {len(app.routes)}")
    
    # Simulate some requests
    test_requests = [
        ("GET", "/", "", {}),
        ("GET", "/hello/Alice", "", {}),
        ("GET", "/json", "", {}),
        ("GET", "/query", "name=Bob&age=25", {}),
        ("POST", "/echo", "", {}, '{"test": "data"}'),
        ("GET", "/notfound", "", {}),
    ]
    
    print("\n📝 Testing routes:")
    print("=" * 50)
    
    for i, request_data in enumerate(test_requests, 1):
        method, path, query, headers = request_data[:4]
        body = request_data[4] if len(request_data) > 4 else ""
        
        print(f"\n{i}. {method} {path}" + (f"?{query}" if query else ""))
        
        try:
            response = await app.handle_request(method, path, query, headers, body)
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"   Body: {response.body[:100]}{'...' if len(response.body) > 100 else ''}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n✅ Sanic demo completed!")
    return app


def show_sanic_features():
    """
    Display information about Sanic features demonstrated in this example.
    """
    features = [
        "🎯 Route decorators (@app.get, @app.post, etc.)",
        "📊 Request object with method, path, query params",
        "📤 Response object with status, headers, body",
        "🔄 Async/await support for handlers",
        "📋 JSON request/response handling",
        "🔍 Query parameter parsing",
        "🚦 HTTP status codes",
        "⚡ Simplified middleware concept",
    ]
    
    print("🌊 Sanic Framework Features Demonstrated:")
    print("=" * 45)
    for feature in features:
        print(f"  {feature}")
    
    print(f"\n💡 Note: This is a simplified implementation for browser environments.")
    print(f"   Real Sanic apps run on servers with full networking capabilities.")
    
    print(f"\n🔗 Learn more about Sanic: https://sanic.dev/")


# Export the main functions for use in the playground
__all__ = [
    "Sanic",
    "Request", 
    "Response",
    "create_example_app",
    "demo_sanic_app",
    "show_sanic_features"
]


# Auto-run demo when imported (can be commented out)
if __name__ == "__main__":
    # This would run when the module is executed directly
    asyncio.run(demo_sanic_app())