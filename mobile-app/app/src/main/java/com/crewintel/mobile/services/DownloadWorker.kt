package com.crewintel.mobile.services

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.crewintel.mobile.R
import com.crewintel.mobile.utils.PrefsManager
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject

/**
 * WorkManager worker that polls download status in the background.
 * Survives Activity destruction, screen off, and app backgrounding.
 */
class DownloadWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    companion object {
        const val KEY_TASK_ID = "task_id"
        const val KEY_TITLE = "title"
        const val KEY_SERVER_URL = "server_url"
        const val KEY_AUTH_TOKEN = "auth_token"
        const val NOTIFICATION_CHANNEL_ID = "download_channel"
        const val NOTIFICATION_ID = 1001
    }

    private val httpClient = OkHttpClient()

    override suspend fun doWork(): Result {
        val taskId = inputData.getString(KEY_TASK_ID) ?: return Result.failure()
        val title = inputData.getString(KEY_TITLE) ?: "Video"
        val serverUrl = inputData.getString(KEY_SERVER_URL) ?: return Result.failure()
        val authToken = inputData.getString(KEY_AUTH_TOKEN) ?: return Result.failure()

        createNotificationChannel()
        showNotification("İndiriliyor: $title", "Lütfen bekleyin...")

        val maxAttempts = 90 // 3 minutes
        var attempts = 0

        while (attempts < maxAttempts) {
            attempts++
            try {
                Thread.sleep(2000) // Poll every 2 seconds

                val statusUrl = "$serverUrl/api/social/downloader/$taskId/status"
                val request = Request.Builder()
                    .url(statusUrl)
                    .addHeader("Authorization", "Bearer $authToken")
                    .build()

                val response = httpClient.newCall(request).execute()
                val body = response.body?.string() ?: "{}"
                val json = JSONObject(body)
                val status = json.optString("status", "")

                when (status) {
                    "completed" -> {
                        val files = json.optJSONArray("files")
                        if (files != null && files.length() > 0) {
                            val file = files.getJSONObject(0)
                            val fileName = file.optString("name", "video.mp4")
                            showNotification("İndirme tamamlandı!", "$fileName indirildi")
                            // Store result for the Activity to pick up
                            val outputData = androidx.work.workDataOf(
                                "task_id" to taskId,
                                "file_name" to fileName,
                                "status" to "completed"
                            )
                            return Result.success(outputData)
                        } else {
                            showNotification("İndirme tamamlandı", "Dosya bulunamadı")
                            return Result.failure()
                        }
                    }
                    "failed" -> {
                        val errorMsg = json.optString("error", "Başarısız")
                        showNotification("İndirme başarısız", errorMsg)
                        return Result.failure()
                    }
                    else -> {
                        showNotification("İndiriliyor: $title", "Lütfen bekleyin... ($attempts)")
                    }
                }
            } catch (_: Exception) {
                // Retry on network error
            }
        }

        showNotification("Zaman aşımı", "İndirme tamamlanamadı")
        return Result.failure()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "Video İndirmeleri",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Video indirme durumu"
            }
            val manager = applicationContext.getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun showNotification(title: String, text: String) {
        val manager = applicationContext.getSystemService(NotificationManager::class.java)
        val notification = NotificationCompat.Builder(applicationContext, NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(title)
            .setContentText(text)
            .setOngoing(true)
            .build()
        manager.notify(NOTIFICATION_ID, notification)
    }
}
