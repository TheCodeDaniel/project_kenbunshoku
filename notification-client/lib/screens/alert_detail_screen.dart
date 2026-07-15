import 'package:flutter/material.dart';

import '../models/alert.dart';

/// Full reasoning text for a single alert. Display only — no actions.
class AlertDetailScreen extends StatelessWidget {
  const AlertDetailScreen({super.key, required this.alert});

  final Alert alert;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(alert.title)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_formatFullTime(alert.time), style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            Text(alert.message, style: Theme.of(context).textTheme.bodyLarge),
          ],
        ),
      ),
    );
  }
}

String _formatFullTime(DateTime time) {
  final local = time.toLocal();
  return '${local.year}-${_pad(local.month)}-${_pad(local.day)} '
      '${_pad(local.hour)}:${_pad(local.minute)}:${_pad(local.second)}';
}

String _pad(int value) => value.toString().padLeft(2, '0');
