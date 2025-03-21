import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:io';
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Reconhecimento Facial',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const FaceRecognitionScreen(),
    );
  }
}

class FaceRecognitionScreen extends StatefulWidget {
  const FaceRecognitionScreen({super.key});

  @override
  State<FaceRecognitionScreen> createState() => _FaceRecognitionScreenState();
}

class _FaceRecognitionScreenState extends State<FaceRecognitionScreen> {
  late CameraController _controller;
  late WebSocketChannel channel;
  List<dynamic> _results = [];
  bool _isConnected = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _connectWebSocket();
  }

  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) return;

    _controller = CameraController(
      cameras[0],
      ResolutionPreset.medium,
      enableAudio: false,
    );

    await _controller.initialize();
    if (mounted) {
      setState(() {});
      _startImageStream();
    }
  }

  void _connectWebSocket() {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/face-recognition'),
    );

    channel.stream.listen(
      (message) {
        final data = jsonDecode(message);
        setState(() {
          _results = data['frame_results'] ?? [];
          _isConnected = true;
        });
      },
      onError: (error) {
        print('Erro WebSocket: $error');
        setState(() => _isConnected = false);
      },
      onDone: () {
        setState(() => _isConnected = false);
      },
    );
  }

  void _startImageStream() {
    _controller.startImageStream((CameraImage image) async {
      if (!_isConnected) return;

      final tempDir = await getTemporaryDirectory();
      final tempPath = '${tempDir.path}/temp_image.jpg';

      // Converte a imagem da câmera para JPEG
      final img.Image? imgImage = img.Image.fromBytes(
        width: image.width,
        height: image.height,
        bytes: image.planes[0].bytes.buffer.asUint8List(),
        numChannels: 1,
      );

      if (imgImage != null) {
        final jpeg = img.encodeJpg(imgImage, quality: 70);
        File(tempPath).writeAsBytesSync(jpeg);

        // Envia a imagem para o servidor
        channel.sink.add(jpeg);
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    channel.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_controller.value.isInitialized) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Reconhecimento Facial'),
        actions: [
          IconButton(
            icon: Icon(_isConnected ? Icons.wifi : Icons.wifi_off),
            onPressed: () {
              if (!_isConnected) {
                _connectWebSocket();
              }
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: CameraPreview(_controller),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.black87,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Status: ${_isConnected ? "Conectado" : "Desconectado"}',
                  style: TextStyle(
                    color: _isConnected ? Colors.green : Colors.red,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Faces encontradas: ${_results.length}',
                  style: const TextStyle(color: Colors.white),
                ),
                const SizedBox(height: 8),
                ..._results.map((result) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Text(
                    '${result['name']} - ${result['status'] == 'match' ? 'Correspondência encontrada' : 'Sem correspondência'}',
                    style: TextStyle(
                      color: result['status'] == 'match' ? Colors.green : Colors.red,
                    ),
                  ),
                )),
              ],
            ),
          ),
        ],
      ),
    );
  }
} 