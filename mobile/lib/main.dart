import 'package:flutter/material.dart';
import 'core/networking/api_client.dart';
import 'core/storage/token_storage.dart';
import 'features/authentication/screens/login_screen.dart';
import 'features/task_discovery/models/task_model.dart';
import 'features/task_instructions/screens/task_detail_screen.dart';
import 'features/submissions/models/submission_model.dart';

void main() {
  runApp(const RoboLensApp());
}

class RoboLensApp extends StatelessWidget {
  const RoboLensApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ROBOLENS',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF070B14),
        primaryColor: const Color(0xFF0066FF),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF0066FF),
          secondary: Color(0xFF00E676),
          surface: Color(0xFF0E1424),
          background: Color(0xFF070B14),
        ),
        cardTheme: CardTheme(
          color: const Color(0xFF131B2E),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF1E293B), width: 1),
          ),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF161B22),
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            letterSpacing: 1.2,
            color: Colors.white,
          ),
        ),
      ),
      home: const AuthGate(),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  bool _isAuthenticated = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkExistingAuth();
  }

  Future<void> _checkExistingAuth() async {
    final token = await TokenStorage.getAccessToken();
    setState(() {
      _isAuthenticated = token != null;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: Color(0xFF0D1117),
        body: Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF))),
      );
    }

    if (!_isAuthenticated) {
      return LoginScreen(
        onLoginSuccess: () => setState(() => _isAuthenticated = true),
      );
    }

    return MainNavigationScreen(
      onLogout: () async {
        await TokenStorage.clearTokens();
        setState(() => _isAuthenticated = false);
      },
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  final VoidCallback onLogout;

  const MainNavigationScreen({super.key, required this.onLogout});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final screens = [
      const TaskDiscoveryScreen(),
      const SubmissionsListScreen(),
      ProfileScreen(onLogout: widget.onLogout),
    ];

    return Scaffold(
      body: screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        backgroundColor: const Color(0xFF161B22),
        indicatorColor: const Color(0xFF00E5FF).withOpacity(0.2),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.explore_outlined),
            selectedIcon: Icon(Icons.explore, color: Color(0xFF00E5FF)),
            label: 'Explore Tasks',
          ),
          NavigationDestination(
            icon: Icon(Icons.history_outlined),
            selectedIcon: Icon(Icons.history, color: Color(0xFF00E5FF)),
            label: 'My Submissions',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person, color: Color(0xFF00E5FF)),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// 1. Task Discovery Screen (Dynamic from FastAPI Backend)
// ---------------------------------------------------------------------------
class TaskDiscoveryScreen extends StatefulWidget {
  const TaskDiscoveryScreen({super.key});

  @override
  State<TaskDiscoveryScreen> createState() => _TaskDiscoveryScreenState();
}

class _TaskDiscoveryScreenState extends State<TaskDiscoveryScreen> {
  final _apiClient = ApiClient();
  List<TaskModel> _tasks = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  Future<void> _loadTasks() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final res = await _apiClient.getTasks();
    if (mounted) {
      setState(() {
        _isLoading = false;
        if (res.success && res.data != null) {
          _tasks = res.data!;
        } else {
          _error = res.errorMessage ?? 'Could not load tasks';
          // Fallback static tasks if local server isn't running on device yet
          if (_tasks.isEmpty) {
            _tasks = _getFallbackTasks();
          }
        }
      });
    }
  }

  List<TaskModel> _getFallbackTasks() {
    return [
      TaskModel(
        id: 'task_cup_manipulation_v1',
        title: 'Tabletop Cup Pick & Place',
        category: 'tabletop_manipulation',
        description: 'Pick cup from table, rotate 90°, and place into marked tray.',
        instructions_md: 'Position camera angled 30° from above. Reach and grasp cup firmly.',
        expectedDurationMin: 8,
        expectedDurationMax: 35,
        rewardAmount: 150.0,
        status: 'ACTIVE',
        version: 1,
      ),
      TaskModel(
        id: 'task_drawer_storage_v1',
        title: 'Cabinet Drawer Pull & Storage',
        category: 'household_manipulation',
        description: 'Grasp handle, pull drawer open, place item inside, and close.',
        instructions_md: 'Ensure drawer face and interior are visible.',
        expectedDurationMin: 10,
        expectedDurationMax: 45,
        rewardAmount: 200.0,
        status: 'ACTIVE',
        version: 1,
      ),
      TaskModel(
        id: 'task_peg_alignment_v1',
        title: 'Peg-in-Hole Precision Alignment',
        category: 'precision_assembly',
        description: 'Pick peg and insert vertically into receptacle hole with precision.',
        instructions_md: 'Close-up camera framing on receptacle opening.',
        expectedDurationMin: 12,
        expectedDurationMax: 60,
        rewardAmount: 280.0,
        status: 'ACTIVE',
        version: 1,
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ROBOLENS — TASKS'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadTasks),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadTasks,
        color: const Color(0xFF00E5FF),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Hero Banner
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF00E5FF), Color(0xFF0091EA)],
                ),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Every Action Teaches AI.',
                    style: TextStyle(
                      color: Colors.black,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 6),
                  Text(
                    'Record real-world human task demonstrations to train next-generation Robotics & Physical AI models.',
                    style: TextStyle(color: Colors.black87, fontSize: 13, height: 1.3),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Available Data Collection Tasks',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),

            if (_isLoading)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(40),
                  child: CircularProgressIndicator(color: Color(0xFF00E5FF)),
                ),
              )
            else
              ..._tasks.map(
                (task) => Card(
                  margin: const EdgeInsets.only(bottom: 14),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF21262D),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                task.category.toUpperCase().replaceAll('_', ' '),
                                style: const TextStyle(
                                  color: Color(0xFF00E5FF),
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            Text(
                              '₹${task.rewardAmount.toInt()}',
                              style: const TextStyle(
                                color: Color(0xFF00E676),
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Text(
                          task.title,
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          task.description,
                          style: const TextStyle(color: Colors.white70, fontSize: 13),
                        ),
                        const SizedBox(height: 14),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                const Icon(Icons.timer_outlined, size: 14, color: Colors.white54),
                                const SizedBox(width: 4),
                                Text(
                                  '${task.expectedDurationMin}-${task.expectedDurationMax}s',
                                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                                ),
                              ],
                            ),
                            ElevatedButton(
                              onPressed: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => TaskDetailScreen(task: task),
                                  ),
                                );
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF00E5FF),
                                foregroundColor: Colors.black,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              ),
                              child: const Text('View Guidelines', style: TextStyle(fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// 2. Submissions Screen
// ---------------------------------------------------------------------------
class SubmissionsListScreen extends StatefulWidget {
  const SubmissionsListScreen({super.key});

  @override
  State<SubmissionsListScreen> createState() => _SubmissionsListScreenState();
}

class _SubmissionsListScreenState extends State<SubmissionsListScreen> {
  final _apiClient = ApiClient();
  List<SubmissionModel> _submissions = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSubmissions();
  }

  Future<void> _loadSubmissions() async {
    setState(() => _isLoading = true);
    final res = await _apiClient.getMySubmissions();
    if (mounted) {
      setState(() {
        _isLoading = false;
        if (res.success && res.data != null) {
          _submissions = res.data!;
        }
      });
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'APPROVED':
        return const Color(0xFF00E676);
      case 'PROCESSING':
        return const Color(0xFF00E5FF);
      case 'IN_REVIEW':
        return Colors.amber;
      case 'REJECTED':
      case 'FAILED':
        return Colors.redAccent;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MY SUBMISSIONS'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadSubmissions),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadSubmissions,
        color: const Color(0xFF00E5FF),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
            : _submissions.isEmpty
                ? const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.video_library_outlined, size: 60, color: Colors.white24),
                          SizedBox(height: 12),
                          Text(
                            'No recorded demonstrations yet.',
                            style: TextStyle(color: Colors.white70, fontSize: 15),
                          ),
                          SizedBox(height: 6),
                          Text(
                            'Select a task from "Explore Tasks" to begin recording.',
                            style: TextStyle(color: Colors.white38, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _submissions.length,
                    itemBuilder: (context, index) {
                      final s = _submissions[index];
                      final color = _getStatusColor(s.status);
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          contentPadding: const EdgeInsets.all(16),
                          title: Text(
                            'Episode ${s.episodeId.substring(0, 8)}',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text('Task ID: ${s.taskId}'),
                          ),
                          trailing: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: color.withOpacity(0.15),
                              border: Border.all(color: color),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              s.status,
                              style: TextStyle(
                                color: color,
                                fontWeight: FontWeight.bold,
                                fontSize: 11,
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// 3. Contributor Profile Screen
// ---------------------------------------------------------------------------
class ProfileScreen extends StatelessWidget {
  final VoidCallback onLogout;

  const ProfileScreen({super.key, required this.onLogout});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('CONTRIBUTOR PROFILE')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Center(
            child: CircleAvatar(
              radius: 42,
              backgroundColor: Color(0xFF00E5FF),
              child: Icon(Icons.person, size: 48, color: Colors.black),
            ),
          ),
          const SizedBox(height: 14),
          const Center(
            child: Text(
              'Verified Contributor',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),
          const Center(
            child: Text(
              'Physical AI Demonstration Contributor',
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
          ),
          const SizedBox(height: 28),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.verified_user_outlined, color: Color(0xFF00E676)),
                  title: const Text('Training Data Consent'),
                  subtitle: const Text('Policy v1.0 (Active & Granted)'),
                  trailing: const Icon(Icons.check_circle, color: Color(0xFF00E676), size: 20),
                ),
                const Divider(height: 1, color: Color(0xFF30363D)),
                ListTile(
                  leading: const Icon(Icons.lock_outline, color: Color(0xFF00E5FF)),
                  title: const Text('Privacy & Direct S3 Storage'),
                  subtitle: const Text('End-to-End Encrypted Storage'),
                  trailing: const Icon(Icons.chevron_right),
                ),
                const Divider(height: 1, color: Color(0xFF30363D)),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.redAccent),
                  title: const Text('Sign Out Session', style: TextStyle(color: Colors.redAccent)),
                  onTap: onLogout,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
