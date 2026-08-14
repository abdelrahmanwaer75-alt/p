import 'package:flutter/material.dart';

import '../../../core/models/models.dart';

class FileTile extends StatelessWidget {
  const FileTile({super.key, required this.file});
  final ManagedFile file;

  @override
  Widget build(BuildContext context) => ListTile(
    leading: Icon(file.mediaType == 'audio' ? Icons.audiotrack : Icons.movie),
    title: Text(file.filename),
    subtitle: Text('${file.extension} • ${file.size} bytes'),
    trailing: Icon(file.isFavorite ? Icons.star : Icons.star_border),
  );
}
