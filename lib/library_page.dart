import 'package:flutter/material.dart';

import 'core_api.dart';

class LibraryPage extends StatefulWidget {
  final VidoraApiClient api;
  final String title;
  final String emptyBody;
  final IconData icon;
  final String mode;
  const LibraryPage({
    super.key,
    required this.api,
    required this.title,
    required this.emptyBody,
    required this.icon,
    required this.mode,
  });

  @override
  State<LibraryPage> createState() => _LibraryPageState();
}

class _LibraryPageState extends State<LibraryPage> {
  late Future<List<LibraryItem>> future;

  @override
  void initState() {
    super.initState();
    future = _load();
  }

  Future<List<LibraryItem>> _load() {
    if (widget.mode == 'favorites') return widget.api.favorites();
    if (widget.mode == 'history') return widget.api.history();
    return widget.api.library();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.title)),
    body: FutureBuilder<List<LibraryItem>>(
      future: future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text(widget.emptyBody));
        }
        final items = snapshot.data ?? const <LibraryItem>[];
        if (items.isEmpty) {
          return Center(
            child: _EmptyCard(
              icon: widget.icon,
              title: widget.title,
              body: widget.emptyBody,
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async {
            setState(() {
              future = _load();
            });
            await future;
          },
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (context, index) => Card(
              child: ListTile(
                leading: Icon(widget.icon),
                title: Text(items[index].title),
                subtitle: Text(items[index].mediaType),
                trailing: items[index].isFavorite
                    ? const Icon(Icons.favorite_rounded)
                    : null,
              ),
            ),
          ),
        );
      },
    ),
  );
}

class _EmptyCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  const _EmptyCard({
    required this.icon,
    required this.title,
    required this.body,
  });
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(32),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 48),
        const SizedBox(height: 16),
        Text(title, textAlign: TextAlign.center),
        const SizedBox(height: 8),
        Text(body, textAlign: TextAlign.center),
      ],
    ),
  );
}
