class ApiConstants {
  // Physical Device (Wi-Fi): http://10.83.134.3:8000/api/v1
  // Android Emulator: http://10.0.2.2:8000/api/v1
  // iOS Simulator / Desktop: http://127.0.0.1:8000/api/v1
  static const String baseUrl = "http://10.83.134.3:8000/api/v1";

  // Auth endpoints
  static const String register = "/auth/register";
  static const String login = "/auth/login";
  static const String refresh = "/auth/refresh";
  static const String profile = "/auth/users/me";

  // Task endpoints
  static const String tasks = "/tasks";

  // Submission & Upload endpoints
  static const String submissions = "/submissions";
}
