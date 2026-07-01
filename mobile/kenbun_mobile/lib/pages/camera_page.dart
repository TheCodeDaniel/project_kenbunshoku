import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:kenbun_mobile/services/api_service.dart';

/// Camera page that captures frames and sends them to the backend for analysis.
class CameraPage extends StatefulWidget {
  const CameraPage({super.key});

  @override
  State<CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends State<CameraPage> {
  late final ApiService _apiService;
  late List<CameraDescription> _cameras;
  late CameraController _controller;
  bool _isAnalyzing = false;
  AlertResult? _lastAlert;
  List<Map<String, dynamic>> _familiarFaces = [];
  bool _cameraInitialized = false;

  @override
  void initState() {
    super.initState();
    _apiService = ApiService(baseUrl: 'http://192.168.1.100:8000');
    _initializeCamera();
    _loadFamiliarFaces();
  }

  Future<void> _initializeCamera() async {
    try {
      _cameras = await availableCameras();
      _controller = CameraController(_cameras[0], ResolutionPreset.high, imageFormatGroup: ImageFormatGroup.jpeg);
      await _controller.initialize();
      if (!mounted) return;
      setState(() => _cameraInitialized = true);
    } catch (e) {
      debugPrint('Camera initialization error: $e');
    }
  }

  Future<void> _loadFamiliarFaces() async {
    try {
      final faces = await _apiService.getFamiliarFaces();
      setState(() => _familiarFaces = faces);
    } catch (e) {
      debugPrint('Error loading familiar faces: $e');
    }
  }

  /// Send current camera frame to backend for analysis.
  Future<void> _analyzeFrame() async {
    if (_isAnalyzing || !_cameraInitialized) return;

    setState(() => _isAnalyzing = true);

    try {
      // Capture the image from the camera
      final image = await _controller.takePicture();

      // Read the image bytes and encode to base64
      final List<int> imageBytes = await image.readAsBytes();
      final String base64Frame = base64Encode(imageBytes);

      // Send to backend for analysis
      final result = await _apiService.analyzeFrame(
        base64Frame: base64Frame,
        metadata: {'timestamp': DateTime.now().millisecondsSinceEpoch.toDouble()},
      );

      if (!mounted) return;
      setState(() {
        _isAnalyzing = false;
        if (result != null) {
          _lastAlert = AlertResult.fromJson(result);
        }
      });
    } catch (e) {
      debugPrint('Error analyzing frame: $e');
      setState(() => _isAnalyzing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_cameraInitialized) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      body: Stack(
        children: [
          // Camera preview
          CameraPreview(_controller),

          // Analysis overlay
          Positioned(
            top: 20,
            left: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  _buildStatusIndicator(),
                  if (_lastAlert != null) ...[const SizedBox(height: 8), _buildAlertCard(_lastAlert!)],
                  if (_familiarFaces.isNotEmpty) ...[const SizedBox(height: 8), _buildFamiliarFacesList()],
                ],
              ),
            ),
          ),

          // Bottom controls
          Positioned(
            bottom: 40,
            left: 16,
            right: 16,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildControlButton(
                  icon: Icons.refresh,
                  label: 'Refresh',
                  onPressed: () {
                    setState(() {});
                    _loadFamiliarFaces();
                  },
                ),
                _buildControlButton(
                  icon: _isAnalyzing ? Icons.hourglass_empty : Icons.visibility,
                  label: _isAnalyzing ? 'Analyzing...' : 'Analyze',
                  onPressed: _analyzeFrame,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusIndicator() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(color: _isAnalyzing ? Colors.orange : Colors.green, shape: BoxShape.circle),
        ),
        const SizedBox(width: 8),
        Text(_isAnalyzing ? 'Analyzing...' : 'Ready', style: const TextStyle(color: Colors.white, fontSize: 16)),
      ],
    );
  }

  Widget _buildAlertCard(AlertResult alert) {
    final isThreat = alert.status == 'threat';
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isThreat ? Colors.red.withValues(alpha: 0.3) : Colors.green.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isThreat ? Colors.red : Colors.green),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(isThreat ? Icons.warning : Icons.check_circle, color: isThreat ? Colors.red : Colors.green),
              const SizedBox(width: 8),
              Text(
                isThreat ? 'THREAT DETECTED' : 'SAFE',
                style: TextStyle(color: isThreat ? Colors.red : Colors.green, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(alert.message ?? '', style: const TextStyle(color: Colors.white)),
        ],
      ),
    );
  }

  Widget _buildFamiliarFacesList() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(color: Colors.black.withValues(alpha: 0.5), borderRadius: BorderRadius.circular(8)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: _familiarFaces.map((face) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Text(
              '${face['name'] ?? 'Unknown'} - ${face['description'] ?? ''}',
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildControlButton({required IconData icon, required String label, required VoidCallback onPressed}) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.black.withValues(alpha: 0.7),
        foregroundColor: Colors.white,
      ),
      child: Column(
        children: [
          Icon(icon),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 12)),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

/// Alert result model for analysis responses.
class AlertResult {
  final String status; // 'threat' or 'safe'
  final double? confidence;
  final String? message;
  final List<String>? detectedObjects;

  AlertResult({required this.status, this.confidence, this.message, this.detectedObjects});

  factory AlertResult.fromJson(Map<String, dynamic> json) {
    return AlertResult(
      status: json['status'] as String? ?? 'unknown',
      confidence: (json['confidence'] as num?)?.toDouble(),
      message: json['message'] as String?,
      detectedObjects: (json['detected_objects'] as List<dynamic>?)?.cast<String>(),
    );
  }
}
