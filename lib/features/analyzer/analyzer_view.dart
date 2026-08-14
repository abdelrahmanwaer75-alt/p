import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../analyzer/analyzer_controller.dart';
import '../downloads/downloads_controller.dart';
import '../../core/localization/app_localizations.dart';
import '../../shared/state/resource_state.dart';

class AnalyzerPage extends ConsumerStatefulWidget {
  const AnalyzerPage({super.key});
  @override
  ConsumerState<AnalyzerPage> createState() => _AnalyzerPageState();
}

class _AnalyzerPageState extends ConsumerState<AnalyzerPage> {
  final controller = TextEditingController();
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final strings = AppLocalizations.of(context);
    final state = ref.watch(analyzerProvider);
    return Scaffold(
      appBar: AppBar(title: Text(strings.analyzeTitle)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          TextField(
            controller: controller,
            keyboardType: TextInputType.url,
            decoration: InputDecoration(
              labelText: strings.mediaUrl,
              hintText: 'https://vimeo.com/...',
            ),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: state.status == ResourceStatus.loading
                ? null
                : () => ref
                      .read(analyzerProvider.notifier)
                      .analyze(controller.text.trim()),
            child: state.status == ResourceStatus.loading
                ? const CircularProgressIndicator()
                : Text(strings.analyzeAction),
          ),
          const SizedBox(height: 24),
          _body(state, strings),
        ],
      ),
    );
  }

  Widget _body(ResourceState state, AppLocalizations strings) {
    if (state.status == ResourceStatus.loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.status == ResourceStatus.error ||
        state.status == ResourceStatus.offline ||
        state.status == ResourceStatus.unauthorized) {
      return Text(state.message ?? strings.unableToAnalyze);
    }
    if (state.status == ResourceStatus.empty) {
      return Text(state.message ?? strings.noVerifiedFormats);
    }
    final result = state.data;
    if (result == null) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          result.title ?? result.platform,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        Text(result.message),
        const SizedBox(height: 16),
        for (final format in result.formats)
          Card(
            child: ListTile(
              title: Text(format.quality ?? format.extension),
              subtitle: Text(format.kind),
              trailing: FilledButton(
                onPressed: () => _queue(result, format),
                child: Text(strings.downloadAction),
              ),
            ),
          ),
      ],
    );
  }

  Future<void> _queue(dynamic result, dynamic format) async {
    final task = await ref
        .read(downloadsProvider.notifier)
        .queue(result, format, authorized: true);
    if (mounted && task != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).downloadQueued)),
      );
    }
  }
}
