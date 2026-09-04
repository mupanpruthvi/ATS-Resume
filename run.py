import sys
import os
import socket
import webbrowser
import threading
import time
import uvicorn

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_available_port(start_port: int = 8000) -> int:
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

def open_browser(url: str):
    time.sleep(1.2)
    print(f"\n[+] Opening ResumeForge ATS in browser: {url}\n")
    webbrowser.open(url)

if __name__ == "__main__":
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"
    print("=" * 65)
    print("  ResumeForge ATS - AI Resume Generator & JD Matcher")
    print(f"  Server starting on: {url}")
    print("=" * 65)

    # Launch browser in a background thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Run FastAPI via uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=port, log_level="info")
