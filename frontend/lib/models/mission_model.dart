import 'detection_model.dart';

class Mission {
  final int id;
  final String name;
  final String? description;
  final double? latitude;
  final double? longitude;
  final String? locationName;
  final String? locationAddress;
  final DateTime createdAt;
  final List<Detection> detections;

  Mission({
    required this.id,
    required this.name,
    this.description,
    this.latitude,
    this.longitude,
    this.locationName,
    this.locationAddress,
    required this.createdAt,
    this.detections = const [],
  });

  factory Mission.fromJson(Map<String, dynamic> json) {
    var detectionsList = <Detection>[];
    if (json['detections'] != null) {
      detectionsList = (json['detections'] as List)
          .map((i) => Detection.fromJson(i))
          .toList();
    }

    return Mission(
      id: json['id'],
      name: json['title'] ?? json['name'] ?? 'Untitled',
      description: json['description'],
      latitude: json['gps_lat'],
      longitude: json['gps_lng'],
      locationName: json['location_name'],
      locationAddress: json['location_address'],
      createdAt: DateTime.parse(json['created_at']),
      detections: detectionsList,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'gps_lat': latitude,
      'gps_lng': longitude,
      'location_name': locationName,
      'location_address': locationAddress,
      'created_at': createdAt.toIso8601String(),
      'detections': detections
          .map((d) => d.toJson())
          .toList(), // Need to add toJson to Detection
    };
  }
}
