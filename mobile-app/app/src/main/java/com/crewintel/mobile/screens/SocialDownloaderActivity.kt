package com.crewintel.mobile.screens

import android.content.Intent
import android.graphics.BitmapFactory
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.crewintel.mobile.databinding.ActivitySocialDownloaderBinding
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.URL
import java.util.concurrent.TimeUnit

class SocialDownloaderActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySocialDownloaderBinding
    private var currentUrl: String? = null

    private val httpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .build()
    }

    private val backendUrl by lazy {
        PrefsManager(this).serverUrl
    }

    private val authToken: String
        get() = PrefsManager(this).authToken ?: ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySocialDownloaderBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.toolbar.setNavigationOnClickListener { finish() }
        binding.btnAnalyze.setOnClickListener { analyzeUrl() }
        binding.btnDownload.setOnClickListener { startDownload() }

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
                    val body = response.body?.string() ?: throw Exception("Empty response")

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

        binding.tvTitle.text = data.optString("title", "Bilinmeyen video")

        val uploader = data.optString("uploader", "")
        val duration = data.optInt("duration", 0)
        val views = data.optLong("view_count", 0)
        binding.tvUploader.text = buildString {
            if (uploader.isNotEmpty()) append(uploader)
            if (duration > 0) {
                if (isNotEmpty()) append(" . ")
                val min = duration / 60
                val sec = duration % 60
                append("${min}:${String.format("%02d", sec)}")
            }
            if (views > 0) {
                if (isNotEmpty()) append(" . ")
                append("${views / 1000}K views")
            }
        }

        val platform = data.optString("platform", "unknown")
        val platformName = when (platform) {
            "youtube" -> "YouTube"
            "instagram" -> "Instagram"
            "tiktok" -> "TikTok"
            "facebook" -> "Facebook"
            "pinterest" -> "Pinterest"
            "twitter" -> "Twitter/X"
            else -> platform
        }
        binding.tvPlatform.text = platformName
        val bgColor = when (platform) {
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

        val thumbnailUrl = data.optString("thumbnail", "")
        if (thumbnailUrl.isNotEmpty()) {
            loadThumbnail(thumbnailUrl)
        }

        val formats = data.optJSONArray("formats")
        val qualityList = mutableListOf<String>()
        if (formats != null) {
            for (i in 0 until formats.length()) {
                val fmt = formats.getJSONObject(i)
                val quality = fmt.optString("quality", "?")
                val ext = fmt.optString("ext", "mp4")
                qualityList.add("$quality ($ext)")
            }
        }
        if (qualityList.isEmpty()) {
            qualityList.add("En iyi kalite")
        }

        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, qualityList)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerQuality.adapter = adapter
    }

    private fun loadThumbnail(url: String) {
        lifecycleScope.launch {
            try {
                val bitmap = withContext(Dispatchers.IO) {
                    val stream = URL(url).openStream()
                    BitmapFactory.decodeStream(stream)
                }
                binding.ivThumbnail.setImageBitmap(bitmap)
            } catch (_: Exception) {
                binding.ivThumbnail.setImageResource(android.R.color.darker_gray)
            }
        }
    }

    private fun startDownload() {
        val url = currentUrl ?: return

        binding.downloadCard.visibility = View.VISIBLE
        binding.tvDownloadStatus.text = "Indiriliyor..."
        binding.btnDownload.isEnabled = false

        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    val jsonBody = JSONObject()
                        .put("url", url)
                        .put("quality", "best")
                        .put("format_type", "video")

                    val requestBody = jsonBody.toString()
                        .toRequestBody("application/json".toMediaType())

                    val request = Request.Builder()
                        .url("$backendUrl/api/social/downloader/download")
                        .post(requestBody)
                        .build()

                    val response = httpClient.newCall(request).execute()
                    val body = response.body?.string() ?: throw Exception("Empty response")
                    JSONObject(body)
                }

                val taskId = result.optString("task_id", "")
                if (taskId.isNotEmpty()) {
                    pollDownload(taskId)
                } else {
                    binding.tvDownloadStatus.text = "Indirme baslatilamadi"
                    binding.btnDownload.isEnabled = true
                }

            } catch (e: Exception) {
                binding.tvDownloadStatus.text = "Hata: ${e.localizedMessage}"
                binding.btnDownload.isEnabled = true
            }
        }
    }

    private fun pollDownload(taskId: String) {
        lifecycleScope.launch {
            val maxAttempts = 150 // 5 minutes max (150 * 2 seconds)
            var attempts = 0

            while (attempts < maxAttempts) {
                attempts++
                kotlinx.coroutines.delay(2000)
                try {
                    val status = withContext(Dispatchers.IO) {
                        val request = Request.Builder()
                            .url("$backendUrl/api/social/downloader/$taskId/status")
                            .build()
                        val response = httpClient.newCall(request).execute()
                        JSONObject(response.body?.string() ?: "{}")
                    }

                    val statusStr = status.optString("status", "")

                    if (statusStr == "completed") {
                        val files = status.optJSONArray("files")
                        if (files != null && files.length() > 0) {
                            val file = files.getJSONObject(0)
                            val fileName = file.optString("name", "video.mp4")

                            // Use OkHttp with auth token to download the file
                            downloadFileWithAuth(taskId, fileName)
                        } else {
                            binding.tvDownloadStatus.text = "Hata: Indirme tamamlandi ama dosya bulunamadi"
                            binding.btnDownload.isEnabled = true
                        }
                        return@launch
                    }

                    if (statusStr == "failed") {
                        val errorMsg = status.optString("error", "Indirme basarisiz oldu")
                        binding.tvDownloadStatus.text = "Basarisiz: $errorMsg"
                        binding.btnDownload.isEnabled = true
                        Toast.makeText(
                            this@SocialDownloaderActivity,
                            "Video indirilemedi: $errorMsg",
                            Toast.LENGTH_LONG
                        ).show()
                        return@launch
                    }

                    // Still downloading
                    binding.tvDownloadStatus.text = "Indiriliyor... ($attempts/${maxAttempts})"

                } catch (_: Exception) {
                    // Network error during polling, keep trying
                }
            }

            // Timeout
            binding.tvDownloadStatus.text = "Zaman asimi — indirme cok uzun surdu"
            binding.btnDownload.isEnabled = true
        }
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

                    if (!response.isSuccessful) {
                        throw Exception("Dosya indirilemedi: HTTP ${response.code}")
                    }

                    val body = response.body ?: throw Exception("Bos yanit")

                    // Save to Downloads/CREWINTEL/
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
                    val mediaScanIntent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
                    mediaScanIntent.data = android.net.Uri.fromFile(outputFile)
                    sendBroadcast(mediaScanIntent)

                    outputFile.name to outputFile.length()
                }

                val (savedName, savedSize) = withContext(Dispatchers.IO) {
                    val downloadsDir = File(
                        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                        "CREWINTEL"
                    )
                    val f = File(downloadsDir, fileName)
                    f.name to f.length()
                }

                val sizeMB = String.format("%.1f", savedSize / 1048576.0)
                binding.tvDownloadStatus.text = "Indirildi: $savedName ($sizeMB MB)"
                binding.btnDownload.isEnabled = true
                Toast.makeText(
                    this@SocialDownloaderActivity,
                    "Video galeriye kaydedildi!",
                    Toast.LENGTH_SHORT
                ).show()

            } catch (e: Exception) {
                binding.tvDownloadStatus.text = "Hata: ${e.localizedMessage}"
                binding.btnDownload.isEnabled = true
                Toast.makeText(
                    this@SocialDownloaderActivity,
                    "Indirme basarisiz: ${e.localizedMessage}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

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

    private fun hideError() {
        binding.tvError.visibility = View.GONE
    }
}
