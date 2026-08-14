package com.vidora.vidora

import android.content.Context
import androidx.work.Constraints
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import io.flutter.plugin.common.EventChannel
import java.util.concurrent.TimeUnit

object BackgroundDownloadBridge {
    private var sink: EventChannel.EventSink? = null
    private var context: Context? = null

    fun attach(appContext: Context, eventSink: EventChannel.EventSink?) { context = appContext.applicationContext; sink = eventSink }
    fun detach() { sink = null }
    fun emit(taskId: String, event: String, fields: Map<String, Any?> = emptyMap()) {
        val payload = HashMap<String, Any?>()
        payload["task_id"] = taskId
        payload["event"] = "download.$event"
        payload.putAll(fields)
        sink?.success(payload)
    }

    fun start(arguments: Map<*, *>): Boolean {
        val app = context ?: return false
        val taskId = arguments["task_id"]?.toString() ?: return false
        val url = arguments["url"]?.toString() ?: return false
        val data = Data.Builder().putString("task_id", taskId).putString("url", url).putString("filename", arguments["filename"]?.toString() ?: "$taskId.bin").build()
        val request = OneTimeWorkRequestBuilder<BackgroundDownloadWorker>().setInputData(data).setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).setBackoffCriteria(androidx.work.BackoffPolicy.EXPONENTIAL, 10, TimeUnit.SECONDS).build()
        WorkManager.getInstance(app).enqueueUniqueWork("vidora_download_$taskId", ExistingWorkPolicy.REPLACE, request)
        emit(taskId, "created")
        return true
    }
    fun pause(taskId: String): Boolean { context?.getSharedPreferences(BackgroundDownloadWorker.PREFS, Context.MODE_PRIVATE)?.edit()?.putBoolean("paused_$taskId", true)?.apply(); emit(taskId, "paused"); return true }
    fun resume(taskId: String): Boolean { context?.getSharedPreferences(BackgroundDownloadWorker.PREFS, Context.MODE_PRIVATE)?.edit()?.putBoolean("paused_$taskId", false)?.apply(); emit(taskId, "started"); return true }
    fun cancel(taskId: String): Boolean { val app = context ?: return false; WorkManager.getInstance(app).cancelUniqueWork("vidora_download_$taskId"); emit(taskId, "cancelled"); return true }
}
