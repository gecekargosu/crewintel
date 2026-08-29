package com.crewintel.mobile.screens

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityDashboardBinding
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class DashboardActivity : AppCompatActivity() {

    private lateinit var binding: ActivityDashboardBinding
    private lateinit var prefs: PrefsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDashboardBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = PrefsManager(this)

        if (!prefs.isLoggedIn()) {
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
            return
        }

        setupUI()
        loadDashboard()
    }

    override fun onResume() {
        super.onResume()
        loadDashboard()
    }

    private fun setupUI() {
        binding.tvUserRole.text = prefs.userRole?.uppercase() ?: "USER"
        binding.tvServerInfo.text = "Sunucu: ${prefs.serverUrl}"

        binding.swipeRefresh.setOnRefreshListener { loadDashboard() }

        // Quick action buttons
        binding.btnCrew.setOnClickListener {
            startActivity(Intent(this, CrewListActivity::class.java))
        }
        binding.btnDocuments.setOnClickListener {
            startActivity(Intent(this, DocumentListActivity::class.java))
        }
        binding.btnShips.setOnClickListener {
            startActivity(Intent(this, ShipListActivity::class.java))
        }
        binding.btnAI.setOnClickListener {
            startActivity(Intent(this, AIAnalysisActivity::class.java))
        }
        binding.btnDownloader.setOnClickListener {
            startActivity(Intent(this, SocialDownloaderActivity::class.java))
        }
        binding.btnSettings.setOnClickListener {
            showSettingsDialog()
        }

        // Activity feed button
        binding.btnActivity.setOnClickListener {
            startActivity(Intent(this, ActivityFeedActivity::class.java))
        }

        // Email button
        binding.btnEmail.setOnClickListener {
            startActivity(Intent(this, EmailActivity::class.java))
        }

        // Upload button
        binding.btnUpload.setOnClickListener {
            startActivity(Intent(this, DocumentUploadActivity::class.java))
        }

        // Warning click listeners
        binding.tvExpired.setOnClickListener {
            startActivity(Intent(this, WarningDetailActivity::class.java).apply {
                putExtra(WarningDetailActivity.EXTRA_FILTER_TYPE, WarningDetailActivity.FILTER_EXPIRED)
                putExtra(WarningDetailActivity.EXTRA_TITLE, "Süresi Dolmuş Belgeler")
            })
        }
        binding.tvUrgent.setOnClickListener {
            startActivity(Intent(this, WarningDetailActivity::class.java).apply {
                putExtra(WarningDetailActivity.EXTRA_FILTER_TYPE, WarningDetailActivity.FILTER_URGENT)
                putExtra(WarningDetailActivity.EXTRA_TITLE, "Acil Belgeler (30 gün)")
            })
        }
        binding.tvApproaching.setOnClickListener {
            startActivity(Intent(this, WarningDetailActivity::class.java).apply {
                putExtra(WarningDetailActivity.EXTRA_FILTER_TYPE, WarningDetailActivity.FILTER_APPROACHING)
                putExtra(WarningDetailActivity.EXTRA_TITLE, "Yaklaşıyor (90 gün)")
            })
        }
        binding.tvUnmatched.setOnClickListener {
            startActivity(Intent(this, WarningDetailActivity::class.java).apply {
                putExtra(WarningDetailActivity.EXTRA_FILTER_TYPE, WarningDetailActivity.FILTER_UNMATCHED)
                putExtra(WarningDetailActivity.EXTRA_TITLE, "Eşleşmemiş Belgeler")
            })
        }
    }

    private fun loadDashboard() {
        binding.swipeRefresh.isRefreshing = true

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)

                val health = api.health()
                if (health.isSuccessful) {
                    binding.tvServerInfo.text = "Sunucu: ${prefs.serverUrl} ✅"
                }

                val summary = api.dashboardSummary()
                if (summary.isSuccessful) {
                    val data = summary.body()!!
                    binding.tvCrewCount.text = data.totalCrew.toString()
                    binding.tvDocCount.text = data.totalDocuments.toString()
                    binding.tvShipCount.text = data.activeShips.toString()
                    binding.tvExpired.text = "🔴 Süresi Dolmuş: ${data.expiredDocuments}"
                    binding.tvUrgent.text = "🟠 Acil: ${data.urgentDocuments}"
                    binding.tvApproaching.text = "🟡 Yaklaşıyor: ${data.expiringDocuments}"
                    binding.tvUnmatched.text = "⚪ Eşleşmemiş: ${data.unmatchedDocuments}"
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@DashboardActivity,
                    "Sunucuya bağlanılamıyor: ${e.localizedMessage}",
                    Toast.LENGTH_LONG
                ).show()
                binding.tvServerInfo.text = "Sunucu: BAĞLANTI HATASI ❌"
            } finally {
                binding.swipeRefresh.isRefreshing = false
            }
        }
    }

    private fun showSettingsDialog() {
        val items = arrayOf(
            "📧 E-posta Gönder",
            "📤 Belge Yükle",
            "🔍 AI ile Analiz",
            "📥 Video İndirici",
            "📋 Aktivite Akışı",
            "🔄 Sunucu Adresini Değiştir",
            "🚪 Çıkış Yap"
        )

        AlertDialog.Builder(this)
            .setTitle("İşlemler")
            .setItems(items) { _, which ->
                when (which) {
                    0 -> startActivity(Intent(this, EmailActivity::class.java))
                    1 -> startActivity(Intent(this, DocumentUploadActivity::class.java))
                    2 -> startActivity(Intent(this, AIAnalysisActivity::class.java))
                    3 -> startActivity(Intent(this, SocialDownloaderActivity::class.java))
                    4 -> startActivity(Intent(this, ActivityFeedActivity::class.java))
                    5 -> showChangeServerDialog()
                    6 -> logout()
                }
            }
            .show()
    }

    private fun showChangeServerDialog() {
        val input = android.widget.EditText(this).apply {
            setText(prefs.serverUrl)
            hint = "http://192.168.1.100:8000"
        }

        AlertDialog.Builder(this)
            .setTitle("Sunucu Adresi")
            .setView(input)
            .setPositiveButton("Kaydet") { _, _ ->
                prefs.serverUrl = input.text.toString().trim()
                ApiClient.reset()
                loadDashboard()
            }
            .setNegativeButton("İptal", null)
            .show()
    }

    private fun logout() {
        prefs.clearSession()
        ApiClient.reset()
        startActivity(Intent(this, LoginActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        })
        finish()
    }
}
