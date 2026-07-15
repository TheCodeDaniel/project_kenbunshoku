/// A single visitor alert as delivered over ntfy.sh.
class Alert {
  const Alert({required this.title, required this.message, required this.time});

  final String title;
  final String message;
  final DateTime time;

  /// Parses one line from ntfy.sh's `/<topic>/json` stream.
  factory Alert.fromNtfyJson(Map<String, dynamic> json) {
    final seconds = json['time'] as int? ?? 0;
    final title = json['title'] as String?;
    return Alert(
      title: (title != null && title.trim().isNotEmpty) ? title : 'Kenbunshoku alert',
      message: json['message'] as String? ?? '',
      time: DateTime.fromMillisecondsSinceEpoch(seconds * 1000),
    );
  }
}
