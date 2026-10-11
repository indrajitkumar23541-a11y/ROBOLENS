import 'package:permission_handler/permission_handler.dart';

class PermissionService {
  /// Request camera and microphone permissions required for recording
  static Future<bool> requestRecordingPermissions() async {
    final cameraStatus = await Permission.camera.request();
    final micStatus = await Permission.microphone.request();

    return cameraStatus.isGranted && micStatus.isGranted;
  }

  /// Check whether camera and microphone are currently granted
  static Future<bool> hasRecordingPermissions() async {
    final cameraGranted = await Permission.camera.isGranted;
    final micGranted = await Permission.microphone.isGranted;

    return cameraGranted && micGranted;
  }

  /// Open app settings if user previously permanently denied permissions
  static Future<void> openSettings() async {
    await openAppSettings();
  }
}
