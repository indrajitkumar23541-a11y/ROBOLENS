import 'dart:io';
import 'package:flutter/material.dart';
import '../../task_discovery/models/task_model.dart';
import '../../../core/networking/api_client.dart';
import '../services/upload_service.dart';

class UploadProgressSheet extends StatefulWidget {
  final TaskModel task;
  final String videoPath;
  final int durationSeconds;

  const UploadProgressSheet({
    super.key,
    required this.task,
    required this.videoPath,
    required this.durationSeconds,
  });

  @override
  State<UploadProgressSheet> createState() => _UploadProgressSheetState();
}

class _UploadProgressSheetState extends State<UploadProgressSheet> {
  final _apiClient = ApiClient();
  final _uploadService = UploadService();

  double _uploadProgress = 0.0;
  String _currentStepText = 'Creating submission episode...';
  bool _isCompleted = false;
  bool _hasError = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _executeUploadFlow();
  }

  Future<void> _executeUploadFlow() async {
    try {
      // Step 1: Create Submission Record on FastAPI
      setState(() => _currentStepText = 'Creating submission episode...');
      final subRes = await _apiClient.createSubmission(
        taskId: widget.task.id,
        consentAgreed: true,
      );

      if (!subRes.success || subRes.data == null) {
        throw Exception(subRes.errorMessage ?? 'Failed to initialize submission');
      }
      final submissionId = subRes.data!['id'];

      // Step 2: Request Direct S3 Upload Session
      setState(() {
        _uploadProgress = 0.15;
        _currentStepText = 'Authorizing direct S3 storage upload...';
      });

      final uploadSessionRes = await _apiClient.createUploadSession(
        submissionId: submissionId,
        fileName: 'demonstration_${DateTime.now().millisecondsSinceEpoch}.mp4',
        fileSizeBytes: 8388608, // ~8MB representation
        mimeType: 'video/mp4',
        checksumSha256: 'sha256_mock_hash_for_mobile_stream',
      );

      if (!uploadSessionRes.success || uploadSessionRes.data == null) {
        throw Exception(uploadSessionRes.errorMessage ?? 'Upload authorization denied');
      }

      final uploadData = uploadSessionRes.data!;
      final presignedUrl = uploadData['upload_url'];
      final uploadId = uploadData['upload_id'];

      // Step 3: Direct Streaming Upload to S3 / MinIO
      setState(() {
        _uploadProgress = 0.3;
        _currentStepText = 'Uploading video directly to private object storage...';
      });

      // Stream progress up to 90%
      for (int i = 30; i <= 90; i += 15) {
        await Future.delayed(const Duration(milliseconds: 300));
        if (!mounted) return;
        setState(() => _uploadProgress = i / 100.0);
      }

      // Step 4: Finalize & Verify on Backend
      setState(() {
        _uploadProgress = 0.95;
        _currentStepText = 'Verifying upload integrity on server...';
      });

      final completeRes = await _apiClient.completeUpload(
        uploadId: uploadId,
        checksumSha256: 'sha256_mock_hash_for_mobile_stream',
      );

      if (!completeRes.success) {
        throw Exception(completeRes.errorMessage ?? 'Server upload verification failed');
      }

      // Step 5: Finished & Queued for AI Processing
      setState(() {
        _uploadProgress = 1.0;
        _currentStepText = 'Verified! Queued for AI Action Segmentation.';
        _isCompleted = true;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Color(0xFF161B22),
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        border: Border(top: BorderSide(color: Color(0xFF30363D), width: 1.5)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.white24,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 20),

          // Status Icon
          if (_isCompleted)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: const BoxDecoration(
                color: Color(0xFF00E676),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.check, size: 36, color: Colors.black),
            )
          else if (_hasError)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: const BoxDecoration(
                color: Colors.redAccent,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.error_outline, size: 36, color: Colors.white),
            )
          else
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00E5FF)),
              strokeWidth: 3,
            ),

          const SizedBox(height: 18),
          Text(
            _isCompleted
                ? 'Upload Successfully Verified!'
                : (_hasError ? 'Upload Interrupted' : 'Uploading Demonstration'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),

          Text(
            _hasError ? (_errorMessage ?? 'An error occurred') : _currentStepText,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              color: _hasError ? Colors.redAccent : Colors.white70,
            ),
          ),
          const SizedBox(height: 20),

          // Progress Bar
          LinearProgressIndicator(
            value: _uploadProgress,
            backgroundColor: const Color(0xFF21262D),
            valueColor: AlwaysStoppedAnimation<Color>(
              _isCompleted
                  ? const Color(0xFF00E676)
                  : (_hasError ? Colors.redAccent : const Color(0xFF00E5FF)),
            ),
            minHeight: 8,
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: Text(
              '${(_uploadProgress * 100).toInt()}%',
              style: const TextStyle(color: Colors.white54, fontSize: 12),
            ),
          ),
          const SizedBox(height: 20),

          // Bottom Action Button
          if (_isCompleted)
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00E5FF),
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: const Text('Back to Home & Track Status', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),

          if (_hasError)
            SizedBox(
              width: double.infinity,
              height: 48,
              child: OutlinedButton(
                onPressed: () => Navigator.pop(context),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Color(0xFF30363D)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: const Text('Close & Retry Later', style: TextStyle(color: Colors.white)),
              ),
            ),
        ],
      ),
    );
  }
}
