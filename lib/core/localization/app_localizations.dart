import 'package:flutter/material.dart';

class AppLocalizations {
  const AppLocalizations(this.locale);

  final Locale locale;

  static const delegate = _AppLocalizationsDelegate();

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations) ??
        const AppLocalizations(Locale('en'));
  }

  bool get isArabic => locale.languageCode == 'ar';

  String get appTitle => isArabic ? 'فيدورا' : 'Vidora';
  String get home => isArabic ? 'الرئيسية' : 'Home';
  String get downloads => isArabic ? 'التنزيلات' : 'Downloads';
  String get library => isArabic ? 'المكتبة' : 'Library';
  String get favorites => isArabic ? 'المفضلة' : 'Favorites';
  String get settings => isArabic ? 'الإعدادات' : 'Settings';
  String get analyze => isArabic ? 'تحليل رابط' : 'Analyze a link';
  String get playlists => isArabic ? 'قوائم التشغيل' : 'Playlists';
  String get goodEvening => isArabic ? 'مساء الخير' : 'Good evening';
  String get homeDescription => isArabic
      ? 'كل ما تحتاجه لإدارة الوسائط المصرح لك بها.'
      : 'Everything you need to manage your authorized media.';
  String get appearance => isArabic ? 'المظهر' : 'Appearance';
  String get theme => isArabic ? 'السمة' : 'Theme';
  String get language => isArabic ? 'اللغة' : 'Language';
  String get system => isArabic ? 'النظام' : 'System';
  String get light => isArabic ? 'فاتح' : 'Light';
  String get dark => isArabic ? 'داكن' : 'Dark';
  String get english => 'English';
  String get arabic => 'العربية';
  String get signOut => isArabic ? 'تسجيل الخروج' : 'Sign out';
  String get files => isArabic ? 'الملفات' : 'Files';
  String get searchFiles => isArabic ? 'البحث في الملفات' : 'Search files';
  String get noFiles => isArabic ? 'لا توجد ملفات' : 'No files';
  String get unableToLoad => isArabic ? 'تعذر التحميل' : 'Unable to load';
  String get active => isArabic ? 'نشط' : 'Active';
  String get queued => isArabic ? 'في الانتظار' : 'Queued';
  String get completed => isArabic ? 'مكتمل' : 'Completed';
  String get failed => isArabic ? 'فشل' : 'Failed';
  String get cancelled => isArabic ? 'ملغى' : 'Cancelled';
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) =>
      const {'en', 'ar'}.contains(locale.languageCode);

  @override
  Future<AppLocalizations> load(Locale locale) async =>
      AppLocalizations(locale);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}
