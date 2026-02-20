import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../models/mission_model.dart';

class ApiService {
  static SharedPreferences? _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  static String get apiIp => _prefs?.getString('API_IP') ?? '';
  static String get apiPort => _prefs?.getString('API_PORT') ?? '';

  static Future<void> setServerConfig(String ip, String port) async {
    if (_prefs == null) await init();
    await _prefs?.setString('API_IP', ip);
    await _prefs?.setString('API_PORT', port);
  }

  // Use 10.0.2.2 for Android Emulator, localhost for iOS simulator/web
  // For physical device, use actual IP
  static String get baseUrl {
    if (apiIp.isNotEmpty && apiPort.isNotEmpty) {
      return 'http://$apiIp:$apiPort';
    }
    return dotenv.env['API_BASE_URL'] ?? 'http://10.0.2.2:8000';
  }

  // 사용자 정보 저장
  static User? _currentUser;
  static String? _accessToken;
  static String? _refreshToken;

  static User? get currentUser => _currentUser;
  static String? get accessToken => _accessToken;
  static bool get isLoggedIn => _currentUser != null;

  // LOGIN
  static Future<User> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      // 사용자 정보 저장
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];

      _currentUser = User.fromJson(data['user']);
      print('✅ 로그인 성공! User: ${_currentUser?.email}');
      return _currentUser!;
    } else {
      print('❌ 로그인 실패: ${response.body}');
      throw Exception('Login failed: ${response.body}');
    }
  }

  // LOGOUT
  static void logout() {
    _currentUser = null;
    _accessToken = null;
    _refreshToken = null;
  }

  // SIGNUP
  static Future<User> signup(String email, String password, String name) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/signup'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password, 'name': name}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      // Backend returns {message: ..., user: ...}
      // Note: User might be null if email confirmation required, but typically returns user object
      if (data['user'] != null) {
        return User.fromJson(data['user']);
      } else {
        // Fallback or specific handling for unconfirmed user
        throw Exception(
          'Signup successful but user data missing (verification needed?)',
        );
      }
    } else {
      throw Exception('Signup failed: ${response.body}');
    }
  }

  // Create a new mission
  static Future<Mission> createMission(
    String name,
    String description,
    double? lat,
    double? lng,
  ) async {
    if (_accessToken == null) {
      throw Exception('Not authenticated');
    }

    final response = await http.post(
      Uri.parse('$baseUrl/missions/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_accessToken',
      },
      body: jsonEncode({
        'name': name,
        'description': description,
        'gps_lat': lat,
        'gps_lng': lng,
      }),
    );

    if (response.statusCode == 200) {
      return Mission.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
    } else {
      throw Exception('Failed to create mission: ${response.body}');
    }
  }

  // Upload a detection (image + metadata)
  static Future<void> uploadDetection({
    required int missionId,
    required File imageFile,
    required String label,
    required double confidence,
  }) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/missions/$missionId/detections'),
    );

    request.fields['label'] = label;
    request.fields['confidence'] = confidence.toString();

    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        imageFile.path,
        contentType: MediaType('image', 'jpeg'),
      ),
    );

    var response = await request.send();

    if (response.statusCode != 200) {
      final respStr = await response.stream.bytesToString();
      throw Exception('Failed to upload detection: $respStr');
    }
  }

  // Fetch all missions
  static Future<List<Mission>> getMissions() async {
    if (_accessToken == null) {
      throw Exception('Not authenticated');
    }

    final response = await http.get(
      Uri.parse('$baseUrl/missions/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_accessToken',
      },
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(utf8.decode(response.bodyBytes));
      List<Mission> missions = body
          .map((dynamic item) => Mission.fromJson(item))
          .toList();
      return missions;
    } else {
      throw Exception('Failed to load missions');
    }
  }

  // Complete a mission (stop auto-saving)
  static Future<void> completeMission(int missionId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/missions/$missionId/complete'),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to complete mission: ${response.body}');
    }
  }

  // Update GPS for a specific detection
  static Future<void> updateDetectionGps(
    int detectionId,
    double lat,
    double lng,
  ) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/missions/detections/$detectionId/gps'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'gps_lat': lat.toString(), 'gps_lng': lng.toString()},
    );

    if (response.statusCode != 200) {
      print(
        '❌ Failed to update GPS for detection $detectionId: ${response.body}',
      );
    } else {
      print('✅ GPS updated for detection $detectionId');
    }
  }
}
