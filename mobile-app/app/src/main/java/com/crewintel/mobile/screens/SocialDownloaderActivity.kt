package com.crewintel.mobile.screens

import android.content.*
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.crewintel.mobile.databinding.ActivitySocialDownloaderBinding
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.URL
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

class SocialDownloaderActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySocialDownloaderBinding
    private var currentUrl: String? = null
    private var currentTitle: String = ""
    private var currentPlatform: String = ""
    private var currentThumbnail: String = ""

    // Adapters
    private val activeAdapter = ActiveDownloadAdapter()
    private val historyAdapter = DownloadHistoryAdapter { item -> playVideo(item) }

    // Active downloads tracking
    private val activeTasks = ConcurrentHashMap<String, ActiveDownload>()

    // Polling jobs
    private val pollJobs = ConcurrentHashMap<String, Job>()

    private val httpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .build()
    }

    private val backendUrl by lazy { PrefsManager(this).serverUrl }

    private val authToken: String
        get() = PrefsManager(this).authToken ?: ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySocialDownloaderBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.toolbar.setNavigationOnClickListener { finish() }
        binding.btnAnalyze.setOnClickListener { analyzeUrl() }
        binding.btnDownload.setOnClickListener { startDownload() }

        // Setup RecyclerViews
        binding.rvActiveDownloads.layoutManager = LinearLayoutManager(this)
        binding.rvActiveDownloads.adapter = activeAdapter

        binding.rvHistory.layoutManager = LinearLayoutManager(this)
        binding.rvHistory.adapter = historyAdapter

        // Load history on start
        loadHistory()

        handleShareIntent(intent)
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleShareIntent(it) }
    }

    private fun handleShareIntent(intent: Intent?) {
        if (intent?.action == Intent.ACTION_SEND && intent.type == "text/plain") {
            val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
            sharedText?.let {
                binding.etUrl.setText(it)
                analyzeUrl()
            }
        }
    }

    private fun analyzeUrl() {
        val url = binding.etUrl.text.toString().trim()
        if (url.isEmpty()) {
            showError("Link girin")
            return
        }

        currentUrl = url
        showLoading(true)
        hideResult()
        hideError()

        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    val jsonBody = JSONObject().put("url", url)
                    val requestBody = jsonBody.toString()
                        .toRequestBody("application/json".toMediaType())

                    val request = Request.Builder()
                        .url("$backendUrl/api/social/downloader/analyze")
                        .post(requestBody)
                        .build()

                    val response = httpClient.newCall(request).execute()
                    val body = response.body?.string() ?: throw Exception("Bos yanit")

                    if (!response.isSuccessful) {
                        val error = JSONObject(body)
                        throw Exception(error.optString("detail", "Analiz hatasi"))
                    }
                    JSONObject(body)
                }

                displayResult(result)
                showLoading(false)

            } catch (e: Exception) {
                showLoading(false)
                showError("Hata: ${e.localizedMessage}")
            }
        }
    }

    private fun displayResult(data: JSONObject) {
        binding.resultCard.visibility = View.VISIBLE

        currentTitle = data.optString("title", "Bilinmeyen video")
        currentPlatform = data.optString("platform", "unknown")
        currentThumbnail = data.optString("thumbnail", "")

        binding.tvTitle.text = currentTitle

        val uploader = data.optString("uploader", "")
        val duration = data.optInt("duration", 0)
        val views = data.optLong("view_count", 0)
        binding.tvUploader.text = buildString {
            if (uploader.isNotEmpty()) append(uploader)
            if (duration > 0) {
                if (isNotEmpty()) append(" | ")
                append("${duration / 60}:${String.format("%02d", duration % 60)}")
            }
            if (views > 0) {
                if (isNotEmpty()) append(" | ")
                append("${views / 1000}K views")
            }
        }

        val platformName = when (currentPlatform) {
            "youtube" -> "YouTube"
            "instagram" -> "Instagram"
            "tiktok" -> "TikTok"
            "facebook" -> "Facebook"
            "pinterest" -> "Pinterest"
            "twitter" -> "Twitter/X"
            else -> currentPlatform
        }
        binding.tvPlatform.text = platformName
        val bgColor = when (currentPlatform) {
            "youtube" -> 0xFFFF0000.toInt()
            "instagram" -> 0xFFE1306C.toInt()
            "tiktok" -> 0xFF000000.toInt()
            "facebook" -> 0xFF1877F2.toInt()
            "pinterest" -> 0xFFE60023.toInt()
            "twitter" -> 0xFF1DA1F2.toInt()
            else -> 0xFF64748B.toInt()
        }
        binding.tvPlatform.setTextColor(0xFFFFFFFF.toInt())
        binding.tvPlatform.setBackgroundColor(bgColor)

        if (currentThumbnail.isNotEmpty()) {
            loadThumbnail(currentThumbnail)
        }

        val formats = data.optJSONArray("formats")
        val qualityList = mutableListOf<String>()
        if (formats != null) {
            for (i in 0 until formats.length()) {
                val fmt = formats.getJSONObject(i)
                qualityList.add(fmt.optString("quality", "?"))
            }
        }
        if (qualityList.isEmpty()) qualityList.add("En iyi kalite")

        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, qualityList)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerQuality.adapter = adapter
    }

    private fun loadThumbnail(url: String) {
        lifecycleScope.launch {
            try {
                val bitmap = withContext(Dispatchers.IO) {
                    BitmapFactory.decodeStream(URL(url).openStream())
                }
                binding.ivThumbnail.setImageBitmap(bitmap)
            } catch (_: Exception) {}
        }
    }

    // ── Download ─────────────────────────────────────────────────────────────
    private fun startDownload() {
        val url = currentUrl ?: return

        // Start foreground service for screen-off support
        startDownloadService(currentTitle)

        binding.downloadCard.visibility = View.VISIBLE
        binding.tvDownloadStatus.text = "Indiriliyor..."
        binding.btnDownload.isEnabled = false

        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    val quality = binding.spinnerQuality.selectedItem?.toString() ?: "best"
                    val qualityValue = quality.replace("p", "").replace("Ses (MP3)", "audio").lowercase()
                    val formatType = if (qualityValue == "audio") "audio" else "video"

                    val jsonBody = JSONObject()
                        .put("url", url)
                        .put("quality", qualityValue)
                        .put("format_type", formatType)

                    val requestBody = jsonBody.toString()
                        .toRequestBody("application/json".toMediaType())

                    val request = Request.Builder()
                        .url("$backendUrl/api/social/downloader/download")
                        .post(requestBody)
                        .build()

                    val response = httpClient.newCall(request).execute()
                    val body = response.body?.string() ?: throw Exception("Bos yanit")
                    JSONObject(body)
                }

                val taskId = result.optString("task_id", "")
                if (taskId.isNotEmpty()) {
                    // Add to active downloads
                    val activeDownload = ActiveDownload(
                        taskId = taskId,
                        title = currentTitle,
                        platform = currentPlatform,
                        thumbnail = currentThumbnail,
                        startedAt = java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault()).format(java.util.Date())
                    )
                    activeTasks[taskId] = activeDownload
                    updateActiveList()

                    // Start polling
                    pollDownload(taskId)
                } else {
                    binding.tvDownloadStatus.text = "Indirme baslatilamadi"
                    binding.btnDownload.isEnabled = true
                }

            } catch (e: Exception) {
                binding.tvDownloadStatus.text = "Hata: ${e.localizedMessage}"
                binding.btnDownload.isEnabled = true
                stopDownloadService()
            }
        }
    }

    private fun pollDownload(taskId: String) {
        val job = lifecycleScope.launch {
            val maxAttempts = 300 // 10 minutes
            var attempts = 0

            while (isActive && attempts < maxAttempts) {
                attempts++
                delay(3000)
                try {
                    val status = withContext(Dispatchers.IO) {
                        val request = Request.Builder()
                            .url("$backendUrl/api/social/downloader/$taskId/status")
                            .build()
                        val response = httpClient.newCall(request).execute()
                        JSONObject(response.body?.string() ?: "{}")
                    }

                    val statusStr = status.optString("status", "")

                    when (statusStr) {
                        "completed" -> {
                            val files = status.optJSONArray("files")
                            if (files != null && files.length() > 0) {
                                val file = files.getJSONObject(0)
                                val fileName = file.optString("name", "video.mp4")
                                downloadFileWithAuth(taskId, fileName)
                            } else {
                                showError("Indirme tamamlandi ama dosya bulunamadi")
                                binding.btnDownload.isEnabled = true
                            }
                            return@launch
                        }
                        "failed" -> {
                            val errorMsg = status.optString("error", "Basarisiz")
                            binding.tvDownloadStatus.text = "Basarisiz: $errorMsg"
                            binding.btnDownload.isEnabled = true
                            Toast.makeText(this@SocialDownloaderActivity, "Video indirilemedi", Toast.LENGTH_LONG).show()
                            stopDownloadService()
                            return@launch
                        }
                        else -> {
                            binding.tvDownloadStatus.text = "Indiriliyor... ($attempts)"
                        }
                    }
                } catch (_: Exception) {}
            }

            binding.tvDownloadStatus.text = "Zaman asimi"
            binding.btnDownload.isEnabled = true
            stopDownloadService()
        }
        pollJobs[taskId] = job
    }

    private fun downloadFileWithAuth(taskId: String, fileName: String) {
        lifecycleScope.launch {
            try {
                withContext(Dispatchers.IO) {
                    val request = Request.Builder()
                        .url("$backendUrl/api/social/downloader/$taskId/file")
                        .apply {
                            if (authToken.isNotEmpty()) {
                                addHeader("Authorization", "Bearer $authToken")
                            }
                        }
                        .build()

                    val response = httpClient.newCall(request).execute()
                    if (!response.isSuccessful) throw Exception("HTTP ${response.code}")

                    val body = response.body ?: throw Exception("Bos yanit")

                    val downloadsDir = File(
                        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                        "CREWINTEL"
                    )
                    downloadsDir.mkdirs()

                    val outputFile = File(downloadsDir, fileName)
                    body.byteStream().use { input ->
                        FileOutputStream(outputFile).use { output ->
                            input.copyTo(output)
                        }
                    }

                    // Notify media scanner
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        android.media.MediaScannerConnection.scanFile(
                            this@SocialDownloaderActivity,
                            arrayOf(outputFile.absolutePath),
                            null, null
                        )
                    } else {
                        sendBroadcast(Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE, Uri.fromFile(outputFile)))
                    }
                }

                // Remove from active, add to history
                activeTasks.remove(taskId)
                pollJobs.remove(taskId)?.cancel()
                updateActiveList()

                binding.tvDownloadStatus.text = "Indirildi: $fileName"
                binding.btnDownload.isEnabled = true

                val sizeMB = withContext(Dispatchers.IO) {
                    val f = File(
                        File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), "CREWINTEL"),
                        fileName
                    )
                    String.format("%.1f MB", f.length() / 1048576.0)
                }

                Toast.makeText(this@SocialDownloaderActivity, "Video kaydedildi! ($sizeMB)", Toast.LENGTH_SHORT).show()

                // Reload history
                loadHistory()
                stopDownloadService()

            } catch (e: Exception) {
                binding.tvDownloadStatus.text = "Hata: ${e.localizedMessage}"
                binding.btnDownload.isEnabled = true
                stopDownloadService()
            }
        }
    }

    // ── History ──────────────────────────────────────────────────────────────
    private fun loadHistory() {
        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    val request = Request.Builder()
                        .url("$backendUrl/api/social/downloader/history")
                        .build()
                    val response = httpClient.newCall(request).execute()
                    JSONObject(response.body?.string() ?: "{}")
                }

                val files = result.optJSONArray("files")
                val items = mutableListOf<HistoryItem>()
                if (files != null) {
                    for (i in 0 until files.length()) {
                        val f = files.getJSONObject(i)
                        items.add(HistoryItem(
                            taskId = f.optString("task_id", ""),
                            title = f.optString("title", ""),
                            platform = f.optString("platform", ""),
                            fileName = f.optString("name", ""),
                            fileSize = f.optLong("size", 0),
                            thumbnail = f.optString("thumbnail", ""),
                            downloadedAt = f.optString("downloaded_at", ""),
                        ))
                    }
                }

                if (items.isNotEmpty()) {
                    binding.tvHistoryHeader.visibility = View.VISIBLE
                    binding.rvHistory.visibility = View.VISIBLE
                    historyAdapter.updateList(items)
                } else {
                    binding.tvHistoryHeader.visibility = View.GONE
                    binding.rvHistory.visibility = View.GONE
                }
            } catch (_: Exception) {}
        }
    }

    private fun playVideo(item: HistoryItem) {
        val downloadsDir = File(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
            "CREWINTEL"
        )
        val file = File(downloadsDir, item.fileName)
        if (file.exists()) {
            val intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.fromFile(file), "video/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            startActivity(intent)
        } else {
            Toast.makeText(this, "Dosya bulunamadi: ${item.fileName}", Toast.LENGTH_SHORT).show()
        }
    }

    // ── Active Downloads UI ──────────────────────────────────────────────────
    private fun updateActiveList() {
        val active = activeTasks.values.toList()
        if (active.isNotEmpty()) {
            binding.tvActiveHeader.visibility = View.VISIBLE
            binding.rvActiveDownloads.visibility = View.VISIBLE
            activeAdapter.updateList(active)
        } else {
            binding.tvActiveHeader.visibility = View.GONE
            binding.rvActiveDownloads.visibility = View.GONE
        }
    }

    // ── Foreground Service ───────────────────────────────────────────────────
    private fun startDownloadService(title: String) {
        val intent = Intent(this, DownloadService::class.java).apply {
            action = DownloadService.ACTION_START
            putExtra(DownloadService.EXTRA_TITLE, "Indiriliyor: $title")
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun stopDownloadService() {
        if (activeTasks.isEmpty()) {
            val intent = Intent(this, DownloadService::class.java).apply {
                action = DownloadService.ACTION_STOP
            }
            startService(intent)
        }
    }

    // ── UI Helpers ───────────────────────────────────────────────────────────
    private fun showLoading(show: Boolean) {
        binding.progressBar.visibility = if (show) View.VISIBLE else View.GONE
        binding.btnAnalyze.isEnabled = !show
    }

    private fun hideResult() {
        binding.resultCard.visibility = View.GONE
        binding.downloadCard.visibility = View.GONE
    }

    private fun showError(msg: String) {
        binding.tvError.text = msg
        binding.tvError.visibility = View.VISIBLE
    }

    override fun onDestroy() {
        super.onDestroy()
        pollJobs.values.forEach { it.cancel() }
        pollJobs.clear()
        stopDownloadService()
    }

    private fun hideError() {
        binding.tvError.visibility = View.GONE
    }

}
