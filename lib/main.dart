import 'package:flutter/material.dart';

import 'core_api.dart';
import 'library_page.dart';
import 'downloads_page.dart';

void main() => runApp(const VidoraApp());

enum AppLanguage { english, arabic }

enum ThemeChoice { system, light, dark }

class AppCopy {
  final AppLanguage language;
  const AppCopy(this.language);
  bool get ar => language == AppLanguage.arabic;
  String get appName => 'Vidora';
  String get tagline =>
      ar ? 'نزّل. رتّب. استمتع.' : 'Download. Organize. Enjoy.';
  String get home => ar ? 'الرئيسية' : 'Home';
  String get downloads => ar ? 'التنزيلات' : 'Downloads';
  String get files => ar ? 'الملفات' : 'Files';
  String get favorites => ar ? 'المفضلة' : 'Favorites';
  String get settings => ar ? 'الإعدادات' : 'Settings';
  String get account => ar ? 'الحساب' : 'Account';
  String get signIn => ar ? 'تسجيل الدخول' : 'Sign in';
  String get email => ar ? 'البريد الإلكتروني' : 'Email';
  String get password => ar ? 'كلمة المرور' : 'Password';
  String get welcomeBody => ar
      ? 'مساحتك الآمنة لإدارة الوسائط المصرّح بتنزيلها والاستمتاع بها.'
      : 'Your trusted space for managing authorized media and enjoying it offline.';
  String get getStarted => ar ? 'ابدأ الآن' : 'Get started';
  String get skip => ar ? 'تخطي' : 'Skip';
  String get greeting => ar ? 'مساء الخير' : 'Good evening';
  String get homeBody => ar
      ? 'كل ما تحتاجه لإدارة مكتبة الوسائط الخاصة بك.'
      : 'Everything you need to manage your media library.';
  String get analyzeUrl => ar ? 'تحليل رابط' : 'Analyze a link';
  String get pasteUrl =>
      ar ? 'ألصق رابطًا للبدء' : 'Paste a link to get started';
  String get recent => ar ? 'النشاط الأخير' : 'Recent activity';
  String get seeAll => ar ? 'عرض الكل' : 'See all';
  String get emptyDownloads => ar ? 'لا توجد تنزيلات بعد' : 'No downloads yet';
  String get emptyDownloadsBody => ar
      ? 'ستظهر التنزيلات المصرّح بها هنا.'
      : 'Authorized downloads will appear here.';
  String get emptyFiles => ar ? 'مكتبتك فارغة' : 'Your library is empty';
  String get emptyFilesBody => ar
      ? 'ابدأ بتحليل رابط أو أضف ملفات من جهازك.'
      : 'Analyze a link or add files from your device.';
  String get emptyFavorites => ar ? 'لا توجد مفضلات' : 'No favorites yet';
  String get emptyFavoritesBody => ar
      ? 'احفظ الوسائط المفضلة لديك للوصول السريع.'
      : 'Save your favorite media for quick access.';
  String get appearance => ar ? 'المظهر' : 'Appearance';
  String get languageLabel => ar ? 'اللغة' : 'Language';
  String get theme => ar ? 'السمة' : 'Theme';
  String get system => ar ? 'النظام' : 'System';
  String get light => ar ? 'فاتح' : 'Light';
  String get dark => ar ? 'داكن' : 'Dark';
  String get english => 'English';
  String get arabic => 'العربية';
  String get comingSoon => ar ? 'قريبًا' : 'Coming soon';
  String get authorizedOnly =>
      ar ? 'للمحتوى المصرّح به فقط' : 'Authorized content only';
}

class VidoraApp extends StatefulWidget {
  const VidoraApp({super.key});
  @override
  State<VidoraApp> createState() => _VidoraAppState();
}

class _VidoraAppState extends State<VidoraApp> {
  AppLanguage language = AppLanguage.english;
  ThemeChoice theme = ThemeChoice.system;
  bool onboarded = false;
  AppCopy get copy => AppCopy(language);
  void setLanguage(AppLanguage value) => setState(() => language = value);
  void setTheme(ThemeChoice value) => setState(() => theme = value);

  @override
  Widget build(BuildContext context) {
    final brightness = MediaQuery.platformBrightnessOf(context);
    final dark =
        theme == ThemeChoice.dark ||
        (theme == ThemeChoice.system && brightness == Brightness.dark);
    const seed = Color(0xFF6750A4);
    final scheme = ColorScheme.fromSeed(
      seedColor: seed,
      brightness: dark ? Brightness.dark : Brightness.light,
    );
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: copy.appName,
      themeMode: theme == ThemeChoice.system
          ? ThemeMode.system
          : (theme == ThemeChoice.dark ? ThemeMode.dark : ThemeMode.light),
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: seed),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      darkTheme: ThemeData(
        colorScheme: scheme,
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      locale: Locale(language == AppLanguage.arabic ? 'ar' : 'en'),
      builder: (context, child) => Directionality(
        textDirection: language == AppLanguage.arabic
            ? TextDirection.rtl
            : TextDirection.ltr,
        child: child!,
      ),
      home: onboarded
          ? Shell(
              copy: copy,
              api: VidoraApiClient(),
              language: language,
              theme: theme,
              onLanguage: setLanguage,
              onTheme: setTheme,
            )
          : Onboarding(
              copy: copy,
              onContinue: () => setState(() => onboarded = true),
            ),
    );
  }
}

class Onboarding extends StatelessWidget {
  final AppCopy copy;
  final VoidCallback onContinue;
  const Onboarding({super.key, required this.copy, required this.onContinue});
  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Spacer(),
            Container(
              width: 82,
              height: 82,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(26),
              ),
              child: Icon(
                Icons.play_circle_fill_rounded,
                size: 48,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            const SizedBox(height: 28),
            Text(
              copy.appName,
              style: Theme.of(context).textTheme.displaySmall
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 10),
            Text(
              copy.tagline,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: Theme.of(context).colorScheme.primary,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 18),
            Text(
              copy.welcomeBody,
              style: Theme.of(context).textTheme.bodyLarge
                  ?.copyWith(height: 1.5),
            ),
            const Spacer(),
            Text(
              copy.authorizedOnly,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: onContinue,
                icon: const Icon(Icons.arrow_forward_rounded),
                label: Text(copy.getStarted),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

class Shell extends StatefulWidget {
  final AppCopy copy;
  final VidoraApiClient api;
  final AppLanguage language;
  final ThemeChoice theme;
  final ValueChanged<AppLanguage> onLanguage;
  final ValueChanged<ThemeChoice> onTheme;
  const Shell({
    super.key,
    required this.copy,
    required this.api,
    required this.language,
    required this.theme,
    required this.onLanguage,
    required this.onTheme,
  });
  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int index = 0;
  @override
  Widget build(BuildContext context) {
    final pages = [
      HomePage(copy: widget.copy, api: widget.api),
      DownloadsPage(
        api: widget.api,
        title: widget.copy.downloads,
        emptyTitle: widget.copy.emptyDownloads,
        emptyBody: widget.copy.emptyDownloadsBody,
      ),
      LibraryPage(
        api: widget.api,
        mode: 'library',
        icon: Icons.folder_rounded,
        title: widget.copy.files,
        emptyBody: widget.copy.emptyFilesBody,
      ),
      LibraryPage(
        api: widget.api,
        mode: 'favorites',
        icon: Icons.favorite_rounded,
        title: widget.copy.favorites,
        emptyBody: widget.copy.emptyFavoritesBody,
      ),
      SettingsPage(
        copy: widget.copy,
        api: widget.api,
        language: widget.language,
        theme: widget.theme,
        onLanguage: widget.onLanguage,
        onTheme: widget.onTheme,
      ),
    ];
    final labels = [
      widget.copy.home,
      widget.copy.downloads,
      widget.copy.files,
      widget.copy.favorites,
      widget.copy.settings,
    ];
    final icons = [
      Icons.home_rounded,
      Icons.download_rounded,
      Icons.folder_rounded,
      Icons.favorite_rounded,
      Icons.settings_rounded,
    ];
    return Scaffold(
      body: IndexedStack(index: index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (v) => setState(() => index = v),
        destinations: [
          for (var i = 0; i < labels.length; i++)
            NavigationDestination(icon: Icon(icons[i]), label: labels[i]),
        ],
      ),
    );
  }
}

class HomePage extends StatelessWidget {
  final AppCopy copy;
  final VidoraApiClient api;
  const HomePage({super.key, required this.copy, required this.api});

  Future<void> _analyze(BuildContext context) async {
    final controller = TextEditingController();
    var loading = false;
    String? result;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(copy.analyzeUrl),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: controller,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(
                  hintText: 'https://example.com/video',
                ),
              ),
              if (result != null)
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: Text(result!),
                ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: Text(copy.skip),
            ),
            FilledButton(
              onPressed: loading
                  ? null
                  : () async {
                      if (controller.text.trim().isEmpty) return;
                      setDialogState(() {
                        loading = true;
                        result = null;
                      });
                      try {
                        final preview = await api.previewUrl(
                          controller.text.trim(),
                        );
                        setDialogState(() {
                          loading = false;
                          result = '${preview.platform}: ${preview.message}';
                        });
                      } catch (_) {
                        setDialogState(() {
                          loading = false;
                          result = copy.authorizedOnly;
                        });
                      }
                    },
              child: loading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(copy.analyzeUrl),
            ),
          ],
        ),
      ),
    );
    controller.dispose();
  }

  @override
  Widget build(BuildContext context) => CustomScrollView(
    slivers: [
      SliverAppBar(
        pinned: true,
        title: Text(copy.appName),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.notifications_none_rounded),
          ),
        ],
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        sliver: SliverList(
          delegate: SliverChildListDelegate([
            Text(
              copy.greeting,
              style: Theme.of(context).textTheme.headlineMedium
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            Text(
              copy.homeBody,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            Card(
              color: Theme.of(context).colorScheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.link_rounded,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      copy.analyzeUrl,
                      style: Theme.of(context).textTheme.titleLarge
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 6),
                    Text(copy.authorizedOnly),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: () => _analyze(context),
                      child: Text(copy.pasteUrl),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 28),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  copy.recent,
                  style: Theme.of(context).textTheme.titleLarge
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                TextButton(onPressed: () {}, child: Text(copy.seeAll)),
              ],
            ),
            const SizedBox(height: 10),
            EmptyCard(
              icon: Icons.auto_awesome_rounded,
              title: copy.emptyDownloads,
              body: copy.emptyDownloadsBody,
            ),
          ]),
        ),
      ),
    ],
  );
}

class EmptyPage extends StatelessWidget {
  final IconData icon;
  final String title, body;
  const EmptyPage({
    super.key,
    required this.icon,
    required this.title,
    required this.body,
  });
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: EmptyCard(icon: icon, title: title, body: body),
      ),
    ),
  );
}

class EmptyCard extends StatelessWidget {
  final IconData icon;
  final String title, body;
  const EmptyCard({
    super.key,
    required this.icon,
    required this.title,
    required this.body,
  });
  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 72,
        height: 72,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          size: 34,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
      const SizedBox(height: 16),
      Text(
        title,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.titleMedium
            ?.copyWith(fontWeight: FontWeight.bold),
      ),
      const SizedBox(height: 6),
      Text(
        body,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodyMedium
            ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
      ),
    ],
  );
}

class SettingsPage extends StatelessWidget {
  final AppCopy copy;
  final VidoraApiClient api;
  final AppLanguage language;
  final ThemeChoice theme;
  final ValueChanged<AppLanguage> onLanguage;
  final ValueChanged<ThemeChoice> onTheme;
  const SettingsPage({
    super.key,
    required this.copy,
    required this.api,
    required this.language,
    required this.theme,
    required this.onLanguage,
    required this.onTheme,
  });
  Future<void> _signIn(BuildContext context) async {
    final email = TextEditingController();
    final password = TextEditingController();
    var loading = false;
    String? error;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(copy.signIn),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: email,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(labelText: copy.email),
              ),
              TextField(
                controller: password,
                obscureText: true,
                decoration: InputDecoration(labelText: copy.password),
              ),
              if (error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(error!),
                ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: Text(copy.skip),
            ),
            FilledButton(
              onPressed: loading
                  ? null
                  : () async {
                      setDialogState(() {
                        loading = true;
                        error = null;
                      });
                      try {
                        await api.login(email.text.trim(), password.text);
                        if (dialogContext.mounted) Navigator.pop(dialogContext);
                      } catch (_) {
                        setDialogState(() {
                          loading = false;
                          error = copy.authorizedOnly;
                        });
                      }
                    },
              child: loading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(copy.signIn),
            ),
          ],
        ),
      ),
    );
    email.dispose();
    password.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(copy.settings)),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: ListTile(
            leading: const Icon(Icons.person_rounded),
            title: Text(copy.account),
            subtitle: Text(copy.signIn),
            onTap: () => _signIn(context),
          ),
        ),
        const SizedBox(height: 20),
        Text(
          copy.appearance,
          style: Theme.of(context).textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.brightness_6_rounded),
                title: Text(copy.theme),
                subtitle: Text(_themeName()),
                trailing: DropdownButton<ThemeChoice>(
                  value: theme,
                  underline: const SizedBox(),
                  items: [
                    DropdownMenuItem(
                      value: ThemeChoice.system,
                      child: Text(copy.system),
                    ),
                    DropdownMenuItem(
                      value: ThemeChoice.light,
                      child: Text(copy.light),
                    ),
                    DropdownMenuItem(
                      value: ThemeChoice.dark,
                      child: Text(copy.dark),
                    ),
                  ],
                  onChanged: (v) {
                    if (v != null) onTheme(v);
                  },
                ),
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.language_rounded),
                title: Text(copy.languageLabel),
                subtitle: Text(
                  language == AppLanguage.arabic ? copy.arabic : copy.english,
                ),
                trailing: DropdownButton<AppLanguage>(
                  value: language,
                  underline: const SizedBox(),
                  items: [
                    DropdownMenuItem(
                      value: AppLanguage.english,
                      child: Text(copy.english),
                    ),
                    DropdownMenuItem(
                      value: AppLanguage.arabic,
                      child: Text(copy.arabic),
                    ),
                  ],
                  onChanged: (v) {
                    if (v != null) onLanguage(v);
                  },
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
  String _themeName() => theme == ThemeChoice.system
      ? copy.system
      : (theme == ThemeChoice.light ? copy.light : copy.dark);
}
