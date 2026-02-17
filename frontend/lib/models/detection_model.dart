class Detection {
  final int id;
  final int missionId;
  final String imageUrl;
  final String label;
  final double confidence;
  final List<dynamic>? bbox;
  final DateTime createdAt;

  Detection({
    required this.id,
    required this.missionId,
    required this.imageUrl,
    required this.label,
    required this.confidence,
    this.bbox,
    required this.createdAt,
  });

  factory Detection.fromJson(Map<String, dynamic> json) {
    return Detection(
      id: json['id'],
      missionId: json['mission_id'],
      imageUrl: json['image_url'],
      label: json['label'],
      confidence: json['confidence'].toDouble(),
      bbox: json['bbox'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'mission_id': missionId,
      'image_url': imageUrl,
      'label': label,
      'confidence': confidence,
      'bbox': bbox,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
