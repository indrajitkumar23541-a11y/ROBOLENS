import 'package:flutter_test/flutter_test.dart';
import 'package:robolens_mobile/features/submissions/models/submission_model.dart';

void main() {
  group('SubmissionModel', () {
    test('deserializes JSON properly from backend API contract', () {
      final json = {
        'id': 'sub_abc_123',
        'task_id': 'task_cup_manipulation_v1',
        'episode_id': 'ep_987654321',
        'status': 'PROCESSING',
        'task_version': 1,
        'created_at': '2026-10-11T12:00:00Z',
        'media_assets': [
          {
            'id': 'asset_1',
            'asset_type': 'RAW_VIDEO',
            'file_size_bytes': 15400000,
            'mime_type': 'video/mp4',
            'duration_seconds': 14.5,
            'status': 'VERIFIED',
          }
        ],
      };

      final sub = SubmissionModel.fromJson(json);

      expect(sub.id, 'sub_abc_123');
      expect(sub.taskId, 'task_cup_manipulation_v1');
      expect(sub.episodeId, 'ep_987654321');
      expect(sub.status, 'PROCESSING');
      expect(sub.taskVersion, 1);
      expect(sub.mediaAssets.length, 1);
      expect(sub.mediaAssets.first.fileSizeBytes, 15400000);
      expect(sub.mediaAssets.first.status, 'VERIFIED');
    });

    test('serializes to JSON correctly', () {
      final sub = SubmissionModel(
        id: 'sub_xyz',
        taskId: 'task_xyz',
        episodeId: 'ep_xyz',
        status: 'IN_REVIEW',
        taskVersion: 1,
        createdAt: '2026-10-11T13:00:00Z',
      );

      final json = sub.toJson();
      expect(json['id'], 'sub_xyz');
      expect(json['status'], 'IN_REVIEW');
    });
  });
}
