package com.vidora.vidora

import android.content.Intent
import android.os.Bundle
import androidx.annotation.NonNull
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val methodChannelName = "vidora/background_downloads"
    private val eventChannelName = "vidora/background_download_events"

    override fun configureFlutterEngine(@NonNull flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, methodChannelName).setMethodCallHandler { call: MethodCall, result: MethodChannel.Result ->
            val taskId = call.argument<String>("task_id")
            when (call.method) {
                "start" -> result.success(BackgroundDownloadBridge.start(call.arguments as? Map<*, *> ?: emptyMap<String, Any>()))
                "pause" -> result.success(taskId?.let { BackgroundDownloadBridge.pause(it) } ?: false)
                "resume" -> result.success(taskId?.let { BackgroundDownloadBridge.resume(it) } ?: false)
                "cancel" -> result.success(taskId?.let { BackgroundDownloadBridge.cancel(it) } ?: false)
                else -> result.notImplemented()
            }
        }
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, eventChannelName).setStreamHandler(object : EventChannel.StreamHandler {
            override fun onListen(arguments: Any?, events: EventChannel.EventSink?) { BackgroundDownloadBridge.attach(this@MainActivity, events) }
            override fun onCancel(arguments: Any?) { BackgroundDownloadBridge.detach() }
        })
        handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); setIntent(intent); handleIntent(intent) }
    private fun handleIntent(intent: Intent?) {
        val taskId = intent?.getStringExtra("vidora_task_id") ?: return
        BackgroundDownloadBridge.emit(taskId, "notification_tap", mapOf("open" to true))
    }
}
