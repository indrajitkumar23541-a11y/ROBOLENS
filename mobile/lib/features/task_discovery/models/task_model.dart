class TaskModel {
  final String id;
  final String title;
  final String description;
  final String instructionsMd;
  final String category;
  final int expectedDurationMin;
  final int expectedDurationMax;
  final double rewardAmount;
  final String status;
  final int version;

  TaskModel({
    required this.id,
    required this.title,
    required this.description,
    required this.instructionsMd,
    required this.category,
    required this.expectedDurationMin,
    required this.expectedDurationMax,
    required this.rewardAmount,
    required this.status,
    required this.version,
  });

  factory TaskModel.fromJson(Map<String, dynamic> json) {
    return TaskModel(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      instructionsMd: json['instructions_md'] ?? '',
      category: json['category'] ?? '',
      expectedDurationMin: json['expected_duration_min'] ?? 5,
      expectedDurationMax: json['expected_duration_max'] ?? 180,
      rewardAmount: (json['reward_amount'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] ?? 'ACTIVE',
      version: json['version'] ?? 1,
    );
  }
}
