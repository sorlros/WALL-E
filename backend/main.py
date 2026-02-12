from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# missions만 불러옵니다 (stream은 에러 유발로 제외)
try:
    from backend.api import missions
except (OSError, ImportError) as e:
    print(f"⚠️ Warning: Failed to load missions module (Likely Torch/DLL error): {e}")
    print("⚠️ server starting in Map-Only mode. Mission APIs will be unavailable.")
    missions = None 

app = FastAPI(title="Wall-E Backend", version="0.1.0")

# 저장소 설정
os.makedirs("backend/storage", exist_ok=True)
app.mount("/storage", StaticFiles(directory="backend/storage"), name="storage")

# missions 라우터만 등록
if missions:
    app.include_router(missions.router)

@app.get("/")
def read_root():
    return {"message": "Wall-E Backend is running"}

@app.get("/map", response_class=HTMLResponse)
async def get_map_page():
    api_key = os.getenv("GOOGLE_MAP_API_KEY") 
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Drone Crack Map</title>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}"></script>
        <style>
          #map {{ height: 600px; width: 100%; }}
          .controls {{ margin: 20px; padding: 10px; }}
          button {{ padding: 10px 20px; font-size: 16px; cursor: pointer; }}
        </style>
      </head>
      <body>
        <h3>📍 실시간 크랙 감지 지도 (Real-time Crack Detection Map)</h3>
        <div class="controls">
          <button onclick="updateMap()">좌표 새로고침 (Refresh Live Data)</button>
          <button onclick="testMockData()">모의 데이터로 테스트 (Test with Mock Data)</button>
        </div>
        <div id="map"></div>
        <script>
          let map;
          let markers = [];
          let flightPath;

          function initMap() {{
            const seoul = {{ lat: 37.5665, lng: 126.9780 }};
            map = new google.maps.Map(document.getElementById("map"), {{
              zoom: 15,
              center: seoul,
            }});

            flightPath = new google.maps.Polyline({{
              geodesic: true,
              strokeColor: "#FF0000",
              strokeOpacity: 1.0,
              strokeWeight: 2,
            }});
            flightPath.setMap(map);
          }}

          function clearMap() {{
            for (let i = 0; i < markers.length; i++) {{
              markers[i].setMap(null);
            }}
            markers = [];
            flightPath.setPath([]);
          }}

          async function updateMap() {{
            try {{
                const res = await fetch('/missions/1/detections');
                if (!res.ok) throw new Error('Network response was not ok');
                const data = await res.json();
                drawPath(data);
            }} catch (error) {{
                console.error('Error fetching data:', error);
                alert('실시간 데이터를 불러올 수 없습니다.\\n(Map-Only Mode에서는 모의 데이터만 사용할 수 있습니다.)\\n\\nFailed to fetch live data.\\n(Live API is disabled in Map-Only Mode due to missing libraries.)');
            }}
          }}

          function testMockData() {{
            const mockData = [
                {{ gps_lat: 37.5665, gps_lng: 126.9780 }},
                {{ gps_lat: 37.5670, gps_lng: 126.9790 }},
                {{ gps_lat: 37.5680, gps_lng: 126.9800 }},
                {{ gps_lat: 37.5690, gps_lng: 126.9810 }},
                {{ gps_lat: 37.5700, gps_lng: 126.9820 }}
            ];
            console.log("Using mock data:", mockData);
            drawPath(mockData);
          }}

          function drawPath(data) {{
            clearMap();
            const pathCoordinates = [];

            if (data.length > 0) {{
              data.forEach(point => {{
                if (point.gps_lat && point.gps_lng) {{
                    const pos = {{ lat: point.gps_lat, lng: point.gps_lng }};
                    pathCoordinates.push(pos);
                    
                    const marker = new google.maps.Marker({{
                        position: pos,
                        map: map,
                        title: "Detected"
                    }});
                    markers.push(marker);
                }}
              }});

              flightPath.setPath(pathCoordinates);
              
              // Center map on the last point
              if (pathCoordinates.length > 0) {{
                  map.panTo(pathCoordinates[pathCoordinates.length - 1]);
              }}
            }}
          }}

          window.onload = initMap;
        </script>
      </body>
    </html>
    """