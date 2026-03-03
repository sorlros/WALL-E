import os
import sys
import socket
import psycopg
from dotenv import load_dotenv

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_port(host, port, service_name):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"✅ {service_name} Port {port} is OPEN")
            return True
        else:
            print(f"❌ {service_name} Port {port} is CLOSED (Code: {result})")
            return False
    except Exception as e:
        print(f"❌ {service_name} Port {port} Check Failed: {e}")
        return False
    finally:
        sock.close()

def check_db_connection():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
        
    try:
        # Simple connection check
        conn = psycopg.connect(db_url)
        conn.close()
        print("✅ Database Connection Successful")
        return True
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")
        return False

def check_env_vars():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    required_vars = ["DATABASE_URL", "SUPABASE_URL", "SUPABASE_KEY", "RTMP_URL"]
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"❌ Missing Env Var: {var}")
            all_present = False
        else:
            print(f"✅ Found Env Var: {var}")
    return all_present

if __name__ == "__main__":
    print("--- 🏥 Backend Health Check ---")
    
    # 1. Env Vars
    env_ok = check_env_vars()
    
    # 2. Database
    db_ok = check_db_connection()
    
    # 3. Ports (Localhost)
    api_ok = check_port("127.0.0.1", 8000, "Backend API")
    rtmp_ok = check_port("127.0.0.1", 1935, "RTMP Server")
    
    print("\n--- Summary ---")
    if env_ok and db_ok and api_ok:
        print("✅ Backend seems healthy (RTMP port optional depending on MediaMTX status)")
        sys.exit(0)
    else:
        print("⚠️ Issues detected. Please check logs above.")
        sys.exit(1)
