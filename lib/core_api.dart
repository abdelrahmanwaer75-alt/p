import 'package:dio/dio.dart';

class AnalyzerPreview {
  final String platform;
  final String message;
  final bool supported;
  final String contentKind;

  const AnalyzerPreview({
    required this.platform,
    required this.message,
    required this.supported,
    required this.contentKind,
  });

  factory AnalyzerPreview.fromJson(Map<String, dynamic> json) =>
      AnalyzerPreview(
        platform: json['platform'] as String? ?? 'generic',
        message: json['message'] as String? ?? '',
        supported: json['supported'] as bool? ?? false,
        contentKind: json['content_kind'] as String? ?? 'unknown',
      );
}

class VidoraApiClient {
  final Dio _dio;
  VidoraApiClient({String? baseUrl})
    : _dio = Dio(
        BaseOptions(
          baseUrl:
              baseUrl ??
              const String.fromEnvironment(
                'VIDORA_API_URL',
                defaultValue: 'http://127.0.0.1:8000',
              ),
          connectTimeout: const Duration(seconds: 5),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        ),
      );

  Future<AnalyzerPreview> previewUrl(String url) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/analyzer/preview',
      data: {'url': url},
    );
    return AnalyzerPreview.fromJson(response.data ?? const {});
  }
}
