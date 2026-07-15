import 'package:flutter/material.dart';

import 'screens/alert_feed_screen.dart';

/// Which ntfy.sh topic to listen on. Must match cloud-backend's
/// PUSH_ENDPOINT (see repo-root .env / alert_dispatcher.py). Override with:
///   flutter run --dart-define=NTFY_TOPIC=your-topic
const String ntfyTopic = String.fromEnvironment('NTFY_TOPIC', defaultValue: 'kenbunshoku-alerts-242f117db45b');

void main() {
  runApp(const KenbunshokuNotifyApp());
}

class KenbunshokuNotifyApp extends StatelessWidget {
  const KenbunshokuNotifyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kenbunshoku Alerts',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo)),
      home: const AlertFeedScreen(topic: ntfyTopic),
    );
  }
}
