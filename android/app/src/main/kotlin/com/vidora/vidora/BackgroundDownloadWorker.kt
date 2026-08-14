package com.vidora.vidora

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Environment
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.ForegroundInfo
import androidx.work.WorkerParameters
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URI

class BackgroundDownloadWorker(appContext: Context, params: WorkerParameters) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val taskId = inputData.getString("task_id") ?: return@withContext Result.failure()
        val url = inputData.getString("url") ?: return@withContext Result.failure()
        val filename = safeFilename(inputData.getString("filename") ?: "$taskId.bin")
        val output = File(applicationContext.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "Vidora/$filename")
        output.parentFile?.mkdirs()
        try {
            ensureActive()
            if (isPaused(taskId)) return@withContext Result.retry()
            emit(taskId, "started", 0, output.absolutePath)
            setForeground(createForegroundInfo(taskId, 0, "Starting"))
            val connection = (URI(url).toURL().openConnection() as HttpURLConnection).apply {
                connectTimeout = 15_000
                readTimeout = 30_000
                requestMethod = "GET"
                instanceFollowRedirects = true
            }
            connection.connect()
            if (connection.responseCode !in 200..299) {
                emit(taskId, "failed", 0, output.absolutePath, "HTTP_${connection.responseCode}")
                return@withContext Result.failure()
            }
            val total = connection.contentLengthLong
            var downloaded = 0L
            connection.inputStream.use { input -> output.outputStream().use { file ->
                val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                while (true) {
                    ensureActive()
                    if (isStopped || isPaused(taskId)) {
                        emit(taskId, if (isPaused(taskId)) "paused" else "cancelled", downloaded, output.absolutePath)
                        return@withContext if (isPaused(taskId)) Result.retry() else Result.failure()
                    }
                    val count = input.read(buffer)
                    if (count < 0) break
                    file.write(buffer, 0, count)
                    downloaded += count
                    val progress = if (total > 0) ((downloaded * 100) / total).toInt() else 0
                    setProgress(androidx.work.workDataOf("event" to "progress", "progress" to progress, "bytes_downloaded" to downloaded, "total_bytes" to total))
                    setForeground(createForegroundInfo(taskId, progress, "$progress%"))
                    emit(taskId, "progress", downloaded, output.absolutePath, progress.toString(), total.toString())
                }
            }}
            emit(taskId, "completed", downloaded, output.absolutePath, "100", total.toString())
            setForeground(createForegroundInfo(taskId, 100, "Completed"))
            Result.success()
        } catch (error: Exception) {
            if (isStopped) Result.retry() else { emit(taskId, "failed", 0, output.absolutePath, "NETWORK_ERROR"); Result.failure() }
        }
    }

    private fun isPaused(taskId: String) = applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean("paused_$taskId", false)
    private fun safeFilename(value: String) = value.substringAfterLast('/').substringAfterLast('\\').replace(Regex("[^A-Za-z0-9._ -]"), "_").ifBlank { "download.bin" }
    private fun emit(taskId: String, event: String, bytes: Long, path: String, progress: String? = null, total: String? = null) = BackgroundDownloadBridge.emit(taskId, event, mapOf("bytes_downloaded" to bytes, "output_path" to path, "progress" to progress, "total_bytes" to total))
    private fun createForegroundInfo(taskId: String, progress: Int, text: String): ForegroundInfo {
        val manager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(NotificationChannel(CHANNEL_ID, "Vidora downloads", NotificationManager.IMPORTANCE_LOW))
        val intent = Intent(applicationContext, MainActivity::class.java).putExtra("vidora_task_id", taskId).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        val pendingIntent = PendingIntent.getActivity(applicationContext, taskId.hashCode(), intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification: Notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID).setSmallIcon(android.R.drawable.stat_sys_download).setContentTitle("Vidora download").setContentText(text).setContentIntent(pendingIntent).setAutoCancel(progress >= 100).setProgress(100, progress, progress == 0).setOngoing(progress in 1..99).build()
        return ForegroundInfo(taskId.hashCode(), notification)
    }
    companion object { const val PREFS = "vidora_background_downloads"; const val CHANNEL_ID = "vidora_downloads" }
}
