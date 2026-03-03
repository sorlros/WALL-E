class User {
  final String id;
  final String email;
  final Map<String, dynamic> metadata;

  User({required this.id, required this.email, required this.metadata});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      metadata: json['user_metadata'] ?? {},
    );
  }
}
