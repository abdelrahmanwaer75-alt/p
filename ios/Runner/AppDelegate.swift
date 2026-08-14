import Flutter
import UIKit
import UserNotifications

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  private let methodChannelName = "vidora/background_downloads"
  private let eventChannelName = "vidora/background_download_events"

  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { _, _ in }
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    let messenger = engineBridge.applicationRegistrar.messenger()
    let methods = FlutterMethodChannel(name: methodChannelName, binaryMessenger: messenger)
    methods.setMethodCallHandler { call, result in
      let args = call.arguments as? [String: Any] ?? [:]
      let taskId = args["task_id"] as? String
      switch call.method {
      case "start": result(BackgroundDownloadService.shared.start(taskId: args["task_id"] as? String ?? "", url: args["url"] as? String ?? "", filename: args["filename"] as? String ?? "download.bin"))
      case "pause": result(taskId.map { BackgroundDownloadService.shared.pause(taskId: $0) } ?? false)
      case "resume": result(taskId.map { BackgroundDownloadService.shared.resume(taskId: $0) } ?? false)
      case "cancel": result(taskId.map { BackgroundDownloadService.shared.cancel(taskId: $0) } ?? false)
      default: result(FlutterMethodNotImplemented)
      }
    }
    let events = FlutterEventChannel(name: eventChannelName, binaryMessenger: messenger)
    events.setStreamHandler(IOSDownloadEventHandler())
  }

  override func application(_ application: UIApplication, handleEventsForBackgroundURLSession identifier: String, completionHandler: @escaping () -> Void) {
    BackgroundDownloadService.shared.sessionCompletion = completionHandler
  }
}

private final class IOSDownloadEventHandler: NSObject, FlutterStreamHandler {
  func onListen(withArguments arguments: Any?, eventSink events: @escaping FlutterEventSink) -> FlutterError? {
    BackgroundDownloadService.shared.setEmitter { payload in events(payload) }
    return nil
  }
  func onCancel(withArguments arguments: Any?) -> FlutterError? {
    BackgroundDownloadService.shared.setEmitter(nil)
    return nil
  }
}
