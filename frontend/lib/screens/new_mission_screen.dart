import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
// import 'live_streaming_screen.dart';
import 'live_streaming_screen_ai_mjpeg.dart';
import '../services/api_service.dart';

class NewMissionScreen extends StatefulWidget {
  const NewMissionScreen({super.key});

  @override
  State<NewMissionScreen> createState() => _NewMissionScreenState();
}

class _NewMissionScreenState extends State<NewMissionScreen> {
  final TextEditingController _missionNameController = TextEditingController();
  final TextEditingController _memoController = TextEditingController();
  bool _isLoading = false;
  double? _lat;
  double? _lng;
  // TODO: Secure this key (move to .env or backend proxy in production)
  final String _googleMapsApiKey = "AIzaSyDcc3bQi6-UTKk2YKnq66k62chIqdiCn0I";

  @override
  void initState() {
    super.initState();
    _fetchLocation();
  }

  Future<void> _fetchLocation() async {
    try {
      Position position = await _determinePosition();
      if (mounted) {
        setState(() {
          _lat = position.latitude;
          _lng = position.longitude;
        });
        print('📍 Current Location: $_lat, $_lng');
      }
    } catch (e) {
      print("Error getting location: $e");
    }
  }

  @override
  void dispose() {
    _missionNameController.dispose();
    _memoController.dispose();
    super.dispose();
  }

  Future<void> _startMission() async {
    if (_missionNameController.text.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('미션 이름을 입력해주세요.')));
      return;
    }

    setState(() {
      _isLoading = true;
    });

    // Get current location
    double? lat;
    double? lng;

    try {
      Position position = await _determinePosition();
      lat = position.latitude;
      lng = position.longitude;
      print('📍 Mission GPS 위치 정보: $lat, $lng');

      // Use cached location if available and determinePosition failed or wasn't called again
      if (lat == null && _lat != null) {
        lat = _lat;
        lng = _lng;
      }
    } catch (e) {
      print("Could not get location: $e");
      // Proceed without location if fails (or show error)
    }

    if (!mounted) return;

    try {
      final mission = await ApiService.createMission(
        _missionNameController.text,
        _memoController.text,
        lat, // Pass lat
        lng, // Pass lng
      );

      if (!mounted) return;

      Navigator.of(context, rootNavigator: true).push(
        MaterialPageRoute(
          builder: (context) =>
              LiveStreamingScreenAiOnly(missionId: mission.id),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('미션 생성 실패: $e')));
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Using a dark theme style similar to the HTML prototype
    return Scaffold(
      backgroundColor: const Color(0xFF101622), // background-dark
      appBar: AppBar(
        backgroundColor: const Color(0xFF101622),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.grey),
          onPressed: () {}, // Close or Cancel action
        ),
        title: const Text(
          '새 미션 생성',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Drone Status Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(
                  0xFF135BEC,
                ).withOpacity(0.05), // primary color with opacity
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: const Color(0xFF135BEC).withOpacity(0.2),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: const Color(0xFF135BEC).withOpacity(0.1),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.flight,
                          color: Color(0xFF135BEC),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: const [
                          Text(
                            '드론 상태',
                            style: TextStyle(
                              color: Color(0xFF135BEC),
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            'Phantom4-Pro 연결됨',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: const [
                      Text(
                        '배터리',
                        style: TextStyle(color: Colors.grey, fontSize: 10),
                      ),
                      Text(
                        '94%',
                        style: TextStyle(
                          color: Colors.green,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Identification Section
            _buildSectionHeader('식별 정보'),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF1A2332), // surface-dark
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white10),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildLabel('미션 이름'),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _missionNameController,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: '예: 에듀타운로 84 - intel gonuai 건물 외벽',
                      hintStyle: const TextStyle(color: Colors.grey),
                      filled: true,
                      fillColor: const Color(0xFF101622),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                      suffixIcon: const Icon(
                        Icons.edit,
                        color: Colors.grey,
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  _buildLabel('설명 / 메모'),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _memoController,
                    style: const TextStyle(color: Colors.white),
                    maxLines: 3,
                    decoration: InputDecoration(
                      hintText: '특이사항 및 메모 내용',
                      hintStyle: const TextStyle(color: Colors.grey),
                      filled: true,
                      fillColor: const Color(0xFF101622),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Location Section
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildSectionHeader('위치 정보'),
                TextButton.icon(
                  onPressed: () {},
                  icon: const Icon(
                    Icons.my_location,
                    size: 16,
                    color: Color(0xFF135BEC),
                  ),
                  label: const Text(
                    '현재 위치 사용',
                    style: TextStyle(color: Color(0xFF135BEC), fontSize: 12),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              height: 200,
              decoration: BoxDecoration(
                color: Colors.grey[800],
                borderRadius: BorderRadius.circular(12),
                image: DecorationImage(
                  image: NetworkImage(
                    (_lat != null && _lng != null)
                        ? 'https://maps.googleapis.com/maps/api/staticmap?center=$_lat,$_lng&zoom=15&size=600x300&maptype=roadmap&markers=color:red%7C$_lat,$_lng&key=$_googleMapsApiKey'
                        : 'https://via.placeholder.com/600x300?text=Location+Loading...',
                  ),
                  fit: BoxFit.cover,
                  // Removed ColorFilter to match the requested bright map style
                  // colorFilter: ColorFilter.mode(
                  //   Colors.black45,
                  //   BlendMode.darken,
                  // ),
                ),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  const Icon(
                    Icons.location_on,
                    color: Color(0xFF135BEC),
                    size: 48,
                  ),
                  Positioned(
                    bottom: 0,
                    left: 0,
                    right: 0,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                      decoration: const BoxDecoration(
                        color: Colors.black54,
                        borderRadius: BorderRadius.vertical(
                          bottom: Radius.circular(12),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                '좌표',
                                style: TextStyle(
                                  color: Colors.grey,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                (_lat != null && _lng != null)
                                    ? '${_lat!.abs().toStringAsFixed(4)}° ${_lat! >= 0 ? 'N' : 'S'}, ${_lng!.abs().toStringAsFixed(4)}° ${_lng! >= 0 ? 'E' : 'W'}'
                                    : '위치 정보를 가져오는 중...',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ],
                          ),
                          Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Icon(
                              Icons.layers,
                              color: Colors.white,
                              size: 16,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(24),
        decoration: const BoxDecoration(
          color: Color(0xFF101622),
          border: Border(top: BorderSide(color: Colors.white10)),
        ),
        child: ElevatedButton(
          onPressed: _startMission,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF135BEC),
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            elevation: 8,
            shadowColor: const Color(0xFF135BEC).withOpacity(0.5),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: _isLoading
                ? const [
                    SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    ),
                  ]
                : const [
                    Text(
                      '미션 시작',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(width: 8),
                    Icon(Icons.rocket_launch, size: 20, color: Colors.white),
                  ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Row(
      children: [
        Container(
          width: 4,
          height: 24,
          decoration: BoxDecoration(
            color: const Color(0xFF135BEC),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            color: Colors.grey,
            fontWeight: FontWeight.bold,
            letterSpacing: 1.2,
          ),
        ),
      ],
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        color: Colors.grey,
        fontSize: 12,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Future<Position> _determinePosition() async {
    bool serviceEnabled;
    LocationPermission permission;

    // Test if location services are enabled.
    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return Future.error('Location services are disabled.');
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return Future.error('Location permissions are denied');
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return Future.error(
        'Location permissions are permanently denied, we cannot request permissions.',
      );
    }

    return await Geolocator.getCurrentPosition();
  }
}
