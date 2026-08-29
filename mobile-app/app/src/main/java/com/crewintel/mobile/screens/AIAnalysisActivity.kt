package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityAiAnalysisBinding
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

        binding.btnAnalyze.setOnClickListener { analyzeText() }
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
                val response = api.analyzeDocument(mapOf("text" to text))
                if (response.isSuccessful) {
                    val result = response.body()
                    binding.tvResult.text = result?.toString() ?: "Sonuc bulunamadi"
                } else {
                    binding.tvResult.text = "Hata: ${response.code()}"
                }
            } catch (e: Exception) {
                binding.tvResult.text = "Baglanti hatasi: ${e.message}"
            } finally {
                binding.btnAnalyze.isEnabled = true
            }
        }
    }
}
