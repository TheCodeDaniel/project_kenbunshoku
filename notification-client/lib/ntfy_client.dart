import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models/alert.dart';

enum NtfyConnectionState { connecting, connected, disconnected }

/// Long-lived listener on an ntfy.sh topic's JSON stream.
///
/// Display only, per CLAUDE.md: this class only ever surfaces alerts to the
/// UI, it never acts on them. Reconnects automatically if the stream drops.
class NtfyClient {
  NtfyClient(this.topic);

  final String topic;

  final _alertController = StreamController<Alert>.broadcast();
  final _stateController = StreamController<NtfyConnectionState>.broadcast();

  Stream<Alert> get alerts => _alertController.stream;
  Stream<NtfyConnectionState> get connectionState => _stateController.stream;

  bool _stopped = false;
  http.Client? _activeClient;
  Timer? _retryTimer;
  Completer<void>? _retryCompleter;

  Uri get _streamUri => Uri.parse('https://ntfy.sh/$topic/json');

  Future<void> start() async {
    _stopped = false;
    while (!_stopped) {
      _stateController.add(NtfyConnectionState.connecting);
      try {
        await _listenOnce();
      } catch (_) {
        // fall through to the retry delay below
      }
      if (_stopped) break;
      _stateController.add(NtfyConnectionState.disconnected);
      await _retryDelay(const Duration(seconds: 3));
    }
  }

  /// Like `Future.delayed`, but `stop()` can cut it short so no Timer
  /// outlives this client (matters for tests, and for a clean widget dispose).
  Future<void> _retryDelay(Duration duration) {
    final completer = Completer<void>();
    _retryCompleter = completer;
    _retryTimer = Timer(duration, () {
      if (!completer.isCompleted) completer.complete();
    });
    return completer.future;
  }

  Future<void> _listenOnce() async {
    final client = http.Client();
    _activeClient = client;
    try {
      final response = await client.send(http.Request('GET', _streamUri));
      if (response.statusCode != 200) {
        throw Exception('ntfy subscribe failed: HTTP ${response.statusCode}');
      }

      _stateController.add(NtfyConnectionState.connected);

      await response.stream.transform(utf8.decoder).transform(const LineSplitter()).forEach((line) {
        if (line.trim().isEmpty) return;
        Map<String, dynamic> json;
        try {
          json = jsonDecode(line) as Map<String, dynamic>;
        } catch (_) {
          return;
        }
        if (json['event'] != 'message') return;
        _alertController.add(Alert.fromNtfyJson(json));
      });
    } finally {
      client.close();
    }
  }

  void stop() {
    _stopped = true;
    _activeClient?.close();
    _retryTimer?.cancel();
    if (_retryCompleter case final completer? when !completer.isCompleted) {
      completer.complete();
    }
  }

  void dispose() {
    stop();
    _alertController.close();
    _stateController.close();
  }
}
