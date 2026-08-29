package com.crewintel.mobile.screens

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.crewintel.mobile.R

class DownloadService : Service() {

    companion object {
        const val CHANNEL_ID = "crewintel_downloads"
        const val NOTIFICATION_ID = 1001
        const val ACTION_START = "ACTION_START_DOWNLOAD"
        const val ACTION_STOP = "ACTION_STOP_DOWNLOAD"
        const val EXTRA_TITLE = "EXTRA_TITLE"
        const val EXTRA_TASK_ID = "EXTRA_TASK_ID"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                val title = intent.getStringExtra(EXTRA_TITLE) ?: "Video indiriliyor..."
                startForeground(NOTIFICATION_ID, buildNotification(title))
            }
            ACTION_STOP -> {
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Video Indirmeleri",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Video indirme durumu"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(title: String): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this, 0,
            packageManager.getLaunchIntentForPackage(packageName),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("CREWINTEL Downloader")
            .setContentText(title)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setSilent(true)
            .build()
    }

    fun updateNotification(title: String) {
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, buildNotification(title))
    }
}
