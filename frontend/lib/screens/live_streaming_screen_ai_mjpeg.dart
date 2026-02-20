import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../services/api_service.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';
import 'dart:convert';

class LiveStreamingScreenAiOnly extends StatefulWidget {
  final int? missionId;
  const LiveStreamingScreenAiOnly({super.key, this.missionId});

  @override
  State<LiveStreamingScreenAiOnly> createState() =>
      _LiveStreamingScreenAiOnlyState();
}

class _LiveStreamingScreenAiOnlyState extends State<LiveStreamingScreenAiOnly> {
  Position? _currentPosition;
  GoogleMapController? _mapController;

  // WebSocket
  WebSocketChannel? _channel;
  List<dynamic> _detections = [];
  int _savedCount = 0;
  bool _showOverlay = true;

  @override
  void initState() {
    super.initState();
    _initLocationService();
    _connectWebSocket();
    print('🎥 [LiveStream MJPEG] Initializing AI-only stream viewer...');
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  void _connectWebSocket() {
    try {
      final wsUrl = ApiService.apiIp.isNotEmpty
          ? 'ws://${ApiService.apiIp}:${ApiService.apiPort}'
          : (dotenv.env['WS_URL'] ?? 'ws://1.238.76.151:8000');

      _channel = WebSocketChannel.connect(Uri.parse('$wsUrl/stream/ws'));

      _channel!.stream.listen(
        (message) {
          try {
            final data = jsonDecode(message);
            if (mounted) {
              setState(() {
                _detections = [data];
                if (data.containsKey('saved_count')) {
                  _savedCount = data['saved_count'];
                }
              });
            }
          } catch (e) {
            print('❌ [WebSocket] Parsing Error: $e');
          }
        },
        onError: (error) {
          print('❌ [WebSocket] Error: $error');
        },
      );
    } catch (e) {
      print('❌ [WebSocket] Connection Failed: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    // Backend MJPEG Stream URL
    final String mjpegStreamUrl = '${ApiService.baseUrl}/stream/live';

    return Scaffold(
      backgroundColor: Colors.black, // Full screen video background
      body: Stack(
        fit: StackFit.expand,
        children: [
          // MJPEG Live Stream (Directly from Backend)
          // 💡 This stream already has the YOLO bounding boxes "burned in" perfectly in sync!
          SizedBox.expand(
            child: FittedBox(
              fit: BoxFit.contain,
              child: _showOverlay
                  ? Mjpeg(
                      isLive: true,
                      stream: mjpegStreamUrl,
                      error: (context, error, stack) => const Center(
                        child: Text(
                          'AI 비디오 스트림 연결 실패',
                          style: TextStyle(color: Colors.red),
                        ),
                      ),
                    )
                  : const Center(
                      child: Text(
                        'AI 스트림 화면 닫힘',
                        style: TextStyle(color: Colors.white),
                      ),
                    ),
            ),
          ),

          // Custom Bounding Box Painter is REMOVED!
          // Because the backend cv2 already draws the boxes exactly on the frames.

          // Debug Overlay
          Positioned(
            top: 100,
            left: 20,
            child: Container(
              padding: const EdgeInsets.all(8),
              color: Colors.black54,
              child: Text(
                'Saved: $_savedCount\nLast: ${_detections.isNotEmpty ? "${_detections[0]['label']} (${(_detections[0]['confidence'] * 100).toInt()}%)" : "None"}',
                style: const TextStyle(color: Colors.yellow, fontSize: 16),
              ),
            ),
          ),

          // Right Controls (Zoom/Filters/Toggle)
          Positioned(
            right: 16,
            top: MediaQuery.of(context).size.height * 0.35,
            child: Column(
              children: [
                // ... (Zoom buttons remain unchanged)
                Container(
                  width: 48,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF101622).withOpacity(0.65),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: _showOverlay ? Colors.green : Colors.white10,
                    ),
                  ),
                  child: Column(
                    children: [
                      IconButton(
                        icon: Icon(
                          _showOverlay ? Icons.layers : Icons.layers_clear,
                          color: _showOverlay ? Colors.green : Colors.grey,
                          size: 20,
                        ),
                        onPressed: () {
                          setState(() {
                            _showOverlay = !_showOverlay;
                          });
                        },
                      ),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Text(
                          _showOverlay ? 'AI ON' : 'AI OFF',
                          style: TextStyle(
                            color: _showOverlay ? Colors.green : Colors.grey,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Bottom Controls (Stop Button)
          Positioned(
            bottom: MediaQuery.of(context).padding.bottom + 24,
            left: 0,
            right: 0,
            child: Center(
              child: SizedBox(
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: () async {
                    if (widget.missionId != null) {
                      try {
                        await ApiService.completeMission(widget.missionId!);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('미션이 종료되었습니다.')),
                          );
                        }
                      } catch (e) {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('미션 종료 오류: $e')),
                          );
                        }
                      }
                    }
                    if (context.mounted) {
                      Navigator.pop(context);
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red[600],
                    padding: const EdgeInsets.symmetric(
                      horizontal: 26,
                    ), // 구모양(반원)에서 양옆 여백 추가
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(
                        28,
                      ), // 56의 절반인 28을 주어 완벽한 둥근 캡슐 형태(구모양 베이스)
                    ),
                  ),
                  icon: const Icon(Icons.stop_circle, size: 28),
                  label: const Text(
                    'AI 화면 스트림 종료',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
          ),

          // Manual Capture Button (Right Side)
          Positioned(
            bottom: MediaQuery.of(context).padding.bottom + 24,
            right: 24,
            child: FloatingActionButton.extended(
              onPressed: () async {
                HapticFeedback.heavyImpact(); // 햅틱 피드백 '찰칵'
                if (widget.missionId != null) {
                  try {
                    await ApiService.captureManualSnapshot(widget.missionId!);
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('📸 수동 캡처 이미지가 저장되었습니다.'),
                          backgroundColor: Colors.green,
                          duration: Duration(seconds: 2),
                        ),
                      );
                    }
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('캡처 실패: $e'),
                          backgroundColor: Colors.red,
                        ),
                      );
                    }
                  }
                }
              },
              backgroundColor: Colors.white,
              icon: const Icon(Icons.camera_alt, color: Colors.black, size: 28),
              label: const Text(
                '캡처',
                style: TextStyle(
                  color: Colors.black,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _initLocationService() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return;
    }

    Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 5,
      ),
    ).listen((Position position) {
      if (mounted) {
        setState(() {
          _currentPosition = position;
        });
      }
    });
  }
}
