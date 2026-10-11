import 'package:flutter/material.dart';
import '../../task_discovery/models/task_model.dart';
import '../../recording/screens/camera_recording_screen.dart';
import '../../upload_manager/screens/upload_progress_sheet.dart';

class VideoPreviewScreen extends StatefulWidget {
  final TaskModel task;
  final int durationSeconds;
  final String videoPath;

  const VideoPreviewScreen({
    super.key,
    required this.task,
    required this.durationSeconds,
    required this.videoPath,
  });

  @override
  State<VideoPreviewScreen> createState() => _VideoPreviewScreenState();
}

class _VideoPreviewScreenState extends State<VideoPreviewScreen> {
  bool _consentAgreed = true;

  void _startUpload() {
    if (!_consentAgreed) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Explicit consent agreement is required to submit recording.'),
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }

    showModalBottomSheet(
      context: context,
      isDismissible: false,
      enableDrag: false,
      backgroundColor: Colors.transparent,
      builder: (context) => UploadProgressSheet(
        task: widget.task,
        videoPath: widget.videoPath,
        durationSeconds: widget.durationSeconds,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        title: const Text('PREVIEW DEMONSTRATION'),
        backgroundColor: const Color(0xFF161B22),
        automaticallyImplyLeading: false,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        children: [
          // Simulated Video Playback Container
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF30363D)),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00E5FF).withOpacity(0.15),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.play_arrow_rounded,
                          size: 48,
                          color: Color(0xFF00E5FF),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Recording Duration: ${widget.durationSeconds} seconds',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        widget.task.title,
                        style: const TextStyle(color: Colors.white54, fontSize: 13),
                      ),
                    ],
                  ),
                  Positioned(
                    bottom: 12,
                    right: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.7),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        '1080p · 30 FPS · H.264',
                        style: TextStyle(color: Colors.white70, fontSize: 11),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Explicit Consent Switch Card
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF161B22),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF30363D)),
            ),
            child: Row(
              children: [
                Switch(
                  value: _consentAgreed,
                  activeColor: const Color(0xFF00E5FF),
                  onChanged: (val) => setState(() => _consentAgreed = val),
                ),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'I confirm this demonstration was recorded by me and grant license for Physical AI model training (ROBOLENS Policy v1.0).',
                    style: TextStyle(fontSize: 12, color: Colors.white70),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Action Buttons: Retake vs Submit
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (context) => CameraRecordingScreen(task: widget.task),
                      ),
                    );
                  },
                  icon: const Icon(Icons.refresh, color: Colors.white70),
                  label: const Text('Discard & Retake', style: TextStyle(color: Colors.white70)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Color(0xFF30363D)),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _consentAgreed ? _startUpload : null,
                  icon: const Icon(Icons.cloud_upload_outlined, color: Colors.black),
                  label: const Text(
                    'Submit & Upload',
                    style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00E5FF),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
