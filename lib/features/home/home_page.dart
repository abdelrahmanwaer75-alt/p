import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Vidora')), body: ListView(padding: const EdgeInsets.all(24), children: [Text('Good evening', style: Theme.of(context).textTheme.headlineMedium), const SizedBox(height: 8), const Text('Everything you need to manage your authorized media.'), const SizedBox(height: 28), FilledButton.icon(onPressed: () => context.go('/analyze'), icon: const Icon(Icons.search_rounded), label: const Text('Analyze a link'))]));
}
