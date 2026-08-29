package com.crewintel.mobile.screens

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.crewintel.mobile.R
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class SocialSettingsActivity : AppCompatActivity() {

    private val httpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    private val backendUrl by lazy { PrefsManager(this).serverUrl }

    // Platform data
    data class PlatformConfig(
        val name: String,
        val editId: Int,
        val statusId: Int,
        val saveId: Int,
    )

    private val platforms = listOf(
        PlatformConfig("instagram", R.id.etInstagramCookies, R.id.tvInstagramStatus, R.id.btnInstagramSave),
        PlatformConfig("youtube", R.id.etYouTubeCookies, R.id.tvYouTubeStatus, R.id.btnYouTubeSave),
        PlatformConfig("tiktok", R.id.etTikTokCookies, R.id.tvTikTokStatus, R.id.btnTikTokSave),
        PlatformConfig("pinterest", R.id.etPinterestCookies, R.id.tvPinterestStatus, R.id.btnPinterestSave),
        PlatformConfig("linkedin", R.id.etLinkedInCookies, R.id.tvLinkedInStatus, R.id.btnLinkedInSave),
        PlatformConfig("facebook", R.id.etFacebookCookies, R.id.tvFacebookStatus, R.id.btnFacebookSave),
        PlatformConfig("twitter", R.id.etTwitterCookies, R.id.tvTwitterStatus, R.id.btnTwitterSave),
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_social_settings)

        findViewById<com.google.android.material.appbar.MaterialToolbar>(R.id.toolbar)
            .setNavigationOnClickListener { finish() }

        // Load existing cookies status
        loadCookieStatus()

        // Setup save buttons
        platforms.forEach { config ->
            findViewById<Button>(config.saveId).setOnClickListener {
                val cookies = findViewById<EditText>(config.editId).text.toString().trim()
                if (cookies.isEmpty()) {
                    Toast.makeText(this, "Once cookie icerigini yapistirin", Toast.LENGTH_SHORT).show()
                    return@setOnClickListener
                }
                saveCookie(config.name, cookies, config.statusId)
            }
        }
    }

    private fun loadCookieStatus() {
        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    val request = Request.Builder()
                        .url("$backendUrl/api/social/downloader/cookies")
                        .build()
                    val response = httpClient.newCall(request).execute()
                    JSONObject(response.body?.string() ?: "{}")
                }

                val cookies = result.optJSONObject("cookies")
                if (cookies != null) {
                    platforms.forEach { config ->
                        val status = cookies.optJSONObject(config.name)
                        val statusView = findViewById<TextView>(config.statusId)
                        if (status != null && status.optBoolean("exists", false)) {
                            statusView.text = "Baglandi (${status.optInt("lines", 0)} satir)"
                            statusView.setTextColor(0xFF22C55E.toInt()) // green
                        } else {
                            statusView.text = "Baglanmadi"
                            statusView.setTextColor(0xFFEF4444.toInt()) // red
                        }
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@SocialSettingsActivity, "Sunucuya baglanamadi", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun saveCookie(platform: String, cookies: String, statusId: Int) {
        lifecycleScope.launch {
            try {
                withContext(Dispatchers.IO) {
                    val jsonBody = JSONObject()
                        .put("platform", platform)
                        .put("cookies", cookies)

                    val requestBody = jsonBody.toString()
                        .toRequestBody("application/json".toMediaType())

                    val request = Request.Builder()
                        .url("$backendUrl/api/social/downloader/cookies")
                        .post(requestBody)
                        .build()

                    val response = httpClient.newCall(request).execute()
                    if (!response.isSuccessful) {
                        throw Exception("Kaydetme basarisiz: HTTP ${response.code}")
                    }
                }

                // Update status
                val statusView = findViewById<TextView>(statusId)
                statusView.text = "Baglandi"
                statusView.setTextColor(0xFF22C55E.toInt())

                Toast.makeText(
                    this@SocialSettingsActivity,
                    "$platform cookie basariyla kaydedildi!",
                    Toast.LENGTH_SHORT
                ).show()

                // Refresh all statuses
                loadCookieStatus()

            } catch (e: Exception) {
                Toast.makeText(
                    this@SocialSettingsActivity,
                    "Hata: ${e.localizedMessage}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }
}
