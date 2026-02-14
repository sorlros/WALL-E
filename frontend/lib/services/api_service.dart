import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class ApiService {
  // Use 10.0.2.2 for Android Emulator, localhost for iOS simulator/web
  // For physical device, use actual IP
  static const String baseUrl = 'http://10.0.2.2:8000';

  // 사용자 정보 저장
  static Map<String, dynamic>? _currentUser;
  static String? _accessToken;
  static String? _refreshToken;

  static Map<String, dynamic>? get currentUser => _currentUser;
  static String? get accessToken => _accessToken;
  static bool get isLoggedIn => _currentUser != null;

  // LOGIN
  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      // 사용자 정보 저장
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];
      _currentUser = data['user'];
      return data;
    } else {
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
  static Future<Map<String, dynamic>> signup(
    String email,
    String password,
    String name,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/signup'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password, 'name': name}),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Signup failed: ${response.body}');
    }
  }

  // Create a new mission
  static Future<Map<String, dynamic>> createMission(
    String name,
    String description,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/missions/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name, 'description': description}),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
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
    double? latitude,
    double? longitude,
  }) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/missions/$missionId/detections'),
    );

    request.fields['label'] = label;
    request.fields['confidence'] = confidence.toString();
    if (latitude != null) request.fields['gps_lat'] = latitude.toString();
    if (longitude != null) request.fields['gps_lng'] = longitude.toString();

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
  static Future<List<dynamic>> getMissions() async {
    final response = await http.get(Uri.parse('$baseUrl/missions/'));

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
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
}
