package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityEmailBinding
import com.crewintel.mobile.models.CrewMember
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class EmailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityEmailBinding
    private lateinit var prefs: PrefsManager
    private var crewList = listOf<CrewMember>()
    private var selectedCrew: CrewMember? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityEmailBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.btnSend.setOnClickListener { sendEmail() }

        loadCrewList()
    }

    private fun loadCrewList() {
        binding.progressBar.visibility = View.VISIBLE
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getCrewList()
                if (response.isSuccessful) {
                    crewList = response.body() ?: emptyList()
                    val names = crewList.map { "${it.firstName} ${it.lastName}" }
                    val adapter = ArrayAdapter(this@EmailActivity, android.R.layout.simple_spinner_item, names)
                    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
                    binding.spinnerCrew.adapter = adapter
                    binding.spinnerCrew.onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
                        override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: View?, position: Int, id: Long) {
                            selectedCrew = crewList.getOrNull(position)
                        }
                        override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@EmailActivity, "Personel listesi yüklenemedi", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun sendEmail() {
        val crew = selectedCrew
        if (crew == null) {
            Toast.makeText(this, "Lütfen bir personel seçin", Toast.LENGTH_SHORT).show()
            return
        }
        if (crew.email.isNullOrBlank()) {
            Toast.makeText(this, "Bu personelin e-posta adresi kayıtlı değil", Toast.LENGTH_SHORT).show()
            return
        }
        val subject = binding.etSubject.text.toString().trim()
        val body = binding.etBody.text.toString().trim()
        if (subject.isBlank()) {
            Toast.makeText(this, "Lütfen konu girin", Toast.LENGTH_SHORT).show()
            return
        }

        binding.progressBar.visibility = View.VISIBLE
        binding.btnSend.isEnabled = false
        binding.tvStatus.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val request = mapOf(
                    "crew_member_id" to crew.id.toString(),
                    "subject" to subject,
                    "body" to body
                )
                val response = api.sendEmail(request)
                if (response.isSuccessful) {
                    val result = response.body()
                    val resultMap = if (result is Map<*, *>) result else emptyMap<Any, Any>()
                    val status = resultMap["status"]?.toString() ?: ""
                    val message = resultMap["message"]?.toString() ?: "Gönderildi"
                    binding.tvStatus.visibility = View.VISIBLE
                    binding.tvStatus.text = "✅ $message (${crew.firstName} ${crew.lastName} → ${crew.email})"
                    binding.tvStatus.setTextColor(0xFF16a34a.toInt())
                    binding.etSubject.text.clear()
                    binding.etBody.text.clear()
                } else {
                    val error = response.errorBody()?.string() ?: "Bilinmeyen hata"
                    binding.tvStatus.visibility = View.VISIBLE
                    binding.tvStatus.text = "❌ Hata: $error"
                    binding.tvStatus.setTextColor(0xFFdc2626.toInt())
                }
            } catch (e: Exception) {
                binding.tvStatus.visibility = View.VISIBLE
                binding.tvStatus.text = "❌ Bağlantı hatası: ${e.message}"
                binding.tvStatus.setTextColor(0xFFdc2626.toInt())
            } finally {
                binding.progressBar.visibility = View.GONE
                binding.btnSend.isEnabled = true
            }
        }
    }
}
