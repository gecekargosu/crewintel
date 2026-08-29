package com.crewintel.mobile.screens

import android.app.DownloadManager
import android.content.Context
import android.graphics.BitmapFactory
import android.net.Uri
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
import java.net.URL
import java.util.concurrent.TimeUnit

class SocialDownloaderActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySocialDownloaderBinding
    private var currentUrl: String? = null
    private var downloadClientId: Long = -1

    private val httpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .build()
    }

    private val backendUrl by lazy {
        PrefsManager(this).serverUrl
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySocialDownloaderBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.toolbar.setNavigationOnClickListener { finish() }
        binding.btnAnalyze.setOnClickListener { analyzeUrl() }
        binding.btnDownload.setOnClickListener { startDownload() }

        handleShareIntent(intent)
    }

    override fun onNewIntent(intent: android.content.Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleShareIntent(it) }
    }

    private fun handleShareIntent(intent: android.content.Intent?) {
        if (intent?.action == android.content.Intent.ACTION_SEND && intent.type == "text/plain") {
            val sharedText = intent.getStringExtra(android.content.Intent.EXTRA_TEXT)
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
                        throw Exception(error.optString("detail", "Analiz hatası"))
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
                if (isNotEmpty()) append(" · ")
                val min = duration / 60
                val sec = duration % 60
                append("${min}:${String.format("%02d", sec)}")
            }
            if (views > 0) {
                if (isNotEmpty()) append(" · ")
                append("${views / 1000}K views")
            }
        }

        val platform = data.optString("platform", "unknown")
        val platformName = when (platform) {
            "youtube" -> "▶️ YouTube"
            "instagram" -> "📷 Instagram"
            "tiktok" -> "🎵 TikTok"
            "facebook" -> "📘 Facebook"
            "pinterest" -> "📌 Pinterest"
            "twitter" -> "🐦 Twitter/X"
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
        binding.tvDownloadStatus.text = "İndiriliyor..."
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
                    binding.tvDownloadStatus.text = "İndirme başlatılamadı"
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
            while (true) {
                kotlinx.coroutines.delay(2000)
                try {
                    val status = withContext(Dispatchers.IO) {
                        val request = Request.Builder()
                            .url("$backendUrl/api/social/downloader/$taskId/status")
                            .build()
                        val response = httpClient.newCall(request).execute()
                        JSONObject(response.body?.string() ?: "{}")
                    }

                    if (status.optString("status") == "completed") {
                        val files = status.optJSONArray("files")
                        if (files != null && files.length() > 0) {
                            val file = files.getJSONObject(0)
                            val fileName = file.optString("name", "video.mp4")
                            val downloadUrl = "$backendUrl/api/social/downloader/$taskId/file"

                            val dm = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                            val request = DownloadManager.Request(Uri.parse(downloadUrl))
                                .setTitle("CREWINTEL Downloader")
                                .setDescription("İndiriliyor: $fileName")
                                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                                .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "CREWINTEL/$fileName")
                                .setAllowedOverMetered(true)
                                .setAllowedOverRoaming(true)

                            downloadClientId = dm.enqueue(request)

                            binding.tvDownloadStatus.text = "✅ Galeriye indirildi: $fileName"
                            binding.btnDownload.isEnabled = true
                            Toast.makeText(this@SocialDownloaderActivity, "İndirme tamamlandı!", Toast.LENGTH_SHORT).show()
                        }
                        break
                    }
                } catch (_: Exception) {}
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
