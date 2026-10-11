class SubmissionModel {
  final String id;
  final String taskId;
  final String episodeId;
  final String status;
  final int taskVersion;
  final String? rejectionReason;
  final DateTime createdAt;

  SubmissionModel({
    required this.id,
    required this.taskId,
    required this.episodeId,
    required this.status,
    required this.taskVersion,
    this.rejectionReason,
    required this.createdAt,
  });

  factory SubmissionModel.fromJson(Map<String, dynamic> json) {
    return SubmissionModel(
      id: json['id'] ?? '',
      taskId: json['task_id'] ?? '',
      episodeId: json['episode_id'] ?? '',
      status: json['status'] ?? 'DRAFT',
      taskVersion: json['task_version'] ?? 1,
      rejectionReason: json['rejection_reason'],
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}
