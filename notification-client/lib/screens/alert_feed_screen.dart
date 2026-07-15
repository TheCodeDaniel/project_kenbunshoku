import 'package:flutter/material.dart';

import '../models/alert.dart';
import '../ntfy_client.dart';
import 'alert_detail_screen.dart';

/// List of past alerts, newest first. Display only — no controls beyond
/// tapping through to the detail view.
class AlertFeedScreen extends StatefulWidget {
  const AlertFeedScreen({super.key, required this.topic});

  final String topic;

  @override
  State<AlertFeedScreen> createState() => _AlertFeedScreenState();
}

class _AlertFeedScreenState extends State<AlertFeedScreen> {
  late final NtfyClient _client;
  final List<Alert> _alerts = [];
  NtfyConnectionState _connectionState = NtfyConnectionState.connecting;

  @override
  void initState() {
    super.initState();
    _client = NtfyClient(widget.topic);
    _client.alerts.listen((alert) {
      setState(() => _alerts.insert(0, alert));
    });
    _client.connectionState.listen((state) {
      setState(() => _connectionState = state);
    });
    _client.start();
  }

  @override
  void dispose() {
    _client.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kenbunshoku Alerts'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(28),
          child: Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: _ConnectionBadge(state: _connectionState, topic: widget.topic),
          ),
        ),
      ),
      body: _alerts.isEmpty ? const _EmptyState() : _AlertList(alerts: _alerts),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Text(
          'No alerts yet. Waiting for a visitor detection from cloud-backend…',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

class _AlertList extends StatelessWidget {
  const _AlertList({required this.alerts});

  final List<Alert> alerts;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      itemCount: alerts.length,
      separatorBuilder: (_, _) => const Divider(height: 1),
      itemBuilder: (context, index) {
        final alert = alerts[index];
        return ListTile(
          leading: const Icon(Icons.notifications_none),
          title: Text(alert.title),
          subtitle: Text(alert.message, maxLines: 2, overflow: TextOverflow.ellipsis),
          trailing: Text(_formatTime(alert.time)),
          onTap: () => Navigator.of(
            context,
          ).push(MaterialPageRoute(builder: (_) => AlertDetailScreen(alert: alert))),
        );
      },
    );
  }
}

String _formatTime(DateTime time) {
  final local = time.toLocal();
  final hh = local.hour.toString().padLeft(2, '0');
  final mm = local.minute.toString().padLeft(2, '0');
  return '$hh:$mm';
}

class _ConnectionBadge extends StatelessWidget {
  const _ConnectionBadge({required this.state, required this.topic});

  final NtfyConnectionState state;
  final String topic;

  @override
  Widget build(BuildContext context) {
    final (Color color, String label) = switch (state) {
      NtfyConnectionState.connected => (Colors.green, 'Connected'),
      NtfyConnectionState.connecting => (Colors.orange, 'Connecting…'),
      NtfyConnectionState.disconnected => (Colors.red, 'Disconnected — retrying'),
    };
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Icon(Icons.circle, size: 10, color: color),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              '$label · ntfy.sh/$topic',
              style: Theme.of(context).textTheme.bodySmall,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
