import 'dart:async';
import 'package:flutter/material.dart';
import '../../task_discovery/models/task_model.dart';
import '../../video_preview/screens/video_preview_screen.dart';

class CameraRecordingScreen extends StatefulWidget {
  final TaskModel task;

  const CameraRecordingScreen({super.key, required this.task});

  @override
  State<CameraRecordingScreen> createState() => _CameraRecordingScreenState();
}

class _CameraRecordingScreenState extends State<CameraRecordingScreen> {
  bool _isRecording = false;
  int _secondsElapsed = 0;
  Timer? _timer;

  void _toggleRecording() {
    if (_isRecording) {
      _stopRecording();
    } else {
      _startRecording();
    }
  }

  void _startRecording() {
    setState(() {
      _isRecording = true;
      _secondsElapsed = 0;
    });

    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _secondsElapsed++;
      });
      // Stop automatically if exceeding maximum limit
      if (_secondsElapsed >= widget.task.expectedDurationMax) {
        _stopRecording();
      }
    });
  }

  void _stopRecording() {
    _timer?.cancel();
    setState(() {
      _isRecording = false;
    });

    if (_secondsElapsed < widget.task.expectedDurationMin) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Recording too short (${_secondsElapsed}s). Minimum required is ${widget.task.expectedDurationMin}s.',
          ),
          backgroundColor: Colors.orangeAccent,
        ),
      );
      return;
    }

    // Navigate to preview screen with simulated/actual recording path
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => VideoPreviewScreen(
          task: widget.task,
          durationSeconds: _secondsElapsed,
          videoPath: '/data/user/0/robolens/cache/recording_${DateTime.now().millisecondsSinceEpoch}.mp4',
        ),
      ),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Color _getTimerColor() {
    if (!_isRecording) return Colors.white;
    if (_secondsElapsed < widget.task.expectedDurationMin) return Colors.amber;
    if (_secondsElapsed <= widget.task.expectedDurationMax) return const Color(0xFF00E676);
    return Colors.redAccent;
  }

  @override
  Widget build(BuildContext context) {
    final task = widget.task;

    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(
          children: [
            // Camera Viewfinder Simulation / Overlay
            Container(
              width: double.infinity,
              height: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                border: Border.all(color: const Color(0xFF30363D)),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Framing Guidance Box
                  Container(
                    width: 280,
                    height: 280,
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: const Color(0xFF00E5FF).withOpacity(0.6),
                        width: 2,
                      ),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Center(
                      child: Text(
                        'Keep hands & objects inside frame',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: const Color(0xFF00E5FF).withOpacity(0.8),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),

                  // Top Status Header
                  Positioned(
                    top: 16,
                    left: 16,
                    right: 16,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.arrow_back, color: Colors.white),
                          onPressed: () => Navigator.pop(context),
                        ),
                        // Timer Indicator
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.7),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: _getTimerColor()),
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 10,
                                height: 10,
                                decoration: BoxDecoration(
                                  color: _isRecording ? Colors.red : Colors.grey,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                '${(_secondsElapsed ~/ 60).toString().padLeft(2, '0')}:${(_secondsElapsed % 60).toString().padLeft(2, '0')} / ${task.expectedDurationMin}-${task.expectedDurationMax}s',
                                style: TextStyle(
                                  color: _getTimerColor(),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 48), // Balance spacing
                      ],
                    ),
                  ),

                  // Bottom Controls
                  Positioned(
                    bottom: 24,
                    left: 20,
                    right: 20,
                    child: Column(
                      children: [
                        Text(
                          task.title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 16),
                        GestureDetector(
                          onTap: _toggleRecording,
                          child: Container(
                            width: 76,
                            height: 76,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.white, width: 4),
                            ),
                            child: Center(
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 200),
                                width: _isRecording ? 30 : 58,
                                height: _isRecording ? 30 : 58,
                                decoration: BoxDecoration(
                                  color: Colors.redAccent,
                                  borderRadius: BorderRadius.circular(_isRecording ? 8 : 29),
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          _isRecording ? 'TAP TO FINISH DEMONSTRATION' : 'TAP TO START RECORDING',
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 11,
                            letterSpacing: 1,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
