import 'package:flutter_test/flutter_test.dart';
import 'package:robolens_mobile/features/task_discovery/models/task_model.dart';

void main() {
  group('TaskModel', () {
    test('deserializes JSON properly from backend API contract', () {
      final json = {
        'id': 'task_test_123',
        'title': 'Tabletop Pick and Place',
        'description': 'Pick a mug and relocate it.',
        'instructions_md': '# Instructions\nGrasp firmly.',
        'category': 'tabletop_manipulation',
        'expected_duration_min': 5,
        'expected_duration_max': 25,
        'reward_amount': 120.0,
        'status': 'ACTIVE',
        'version': 1,
      };

      final task = TaskModel.fromJson(json);

      expect(task.id, 'task_test_123');
      expect(task.title, 'Tabletop Pick and Place');
      expect(task.category, 'tabletop_manipulation');
      expect(task.expectedDurationMin, 5);
      expect(task.expectedDurationMax, 25);
      expect(task.rewardAmount, 120.0);
      expect(task.status, 'ACTIVE');
      expect(task.version, 1);
    });

    test('serializes to JSON correctly', () {
      final task = TaskModel(
        id: 'task_demo',
        title: 'Drawer Pull',
        description: 'Pull cabinet drawer open.',
        instructions_md: 'Ensure drawer is in frame.',
        category: 'household_manipulation',
        expectedDurationMin: 10,
        expectedDurationMax: 30,
        rewardAmount: 180.0,
        status: 'ACTIVE',
        version: 2,
      );

      final json = task.toJson();
      expect(json['id'], 'task_demo');
      expect(json['category'], 'household_manipulation');
      expect(json['expected_duration_min'], 10);
      expect(json['reward_amount'], 180.0);
    });
  });
}
