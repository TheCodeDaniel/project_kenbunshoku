import 'package:flutter/material.dart';
import 'package:kenbun_mobile/pages/camera_page.dart';

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kenbunshoku',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      darkTheme: ThemeData(brightness: Brightness.dark, colorSchemeSeed: Colors.redAccent, useMaterial3: true),
      home: const CameraPage(),
    );
  }
}
