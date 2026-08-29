package com.crewintel.mobile.screens

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.crewintel.mobile.databinding.ActivityJobPostBinding

class JobPostActivity : AppCompatActivity() {

    private lateinit var binding: ActivityJobPostBinding
    private var selectedMediaUri: Uri? = null
    private var overlayBitmap: Bitmap? = null

    private val mediaPicker = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            selectedMediaUri = uri
            binding.ivPreview.setImageURI(uri)
            binding.ivPreview.visibility = View.VISIBLE
            binding.layoutPlaceholder.visibility = View.GONE
            updateOverlay()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityJobPostBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnBack.setOnClickListener { finish() }
        binding.btnSelectMedia.setOnClickListener { mediaPicker.launch("image/*") }

        // Platform share buttons
        binding.btnShareWA.setOnClickListener { shareTo("whatsapp") }
        binding.btnShareIG.setOnClickListener { shareTo("instagram") }
        binding.btnShareFB.setOnClickListener { shareTo("facebook") }
        binding.btnShareLI.setOnClickListener { shareTo("linkedin") }
        binding.btnShareTG.setOnClickListener { shareTo("telegram") }
        binding.btnShareMore.setOnClickListener { shareTo("more") }
    }

    private fun buildPostText(): String {
        val pos = binding.etPosition.text.toString().trim()
        val vessel = binding.etVesselType.text.toString().trim()
        val desc = binding.etDescription.text.toString().trim()
        val salary = binding.etSalary.text.toString().trim()
        val contact = binding.etContact.text.toString().trim()

        val sb = StringBuilder()
        sb.appendLine("⚓ İŞ İLANI")
        sb.appendLine()
        if (pos.isNotBlank()) sb.appendLine("📋 Pozisyon: $pos")
        if (vessel.isNotBlank()) sb.appendLine("🚢 Gemi: $vessel")
        if (desc.isNotBlank()) { sb.appendLine(); sb.appendLine(desc) }
        if (salary.isNotBlank()) { sb.appendLine(); sb.appendLine("💰 Maaş: $salary") }
        if (contact.isNotBlank()) { sb.appendLine(); sb.appendLine("📞 İletişim: $contact") }
        sb.appendLine()
        sb.appendLine("🔗 CREWINTEL — Personel Yönetimi")
        return sb.toString()
    }

    private fun updateOverlay() {
        val pos = binding.etPosition.text.toString().trim()
        val vessel = binding.etVesselType.text.toString().trim()
        val salary = binding.etSalary.text.toString().trim()

        if (pos.isNotBlank() || vessel.isNotBlank()) {
            binding.layoutOverlay.visibility = View.VISIBLE
            binding.tvOverlayTitle.text = buildString {
                if (pos.isNotBlank()) append(pos)
                if (vessel.isNotBlank()) { if (isNotEmpty()) append(" • "); append(vessel) }
            }
            binding.tvOverlaySub.text = buildString {
                if (salary.isNotBlank()) append("💰 $salary")
                append(" | 📞 İletişim bilgileri için mesaj atın")
            }
        } else {
            binding.layoutOverlay.visibility = View.GONE
        }
    }

    private fun shareTo(platform: String) {
        val text = buildPostText()
        if (text.length < 20) {
            Toast.makeText(this, "Lütfen ilan bilgilerini doldurun", Toast.LENGTH_SHORT).show()
            return
        }

        val intent = when (platform) {
            "whatsapp" -> {
                Intent(Intent.ACTION_SEND).apply {
                    type = if (selectedMediaUri != null) "image/*" else "text/plain"
                    setPackage("com.whatsapp")
                    putExtra(Intent.EXTRA_TEXT, text)
                    if (selectedMediaUri != null) putExtra(Intent.EXTRA_STREAM, selectedMediaUri)
                }
            }
            "instagram" -> {
                // Instagram needs share to stories or feed
                Intent(Intent.ACTION_SEND).apply {
                    type = if (selectedMediaUri != null) "image/*" else "text/plain"
                    setPackage("com.instagram.android")
                    putExtra(Intent.EXTRA_TEXT, text)
                    if (selectedMediaUri != null) putExtra(Intent.EXTRA_STREAM, selectedMediaUri)
                }
            }
            "facebook" -> {
                Intent(Intent.ACTION_SEND).apply {
                    type = if (selectedMediaUri != null) "image/*" else "text/plain"
                    setPackage("com.facebook.katana")
                    putExtra(Intent.EXTRA_TEXT, text)
                    if (selectedMediaUri != null) putExtra(Intent.EXTRA_STREAM, selectedMediaUri)
                }
            }
            "linkedin" -> {
                Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    setPackage("com.linkedin.android")
                    putExtra(Intent.EXTRA_TEXT, text)
                }
            }
            "telegram" -> {
                Intent(Intent.ACTION_SEND).apply {
                    type = if (selectedMediaUri != null) "image/*" else "text/plain"
                    setPackage("org.telegram.messenger")
                    putExtra(Intent.EXTRA_TEXT, text)
                    if (selectedMediaUri != null) putExtra(Intent.EXTRA_STREAM, selectedMediaUri)
                }
            }
            else -> {
                Intent(Intent.ACTION_SEND).apply {
                    type = if (selectedMediaUri != null) "image/*" else "text/plain"
                    putExtra(Intent.EXTRA_TEXT, text)
                    if (selectedMediaUri != null) putExtra(Intent.EXTRA_STREAM, selectedMediaUri)
                }
            }
        }

        try {
            startActivity(Intent.createChooser(intent, "İlanı paylaş"))
        } catch (e: Exception) {
            Toast.makeText(this, "Uygulama bulunamadı: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
}
