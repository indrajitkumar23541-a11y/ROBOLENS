import 'dart:io';
import 'package:dio/dio.dart';

class UploadService {
  final Dio _dio = Dio();

  /// Upload video file directly to S3/MinIO using presigned PUT URL
  /// Reports real-time progress back to UI (0.0 to 1.0)
  Future<bool> uploadVideoToS3({
    required String presignedUrl,
    required File videoFile,
    required String mimeType,
    required Function(double progress) onProgress,
  }) async {
    try {
      final fileLength = await videoFile.length();
      
      final response = await _dio.put(
        presignedUrl,
        data: videoFile.openRead(),
        options: Options(
          headers: {
            Headers.contentLengthHeader: fileLength,
            Headers.contentTypeHeader: mimeType,
          },
        ),
        onSendProgress: (int sent, int total) {
          if (total > 0) {
            final progress = sent / total;
            onProgress(progress);
          }
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
