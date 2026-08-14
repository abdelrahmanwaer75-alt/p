import CryptoKit
import Foundation
import UIKit
import UserNotifications

final class BackgroundDownloadService: NSObject, URLSessionDownloadDelegate, UNUserNotificationCenterDelegate {
  static let shared = BackgroundDownloadService()
  private let identifier = "com.vidora.background-downloads"
  private var session: URLSession!
  private var taskIds: [Int: String] = [:]
  private var tasks: [Int: URLSessionDownloadTask] = [:]
  private var resumeData: [String: Data] = [:]
  private var pendingEvents: [[String: Any]] = []
  private var emitter: (([String: Any]) -> Void)?
  var sessionCompletion: (() -> Void)?

  private override init() {
    super.init()
    let configuration = URLSessionConfiguration.background(withIdentifier: identifier)
    configuration.isDiscretionary = false
    configuration.sessionSendsLaunchEvents = true
    configuration.waitsForConnectivity = true
    configuration.allowsCellularAccess = true
    session = URLSession(configuration: configuration, delegate: self, delegateQueue: OperationQueue.main)
    UNUserNotificationCenter.current().delegate = self
    restoreExistingTasks()
  }

  func setEmitter(_ handler: (([String: Any]) -> Void)?) {
    emitter = handler
    guard let handler else { return }
    let queued = pendingEvents
    pendingEvents.removeAll()
    queued.forEach(handler)
  }

  func start(taskId: String, url: String, filename: String) -> Bool {
    guard let remoteURL = URL(string: url), ["http", "https"].contains(remoteURL.scheme?.lowercased()) else { return false }
    let task = session.downloadTask(with: URLRequest(url: remoteURL))
    taskIds[task.taskIdentifier] = taskId
    tasks[task.taskIdentifier] = task
    task.taskDescription = "\(taskId)|\(safeFilename(filename))"
    task.resume()
    emitEvent(taskId: taskId, event: "created", fields: [:])
    notify(taskId: taskId, event: "started", progress: nil)
    return true
  }

  func cancel(taskId: String) -> Bool {
    guard let task = findTask(taskId) else { return false }
    task.cancel()
    emitEvent(taskId: taskId, event: "cancelled", fields: [:])
    notify(taskId: taskId, event: "cancelled", progress: nil)
    return true
  }

  func pause(taskId: String) -> Bool {
    guard let task = findTask(taskId) else { return false }
    task.cancel(byProducingResumeData: { data in
      if let data { self.resumeData[taskId] = data }
    })
    emitEvent(taskId: taskId, event: "paused", fields: [:])
    notify(taskId: taskId, event: "paused", progress: nil)
    return true
  }

  func resume(taskId: String) -> Bool {
    guard let data = resumeData.removeValue(forKey: taskId) else { return false }
    let task = session.downloadTask(withResumeData: data)
    taskIds[task.taskIdentifier] = taskId
    tasks[task.taskIdentifier] = task
    task.resume()
    emitEvent(taskId: taskId, event: "started", fields: [:])
    notify(taskId: taskId, event: "started", progress: nil)
    return true
  }

  func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didWriteData bytesWritten: Int64, totalBytesWritten: Int64, totalBytesExpectedToWrite: Int64) {
    guard let taskId = taskIds[downloadTask.taskIdentifier] else { return }
    let progress = totalBytesExpectedToWrite > 0 ? Int(Double(totalBytesWritten) / Double(totalBytesExpectedToWrite) * 100) : 0
    emitEvent(taskId: taskId, event: "progress", fields: ["progress": progress, "bytes_downloaded": totalBytesWritten, "total_bytes": totalBytesExpectedToWrite])
    notify(taskId: taskId, event: "progress", progress: progress)
  }

  func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didFinishDownloadingTo location: URL) {
    guard let taskId = taskIds[downloadTask.taskIdentifier] else { return }
    let filename = safeFilename(downloadTask.taskDescription?.split(separator: "|", maxSplits: 1).last.map(String.init) ?? "\(taskId).bin")
    let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("Vidora", isDirectory: true)
    do {
      try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
      let destination = directory.appendingPathComponent(filename)
      try? FileManager.default.removeItem(at: destination)
      try FileManager.default.moveItem(at: location, to: destination)
      let attributes = try FileManager.default.attributesOfItem(atPath: destination.path)
      let size = (attributes[.size] as? NSNumber)?.int64Value ?? 0
      let checksum = try sha256(of: destination)
      emitEvent(taskId: taskId, event: "completed", fields: ["output_path": destination.path, "bytes_downloaded": size, "sha256": checksum])
      notify(taskId: taskId, event: "completed", progress: 100)
    } catch {
      emitEvent(taskId: taskId, event: "failed", fields: ["error_code": "FILE_MOVE_FAILED"])
      notify(taskId: taskId, event: "failed", progress: nil)
    }
    cleanup(downloadTask.taskIdentifier)
  }

  func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
    guard let taskId = taskIds[task.taskIdentifier], error != nil else { return }
    emitEvent(taskId: taskId, event: "failed", fields: ["error_code": "NETWORK_ERROR"])
    notify(taskId: taskId, event: "failed", progress: nil)
    cleanup(task.taskIdentifier)
  }

  func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
    DispatchQueue.main.async {
      self.sessionCompletion?()
      self.sessionCompletion = nil
    }
  }

  func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping () -> Void) {
    if let taskId = response.notification.request.content.userInfo["task_id"] as? String {
      emitEvent(taskId: taskId, event: "notification_tap", fields: ["open": true])
    }
    completionHandler()
  }

  private func restoreExistingTasks() {
    session.getAllTasks { allTasks in
      allTasks.compactMap { $0 as? URLSessionDownloadTask }.forEach { task in
        guard let description = task.taskDescription,
              let separator = description.firstIndex(of: "|") else { return }
        let taskId = String(description[..<separator])
        self.taskIds[task.taskIdentifier] = taskId
        self.tasks[task.taskIdentifier] = task
      }
    }
  }

  private func findTask(_ taskId: String) -> URLSessionDownloadTask? {
    tasks.first(where: { $0.value == taskId })?.value
  }

  private func cleanup(_ identifier: Int) {
    taskIds.removeValue(forKey: identifier)
    tasks.removeValue(forKey: identifier)
  }

  private func safeFilename(_ value: String) -> String {
    let name = value.split(separator: "/").last.map(String.init) ?? "download.bin"
    let sanitized = name.replacingOccurrences(of: "[^A-Za-z0-9._ -]", with: "_", options: .regularExpression)
    return sanitized.isEmpty ? "download.bin" : sanitized
  }

  private func sha256(of url: URL) throws -> String {
    let file = try FileHandle(forReadingFrom: url)
    defer { try? file.close() }
    var hasher = SHA256()
    while let data = try file.read(upToCount: 1024 * 1024), !data.isEmpty {
      hasher.update(data: data)
    }
    return hasher.finalize().map { String(format: "%02x", $0) }.joined()
  }

  private func emitEvent(taskId: String, event: String, fields: [String: Any]) {
    var value = fields
    value["task_id"] = taskId
    value["event"] = event.hasPrefix("download.") ? event : "download.\(event)"
    if let emitter {
      emitter(value)
    } else {
      if pendingEvents.count >= 100 { pendingEvents.removeFirst() }
      pendingEvents.append(value)
    }
  }

  private func notify(taskId: String, event: String, progress: Int?) {
    let content = UNMutableNotificationContent()
    content.title = "Vidora download"
    content.body = progress == nil ? event.capitalized : "\(progress!)%"
    content.sound = .default
    content.userInfo = ["task_id": taskId]
    UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: "vidora-\(taskId)", content: content, trigger: nil))
  }
}
