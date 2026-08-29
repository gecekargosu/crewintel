package com.crewintel.mobile.screens

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.crewintel.mobile.databinding.ActivityJobPostBinding

class JobPostActivity : AppCompatActivity() {

    private lateinit var binding: ActivityJobPostBinding
    private var selectedMediaUri: Uri? = null

    private val mediaPicker = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            selectedMediaUri = uri
            binding.tvMediaIcon.text = "✅"
            binding.tvMediaHint.text = "Medya seçildi"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityJobPostBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnBack.setOnClickListener { finish() }
        binding.cardMedia.setOnClickListener {
            mediaPicker.launch("image/*")
        }

        binding.btnPreview.setOnClickListener { showPreview() }
        binding.btnShare.setOnClickListener { sharePost() }
    }

    private fun buildPostText(): String {
        val position = binding.etPosition.text.toString().trim()
        val vessel = binding.etVesselType.text.toString().trim()
        val desc = binding.etDescription.text.toString().trim()
        val salary = binding.etSalary.text.toString().trim()
        val contact = binding.etContact.text.toString().trim()

        val sb = StringBuilder()
        sb.appendLine("⚓ İŞ İLANI")
        sb.appendLine()
        if (position.isNotBlank()) sb.appendLine("📋 Pozisyon: $position")
        if (vessel.isNotBlank()) sb.appendLine("🚢 Gemi: $vessel")
        if (desc.isNotBlank()) sb.appendLine()
        if (desc.isNotBlank()) sb.appendLine(desc)
        if (salary.isNotBlank()) sb.appendLine()
        if (salary.isNotBlank()) sb.appendLine("💰 Maaş: $salary")
        if (contact.isNotBlank()) sb.appendLine()
        if (contact.isNotBlank()) sb.appendLine("📞 İletişim: $contact")
        sb.appendLine()
        sb.appendLine("🔗 CREWINTEL ile Personel Yönetimi")
        return sb.toString()
    }

    private fun showPreview() {
        val text = buildPostText()
        binding.tvPreview.text = text
        binding.tvPreview.visibility = View.VISIBLE
    }

    private fun sharePost() {
        val text = buildPostText()
        if (text.length < 20) {
            Toast.makeText(this, "Lütfen ilan bilgilerini doldurun", Toast.LENGTH_SHORT).show()
            return
        }

        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = if (selectedMediaUri != null) "image/*" else "text/plain"
            putExtra(Intent.EXTRA_TEXT, text)
            if (selectedMediaUri != null) {
                putExtra(Intent.EXTRA_STREAM, selectedMediaUri)
            }
        }
        startActivity(Intent.createChooser(shareIntent, "İlanı paylaş"))
    }
}
