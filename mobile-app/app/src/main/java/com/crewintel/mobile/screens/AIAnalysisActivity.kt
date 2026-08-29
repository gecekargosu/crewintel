package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityAiAnalysisBinding
import com.crewintel.mobile.models.AIAnalyzeRequest
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class AIAnalysisActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAiAnalysisBinding
    private lateinit var prefs: PrefsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAiAnalysisBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = PrefsManager(this)
        binding.toolbar.setNavigationOnClickListener { finish() }

        // Health check
        checkAIHealth()

        binding.btnAnalyze.setOnClickListener { analyzeText() }
        binding.btnMatch.setOnClickListener { matchText() }
    }

    private fun checkAIHealth() {
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.aiHealth()
                if (response.isSuccessful) {
                    val data = response.body()!!
                    binding.tvHealth.text = if (data.llmAvailable) {
                        "✅ AI Aktif (${data.provider} / ${data.model})"
                    } else {
                        "⚠️ AI Pasif — GROQ_API_KEY tanımlı değil"
                    }
                }
            } catch (e: Exception) {
                binding.tvHealth.text = "❌ AI sağlık kontrolü başarısız"
            }
        }
    }

    private fun analyzeText() {
        val text = binding.etInput.text.toString().trim()
        if (text.isEmpty()) {
            Toast.makeText(this, "Metin girin", Toast.LENGTH_SHORT).show()
            return
        }

        binding.btnAnalyze.isEnabled = false
        binding.tvResult.text = "Analiz ediliyor..."

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.aiAnalyze(AIAnalyzeRequest(text))
                if (response.isSuccessful) {
                    val result = response.body()!!
                    binding.tvResult.text = buildString {
                        appendLine("📋 Tip: ${result.documentType ?: "—"}")
                        appendLine("🎯 Güven: %${(result.confidence?.times(100))?.toInt() ?: 0}")
                        appendLine()
                        appendLine("Entity'ler:")
                        result.entities?.forEach { (k, v) ->
                            appendLine("  • $k: $v")
                        }
                        appendLine()
                        appendLine("Öneriler:")
                        result.suggestions?.forEach { s ->
                            appendLine("  • $s")
                        }
                    }
                } else {
                    binding.tvResult.text = "Hata: ${response.code()} — ${response.message()}"
                }
            } catch (e: Exception) {
                binding.tvResult.text = "Bağlantı hatası: ${e.localizedMessage}"
            } finally {
                binding.btnAnalyze.isEnabled = true
            }
        }
    }

    private fun matchText() {
        val text = binding.etInput.text.toString().trim()
        if (text.isEmpty()) {
            Toast.makeText(this, "Metin girin", Toast.LENGTH_SHORT).show()
            return
        }

        binding.btnMatch.isEnabled = false
        binding.tvResult.text = "Eşleştirme yapılıyor..."

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.aiMatch(AIAnalyzeRequest(text))
                if (response.isSuccessful) {
                    val raw = response.body()
                    val result = if (raw is Map<*, *>) raw else emptyMap<Any, Any>()
                    binding.tvResult.text = buildString {
                        result.forEach { (k, v) ->
                            appendLine("$k: $v")
                        }
                    }
                } else {
                    binding.tvResult.text = "Hata: ${response.code()}"
                }
            } catch (e: Exception) {
                binding.tvResult.text = "Bağlantı hatası: ${e.localizedMessage}"
            } finally {
                binding.btnMatch.isEnabled = true
            }
        }
    }
}
