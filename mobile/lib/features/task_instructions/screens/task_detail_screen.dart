import 'package:flutter/material.dart';
import '../../task_discovery/models/task_model.dart';
import '../../../core/networking/api_client.dart';
import '../../recording/screens/camera_recording_screen.dart';

class TaskDetailScreen extends StatefulWidget {
  final TaskModel task;

  const TaskDetailScreen({super.key, required this.task});

  @override
  State<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends State<TaskDetailScreen> {
  final _apiClient = ApiClient();
  bool _isCheckingEligibility = true;
  bool _isEligible = true;
  String? _eligibilityReason;

  @override
  void initState() {
    super.initState();
    _checkEligibility();
  }

  Future<void> _checkEligibility() async {
    final res = await _apiClient.checkTaskEligibility(widget.task.id);
    if (mounted) {
      setState(() {
        _isCheckingEligibility = false;
        if (res.success && res.data != null) {
          _isEligible = res.data!['eligible'] ?? true;
          _eligibilityReason = res.data!['reason'];
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final task = widget.task;

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        title: Text(task.title),
        backgroundColor: const Color(0xFF161B22),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Header Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF161B22),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFF30363D)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFF21262D),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        task.category.toUpperCase().replaceAll('_', ' '),
                        style: const TextStyle(
                          color: Color(0xFF00E5FF),
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ),
                    Text(
                      '₹${task.rewardAmount.toInt()}',
                      style: const TextStyle(
                        color: Color(0xFF00E676),
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  task.title,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  task.description,
                  style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
                ),
                const Divider(height: 24, color: Color(0xFF30363D)),
                Row(
                  children: [
                    const Icon(Icons.timer_outlined, size: 16, color: Colors.white54),
                    const SizedBox(width: 6),
                    Text(
                      'Target Duration: ${task.expectedDurationMin}s – ${task.expectedDurationMax}s',
                      style: const TextStyle(color: Colors.white70, fontSize: 13),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Eligibility Banner
          if (!_isCheckingEligibility && !_isEligible)
            Container(
              margin: const EdgeInsets.only(bottom: 20),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.15),
                border: Border.all(color: Colors.orangeAccent),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: Colors.orangeAccent),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _eligibilityReason ?? 'Task quota reached.',
                      style: const TextStyle(color: Colors.orangeAccent, fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),

          // Recording Guidelines
          const Text(
            'Recording Guidelines & Instructions',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF161B22),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF30363D)),
            ),
            child: Text(
              task.instructionsMd.isNotEmpty
                  ? task.instructionsMd
                  : '• Ensure stable, clear lighting.\n• Keep hands and target objects within the camera frame.\n• Complete action steadily without abrupt jerks.',
              style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.5),
            ),
          ),
          const SizedBox(height: 30),

          // Begin Recording Action Button
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _isEligible && !_isCheckingEligibility
                  ? () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => CameraRecordingScreen(task: task),
                        ),
                      );
                    }
                  : null,
              icon: const Icon(Icons.videocam, color: Colors.black),
              label: const Text(
                'Accept & Open Recording Camera',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.black),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00E5FF),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
