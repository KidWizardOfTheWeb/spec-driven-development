"""
Example application using Python 3.10+ features (match statement)
"""

def process_command(command: str, args: list) -> str:
    """Process a command using structural pattern matching (Python 3.10+)."""
    
    match command:
        case "start":
            return f"Starting application with args: {args}"
        
        case "stop":
            return "Stopping application"
        
        case "restart":
            return "Restarting application"
        
        case "status":
            status = "running" if args else "stopped"
            return f"Application status: {status}"
        
        case _:
            return f"Unknown command: {command}"


def process_http_status(status_code: int) -> str:
    """Process HTTP status codes using match statement."""
    
    match status_code:
        case 200:
            return "OK"
        case 201:
            return "Created"
        case 400:
            return "Bad Request"
        case 401 | 403:
            return "Unauthorized"
        case 404:
            return "Not Found"
        case 500:
            return "Internal Server Error"
        case code if 200 <= code < 300:
            return "Success"
        case code if 400 <= code < 500:
            return "Client Error"
        case code if 500 <= code < 600:
            return "Server Error"
        case _:
            return "Unknown Status"


if __name__ == "__main__":
    # Test the functions
    print(process_command("start", ["--verbose"]))
    print(process_command("status", []))
    print(process_http_status(200))
    print(process_http_status(404))
