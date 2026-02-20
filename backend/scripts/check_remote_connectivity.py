import socket
import sys
import time

REMOTE_IP = "1.238.76.151"
PORTS = {
    8000: "Backend API (FastAPI)",
    1935: "RTMP Server (MediaMTX Input)",
    8888: "HLS Server (MediaMTX Output)"
}

def check_remote_port(ip, port, service_name):
    print(f"Checking {service_name} at {ip}:{port}...", end=" ", flush=True)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3) # 3 second timeout
        result = sock.connect_ex((ip, port))
        if result == 0:
            print("✅ OPEN")
            return True
        else:
            print(f"❌ CLOSED (Code: {result})")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    print(f"--- 🌏 Remote Server Connectivity Check ({REMOTE_IP}) ---")
    print("This script checks if YOUR computer can reach the REMOTE server.")
    
    results = {}
    for port, name in PORTS.items():
        results[port] = check_remote_port(REMOTE_IP, port, name)
        
    print("\n--- Summary ---")
    if all(results.values()):
        print("✅ All remote ports are accessible!")
    else:
        print("⚠️ Some ports are blocked. Check Server Firewall (UFW/AWS Security Group) or MediaMTX status.")
        if not results[8000]:
            print("  - Backend API (8000) unreachable: App cannot login or get data.")
        if not results[8888] and not results[1935]:
            print("  - MediaMTX (1935/8888) unreachable: Video streaming will fail.")
