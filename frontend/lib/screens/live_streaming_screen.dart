import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../services/api_service.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import '../widgets/option_c_loading.dart';

class LiveStreamingScreen extends StatefulWidget {
  final int? missionId;
  const LiveStreamingScreen({super.key, this.missionId});

  @override
  State<LiveStreamingScreen> createState() => _LiveStreamingScreenState();
}

class _LiveStreamingScreenState extends State<LiveStreamingScreen> {
  late VideoPlayerController _controller;
  Position? _currentPosition;
  GoogleMapController? _mapController;

  // WebSocket & Detection
  WebSocketChannel? _channel;
  List<dynamic> _detections = [];
  int _savedCount = 0; // Track cumulative saved detections
  bool _showOverlay = true; // Toggle for Bounding Box Overlay

  @override
  void initState() {
    super.initState();
    _initLocationService();
    _connectWebSocket();
    print('🎥 [LiveStream] Initializing Video Player...');

    // HLS Stream URL
    // Priority: 1. .env HLS_URL (for hybrid setup) -> 2. Runtime API IP -> 3. Default
    String hlsBase;
    if (dotenv.env['HLS_URL'] != null && dotenv.env['HLS_URL']!.isNotEmpty) {
      hlsBase = dotenv.env['HLS_URL']!;
    } else if (ApiService.apiIp.isNotEmpty) {
      hlsBase = 'http://${ApiService.apiIp}:8888';
    } else {
      hlsBase = 'http://1.238.76.151:8888';
    }

    print('🎥 [LiveStream] HLS URL: $hlsBase/live/drone/index.m3u8');

    _controller = VideoPlayerController.networkUrl(
      Uri.parse('$hlsBase/live/drone/index.m3u8'),
    );

    _controller
        .initialize()
        .then((_) {
          print(
            '✅ [LiveStream] Video Initialized! (Duration: ${_controller.value.duration})',
          );
          setState(() {});
          _controller.play();
        })
        .catchError((error) {
          print('❌ [LiveStream] Initialization Error: $error');
        });

    _controller.addListener(() {
      if (_controller.value.hasError) {
        print(
          '❌ [LiveStream] Player Error: ${_controller.value.errorDescription}',
        );
      }
      if (_controller.value.isBuffering) {
        print(
          '⏳ [LiveStream] Buffering... (Buffered: ${_controller.value.buffered.length} ranges)',
        );
      }
      // Print status every second if playing
      if (_controller.value.isPlaying &&
          _controller.value.position.inSeconds % 5 == 0 &&
          _controller.value.position.inMilliseconds % 1000 < 50) {
        print('▶️ [LiveStream] Playing... Pos: ${_controller.value.position}');
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _channel?.sink.close();
    super.dispose();
  }

  void _connectWebSocket() {
    try {
      // Connect to Backend WebSocket
      final wsUrl = ApiService.apiIp.isNotEmpty
          ? 'ws://${ApiService.apiIp}:${ApiService.apiPort}'
          : (dotenv.env['WS_URL'] ?? 'ws://1.238.76.151:8000');

      _channel = WebSocketChannel.connect(Uri.parse('$wsUrl/stream/ws'));

      _channel!.stream.listen(
        (message) {
          print('📩 [WebSocket] Received: $message'); // Debug Raw Message
          try {
            final data = jsonDecode(message);
            print('✅ [WebSocket] Parsed Data: $data'); // Debug Parsed Data

            if (mounted) {
              setState(() {
                // Replace detections list with new single detection (or append if list)
                // For now, we just show the latest single detection
                _detections = [data];
                if (data.containsKey('saved_count')) {
                  _savedCount = data['saved_count'];
                }
              });
            }
          } catch (e) {
            print('❌ [WebSocket] Parsing Error: $e');
          }

          // GPS Sync removed as per new requirement (Mission Start sets location)
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
    return Scaffold(
      backgroundColor: Colors.black, // Full screen video background
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Background Video Placeholder
          // Live Stream
          // Live Stream (HLS)
          _controller.value.isInitialized
              ? SizedBox.expand(
                  child: FittedBox(
                    fit: BoxFit.contain,
                    child: SizedBox(
                      width: _controller.value.size.width,
                      height: _controller.value.size.height,
                      child: Stack(
                        children: [
                          VideoPlayer(_controller),
                          // Detection Overlay
                          if (_showOverlay)
                            CustomPaint(
                              size: Size.infinite,
                              painter: BoundingBoxPainter(_detections),
                            ),
                        ],
                      ),
                    ),
                  ),
                )
              : const Center(child: OptionCLoading()),

          // Debug Overlay (Temporary)
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

          // Crosshair / Bounding Box Overlay
          Center(
            child: Stack(
              children: [
                // Crosshair lines
                // Horizontal
                Center(
                  child: Container(
                    height: 1,
                    width: MediaQuery.of(context).size.width * 0.6,
                    color: Colors.white30,
                  ),
                ),
                // Vertical
                Center(
                  child: Container(
                    width: 1,
                    height: MediaQuery.of(context).size.height * 0.6,
                    color: Colors.white30,
                  ),
                ),
              ],
            ),
          ),

          // Right Controls (Zoom/Filters)
          Positioned(
            right: 16,
            top: MediaQuery.of(context).size.height * 0.35,
            child: Column(
              children: [
                Container(
                  width: 48,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF101622).withOpacity(0.65),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Column(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.zoom_in, color: Colors.white),
                        onPressed: () {},
                      ),
                      Container(height: 1, width: 24, color: Colors.white10),
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 8),
                        child: Text(
                          '1.0x',
                          style: TextStyle(
                            color: Colors.blue,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      Container(height: 1, width: 24, color: Colors.white10),
                      IconButton(
                        icon: const Icon(Icons.zoom_out, color: Colors.white),
                        onPressed: () {},
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  width: 48,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF101622).withOpacity(0.65),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Column(
                    children: [
                      IconButton(
                        icon: const Icon(
                          Icons.filter_center_focus,
                          color: Colors.white,
                          size: 20,
                        ),
                        onPressed: () {},
                      ),
                      const SizedBox(height: 8),
                      IconButton(
                        icon: const Icon(
                          Icons.wb_sunny,
                          color: Colors.white,
                          size: 20,
                        ),
                        onPressed: () {},
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                // NEW: AI Overlay Toggle Button
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

          // Bottom Controls (Map, Stop, Thumbnail)
          Positioned(
            bottom: MediaQuery.of(context).padding.bottom + 24,
            left: 16,
            right: 16,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                // Map Thumbnail Removed
                /*
                Container(
                  width: 90,
                  height: 90,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Stack(
                      children: [
                        _currentPosition != null
                            ? GoogleMap(
                                initialCameraPosition: CameraPosition(
                                  target: LatLng(
                                    _currentPosition!.latitude,
                                    _currentPosition!.longitude,
                                  ),
                                  zoom: 15,
                                ),
                                myLocationEnabled: true,
                                myLocationButtonEnabled: false,
                                zoomControlsEnabled: false,
                                onMapCreated: (GoogleMapController controller) {
                                  _mapController = controller;
                                },
                              )
                            : const Center(
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              ),
                        // N Compass overlay
                        Positioned(
                          top: 4,
                          right: 4,
                          child: Container(
                            padding: const EdgeInsets.all(2),
                            decoration: const BoxDecoration(
                              color: Colors.black54,
                              shape: BoxShape.circle,
                            ),
                            child: const Text(
                              'N',
                              style: TextStyle(
                                color: Colors.red,
                                fontSize: 8,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                */

                // Stop Button
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.black54,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: Colors.white10),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: Colors.green,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            const Text(
                              'AI 감지 활성',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                      SizedBox(
                        width: double.infinity,
                        height: 56,
                        child: ElevatedButton.icon(
                          onPressed: () async {
                            if (widget.missionId != null) {
                              try {
                                await ApiService.completeMission(
                                  widget.missionId!,
                                );
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('점검이 안전하게 종료되었습니다.'),
                                    ),
                                  );
                                }
                              } catch (e) {
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text(
                                        '종료 중 문제가 발생했습니다. 네트워크 상태를 확인해 주세요.',
                                      ),
                                      backgroundColor: Colors.red,
                                    ),
                                  );
                                }
                              }
                            }
                            if (context.mounted) {
                              Navigator.pop(
                                context,
                              ); // Go back to New Mission Screen
                            }
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red[600],
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          icon: const Icon(Icons.stop_circle, size: 28),
                          label: const Text(
                            '미션 종료',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTelemetryCard(String label, String value, String unit) {
    return Container(
      constraints: const BoxConstraints(minWidth: 70),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF101622).withOpacity(0.65),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 10,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 2),
          RichText(
            text: TextSpan(
              text: value,
              style: const TextStyle(
                fontSize: 18,
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
              children: [
                TextSpan(
                  text: unit,
                  style: const TextStyle(fontSize: 10, color: Colors.grey),
                ),
              ],
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
      print('⚠️ Location services are disabled.');
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        print('⚠️ Location permissions are denied');
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      print(
        '⚠️ Location permissions are permanently denied, we cannot request permissions.',
      );
      return;
    }

    // Get current position stream
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
        print(
          '📍 [GPS] Lat: ${position.latitude}, Long: ${position.longitude}',
        );

        // Update Map Camera if map is created
        if (_mapController != null) {
          _mapController!.animateCamera(
            CameraUpdate.newCameraPosition(
              CameraPosition(
                target: LatLng(position.latitude, position.longitude),
                zoom: 15,
              ),
            ),
          );
        }
      }
    });
  }
}

class BoundingBoxPainter extends CustomPainter {
  final List<dynamic> detections;

  BoundingBoxPainter(this.detections);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0;

    final textStyle = TextStyle(
      color: Colors.white,
      fontSize: 14,
      backgroundColor: Colors.red,
    );

    for (var detection in detections) {
      // bbox is [centerX, centerY, width, height] (Normalized)
      // We need to convert to [left, top, width, height] for drawing
      final bbox = detection['bbox']; // List<dynamic>
      final double x = bbox[0];
      final double y = bbox[1];
      final double w = bbox[2];
      final double h = bbox[3];

      // Convert Center-XYWH to TopLeft-XYWH
      // left = x - w/2
      // top = y - h/2
      final double left = (x - w / 2) * size.width;
      final double top = (y - h / 2) * size.height;
      final double width = w * size.width;
      final double height = h * size.height;

      final rect = Rect.fromLTWH(left, top, width, height);
      canvas.drawRect(rect, paint);

      // Draw Label
      final label =
          '${detection['label']} ${(detection['confidence'] * 100).toInt()}%';
      final textSpan = TextSpan(text: label, style: textStyle);
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();
      textPainter.paint(
        canvas,
        Offset(left, top - 20), // Draw above the box
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true; // Always repaint when detections change
  }
}
