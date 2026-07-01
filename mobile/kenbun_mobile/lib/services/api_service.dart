import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

/// Backend API service for Kenbunshoku mobile app.
class ApiService {
  final String baseUrl;

  /// Initialize with backend base URL (e.g., "http://192.168.1.100:8000").
  /// Auto-detects if a port is specified; defaults to 8000 if not.
  ApiService({String? baseUrl}) : baseUrl = _resolveBaseUrl(baseUrl);

  static String _resolveBaseUrl(String? baseUrl) {
    if (baseUrl != null && baseUrl.isNotEmpty) return baseUrl;

    // Detect platform-specific default: localhost for web/Windows,
    // device IP for physical devices
    return 'http://10.0.2.2:8000'; // Android emulator localhost alias
  }

  /// Analyze a single frame sent from the camera.
  /// Returns decoded JSON response or null on failure.
  Future<Map<String, dynamic>?> analyzeFrame({
    required String base64Frame,
    double? timestamp,
    Map<String, dynamic>? metadata,
  }) async {
    final url = Uri.parse('$baseUrl/analyze_frame');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'frame': base64Frame, 'metadata': metadata ?? {}}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }

      // Log non-200 status for debugging
      debugPrint('[ApiService] POST /analyze_frame → ${response.statusCode}');
      return null;
    } catch (e) {
      debugPrint('[ApiService] Error analyzing frame: $e');
      return null;
    }
  }

  /// Register a familiar face by name and description.
  Future<bool> registerFamiliarFace({required String name, required String description}) async {
    final url = Uri.parse('$baseUrl/register_face');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'name': name, 'description': description}),
      );

      return response.statusCode == 200;
    } catch (e) {
      debugPrint('[ApiService] Error registering familiar face: $e');
      return false;
    }
  }

  /// Fetch list of registered familiar faces.
  Future<List<Map<String, dynamic>>> getFamiliarFaces() async {
    final url = Uri.parse('$baseUrl/familiar_faces');

    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final faces = data['faces'] as List<dynamic>? ?? [];
        return faces.cast<Map<String, dynamic>>();
      }

      return [];
    } catch (e) {
      debugPrint('[ApiService] Error fetching familiar faces: $e');
      return [];
    }
  }

  /// Remove a registered familiar face by name.
  Future<bool> removeFamiliarFace(String name) async {
    final url = Uri.parse('$baseUrl/familiar_faces/$name');

    try {
      final response = await http.delete(url);
      return response.statusCode == 200;
    } catch (e) {
      debugPrint('[ApiService] Error removing familiar face: $e');
      return false;
    }
  }
}
