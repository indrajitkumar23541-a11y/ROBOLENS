import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../constants/api_constants.dart';
import '../storage/token_storage.dart';
import '../../features/task_discovery/models/task_model.dart';
import '../../features/submissions/models/submission_model.dart';

class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? errorMessage;

  ApiResponse({required this.success, this.data, this.errorMessage});
}

class ApiClient {
  final String baseUrl;

  ApiClient({this.baseUrl = ApiConstants.baseUrl});

  Future<Map<String, String>> _getHeaders({bool requireAuth = true}) async {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (requireAuth) {
      final token = await TokenStorage.getAccessToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return headers;
  }

  // ---------------------------------------------------------------------------
  // Authentication
  // ---------------------------------------------------------------------------
  Future<ApiResponse<Map<String, dynamic>>> login({
    required String email,
    required String password,
  }) async {
    try {
      final url = Uri.parse('$baseUrl${ApiConstants.login}');
      // OAuth2 form URL-encoded login
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {'username': email, 'password': password},
      );

      final body = jsonDecode(response.body);
      if (response.statusCode == 200 && body['success'] == true) {
        final data = body['data'];
        await TokenStorage.saveTokens(
          accessToken: data['access_token'],
          refreshToken: data['refresh_token'],
        );
        return ApiResponse(success: true, data: data);
      } else {
        final msg = body['error']?['message'] ?? 'Authentication failed';
        return ApiResponse(success: false, errorMessage: msg);
      }
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> register({
    required String email,
    required String password,
    String? fullName,
  }) async {
    try {
      final url = Uri.parse('$baseUrl${ApiConstants.register}');
      final response = await http.post(
        url,
        headers: await _getHeaders(requireAuth: false),
        body: jsonEncode({
          'email': email,
          'password': password,
          'full_name': fullName,
        }),
      );

      final body = jsonDecode(response.body);
      if (response.statusCode == 201 && body['success'] == true) {
        return ApiResponse(success: true, data: body['data']);
      } else {
        final msg = body['error']?['message'] ?? 'Registration failed';
        return ApiResponse(success: false, errorMessage: msg);
      }
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Network error: $e');
    }
  }

  // ---------------------------------------------------------------------------
  // Task Discovery
  // ---------------------------------------------------------------------------
  Future<ApiResponse<List<TaskModel>>> getTasks() async {
    try {
      final url = Uri.parse('$baseUrl${ApiConstants.tasks}');
      final response = await http.get(url, headers: await _getHeaders());

      final body = jsonDecode(response.body);
      if (response.statusCode == 200 && body['success'] == true) {
        final list = (body['data'] as List)
            .map((item) => TaskModel.fromJson(item))
            .toList();
        return ApiResponse(success: true, data: list);
      }
      return ApiResponse(success: false, errorMessage: body['error']?['message']);
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Failed to fetch tasks: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> checkTaskEligibility(String taskId) async {
    try {
      final url = Uri.parse('$baseUrl${ApiConstants.tasks}/$taskId/eligibility');
      final response = await http.get(url, headers: await _getHeaders());

      final body = jsonDecode(response.body);
      if (response.statusCode == 200 && body['success'] == true) {
        return ApiResponse(success: true, data: body['data']);
      }
      return ApiResponse(success: false, errorMessage: body['error']?['message']);
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Network error: $e');
    }
  }

  // ---------------------------------------------------------------------------
  // Submissions & Upload Lifecycle
  // ---------------------------------------------------------------------------
  Future<ApiResponse<Map<String, dynamic>>> createSubmission({
    required String taskId,
    bool consentAgreed = true,
  }) async {
    try {
      final url = Uri.parse('$baseUrl${ApiConstants.submissions}');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({
          'task_id': taskId,
          'consent_agreed': consentAgreed,
          'policy_version': '1.0',
        }),
      );

      final body = jsonDecode(response.body);
      if (response.statusCode == 201 && body['success'] == true) {
        return ApiResponse(success: true, data: body['data']);
      }
      return ApiResponse(success: false, errorMessage: body['error']?['message']);
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Failed to create submission: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> createUploadSession({
    required String submissionId,
    required String fileName,
    required int fileSizeBytes,
    String mimeType = 'video/mp4',
    String? checksumSha256,
  }) async {
    try {
      final url = Uri.parse('$baseUrl${ApiConstants.submissions}/$submissionId/uploads');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({
          'file_name': fileName,
          'file_size_bytes': fileSizeBytes,
          'mime_type': mimeType,
          'checksum_sha256': checksumSha256,
        }),
      );

      final body = jsonDecode(response.body);
      if (response.statusCode == 200 && body['success'] == true) {
        return ApiResponse(success: true, data: body['data']);
      }
      return ApiResponse(success: false, errorMessage: body['error']?['message']);
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Failed to request upload session: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> completeUpload({
    required String uploadId,
    String? checksumSha256,
    int? actualFileSize,
  }) async {
    try {
      final url = Uri.parse('$baseUrl/uploads/$uploadId/complete');
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({
          'checksum_sha256': checksumSha256,
          'actual_file_size': actualFileSize,
        }),
      );

      final body = jsonDecode(response.body);
      if (response.statusCode == 200 && body['success'] == true) {
        return ApiResponse(success: true, data: body['data']);
      }
      return ApiResponse(success: false, errorMessage: body['error']?['message']);
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Failed to complete upload: $e');
    }
  }

  Future<ApiResponse<List<SubmissionModel>>> getMySubmissions() async {
    try {
      final url = Uri.parse('$baseUrl${ApiConstants.submissions}');
      final response = await http.get(url, headers: await _getHeaders());

      final body = jsonDecode(response.body);
      if (response.statusCode == 200 && body['success'] == true) {
        final items = (body['data']?['items'] as List? ?? [])
            .map((item) => SubmissionModel.fromJson(item))
            .toList();
        return ApiResponse(success: true, data: items);
      }
      return ApiResponse(success: false, errorMessage: body['error']?['message']);
    } catch (e) {
      return ApiResponse(success: false, errorMessage: 'Failed to fetch submissions: $e');
    }
  }
}
