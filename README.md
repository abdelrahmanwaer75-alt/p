# Vidora

**Download. Organize. Enjoy.**

Vidora is a Flutter foundation for an authorized media management application. This local Phase 1 implementation establishes the product shell without pretending that download or extraction functionality is complete.

## Phase 1 delivered

The application includes a Material 3 design system, light/dark/system themes, English and Arabic copy, runtime RTL/LTR direction switching, onboarding, a five-destination bottom navigation shell, home dashboard, empty states, settings controls, and reusable empty-state cards. The analyzer action is intentionally presented as a coming-soon surface; no downloader, extractor, DRM bypass, or fake API response has been added.

## Run locally

```bash
cd /home/ubuntu/vidora
/home/ubuntu/tools/flutter/bin/flutter run -d linux
```

For Android or iOS development, use a host with the corresponding SDKs and devices configured:

```bash
flutter run -d <device-id>
```

## Verification

The following checks pass in the local environment:

```bash
flutter analyze
flutter test
CC=clang CXX=clang++ flutter build linux --debug
```

The Linux debug binary is generated at `build/linux/x64/debug/bundle/vidora`. Android and iOS compilation were not claimed because this environment does not include the Android SDK/emulator or macOS/Xcode toolchain.

## Project structure

The current foundation is intentionally small and easy to extend. The primary UI entry point is `lib/main.dart`, while `test/widget_test.dart` contains the onboarding and navigation smoke test. Future phases should split the application into the architecture described by the master specification, beginning with domain models and API contracts before implementing analyzer and download services.

## Legal boundary

Vidora must only process media that the user is authorized to download and that the source platform permits downloading. DRM circumvention, paywall bypass, authentication bypass, CAPTCHA bypass, anti-bot bypass, private-content extraction without authorization, and arbitrary shell execution are outside the product and must remain excluded.
