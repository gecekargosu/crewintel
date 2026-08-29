package com.crewintel.mobile.screens

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Shader
import android.graphics.Typeface
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityJobPostBinding
import java.io.File
import java.io.FileOutputStream

class JobPostActivity : AppCompatActivity() {

    private lateinit var binding: ActivityJobPostBinding
    private var selectedImageBitmap: Bitmap? = null
    private var selectedMediaUri: Uri? = null

    private val mediaPicker = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            selectedMediaUri = uri
            try {
                val inputStream = contentResolver.openInputStream(uri)
                selectedImageBitmap = android.graphics.BitmapFactory.decodeStream(inputStream)
                inputStream?.close()

                binding.ivPreview.setImageURI(uri)
                binding.ivPreview.visibility = View.VISIBLE
                binding.layoutPlaceholder.visibility = View.GONE
                updateOverlay()
            } catch (e: Exception) {
                Toast.makeText(this, "Resim yüklenemedi", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityJobPostBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnBack.setOnClickListener { finish() }
        binding.btnSelectMedia.setOnClickListener { mediaPicker.launch("image/*") }

        binding.btnShareWA.setOnClickListener { shareWithOverlay("com.whatsapp") }
        binding.btnShareIG.setOnClickListener { shareWithOverlay("com.instagram.android") }
        binding.btnShareFB.setOnClickListener { shareWithOverlay("com.facebook.katana") }
        binding.btnShareLI.setOnClickListener { shareWithOverlay("com.linkedin.android") }
        binding.btnShareTG.setOnClickListener { shareWithOverlay("org.telegram.messenger") }
        binding.btnShareMore.setOnClickListener { shareWithOverlay(null) }
    }

    private fun updateOverlay() {
        val pos = binding.etPosition.text.toString().trim()
        val vessel = binding.etVesselType.text.toString().trim()
        if (pos.isNotBlank() || vessel.isNotBlank()) {
            binding.layoutOverlay.visibility = View.VISIBLE
            binding.tvOverlayTitle.text = buildString {
                if (pos.isNotBlank()) append(pos)
                if (vessel.isNotBlank()) { if (isNotEmpty()) append(" • "); append(vessel) }
            }
            val salary = binding.etSalary.text.toString().trim()
            binding.tvOverlaySub.text = if (salary.isNotBlank()) "💰 $salary" else ""
        } else {
            binding.layoutOverlay.visibility = View.GONE
        }
    }

    private fun createOverlayBitmap(): Bitmap {
        val base = selectedImageBitmap ?: Bitmap.createBitmap(1080, 1080, Bitmap.Config.ARGB_8888)
        val result = base.copy(Bitmap.Config.ARGB_8888, true)
        val canvas = Canvas(result)
        val w = result.width.toFloat()
        val h = result.height.toFloat()

        val pos = binding.etPosition.text.toString().trim()
        val vessel = binding.etVesselType.text.toString().trim()
        val desc = binding.etDescription.text.toString().trim()
        val salary = binding.etSalary.text.toString().trim()
        val contact = binding.etContact.text.toString().trim()

        // Semi-transparent dark gradient at bottom
        val gradientPaint = Paint()
        gradientPaint.shader = LinearGradient(
            0f, h * 0.5f, 0f, h,
            Color.TRANSPARENT, Color.argb(200, 0, 0, 0),
            Shader.TileMode.CLAMP
        )
        canvas.drawRect(0f, h * 0.5f, w, h, gradientPaint)

        // UMAY logo text (top-left)
        val logoPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 42f
            typeface = Typeface.DEFAULT_BOLD
            alpha = 180
        }
        canvas.drawText("⚓ UMAY", 30f, 60f, logoPaint)

        // Main title (position + vessel)
        val titlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 64f
            typeface = Typeface.DEFAULT_BOLD
            setShadowLayer(6f, 2f, 2f, Color.BLACK)
        }
        val titleText = buildString {
            if (pos.isNotBlank()) append(pos.uppercase())
        }
        if (titleText.isNotBlank()) {
            canvas.drawText(titleText, 30f, h - 280f, titlePaint)
        }

        // Vessel type
        if (vessel.isNotBlank()) {
            val vesselPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.YELLOW
                textSize = 44f
                typeface = Typeface.DEFAULT_BOLD
                setShadowLayer(4f, 2f, 2f, Color.BLACK)
            }
            canvas.drawText("🚢 ${vessel.uppercase()}", 30f, h - 220f, vesselPaint)
        }

        // Salary
        if (salary.isNotBlank()) {
            val salaryPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.WHITE
                textSize = 38f
                typeface = Typeface.DEFAULT_BOLD
                setShadowLayer(4f, 2f, 2f, Color.BLACK)
            }
            canvas.drawText("💰 $salary", 30f, h - 165f, salaryPaint)
        }

        // Description
        if (desc.isNotBlank()) {
            val descPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.WHITE
                textSize = 32f
                alpha = 220
                setShadowLayer(3f, 1f, 1f, Color.BLACK)
            }
            val maxWidth = w - 60f
            val lines = wrapText(desc, descPaint, maxWidth)
            var yPos = h - 120f
            for (line in lines.take(3)) {
                canvas.drawText(line, 30f, yPos, descPaint)
                yPos += 40f
            }
        }

        // Contact (bottom)
        if (contact.isNotBlank()) {
            val contactPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.WHITE
                textSize = 30f
                typeface = Typeface.DEFAULT_BOLD
                setShadowLayer(3f, 1f, 1f, Color.BLACK)
            }
            canvas.drawText("📞 $contact", 30f, h - 40f, contactPaint)
        }

        // CREWINTEL watermark (bottom-right)
        val watermarkPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 24f
            alpha = 120
        }
        canvas.drawText("CREWINTEL", w - 200f, h - 15f, watermarkPaint)

        return result
    }

    private fun wrapText(text: String, paint: Paint, maxWidth: Float): List<String> {
        val words = text.split(" ")
        val lines = mutableListOf<String>()
        var currentLine = ""
        for (word in words) {
            val testLine = if (currentLine.isEmpty()) word else "$currentLine $word"
            if (paint.measureText(testLine) <= maxWidth) {
                currentLine = testLine
            } else {
                if (currentLine.isNotBlank()) lines.add(currentLine)
                currentLine = word
            }
        }
        if (currentLine.isNotBlank()) lines.add(currentLine)
        return lines
    }

    private fun shareWithOverlay(targetPackage: String?) {
        val pos = binding.etPosition.text.toString().trim()
        if (pos.isBlank()) {
            Toast.makeText(this, "Lütfen pozisyon girin", Toast.LENGTH_SHORT).show()
            return
        }

        val overlayBitmap = createOverlayBitmap()

        // Save bitmap to cache
        val file = File(cacheDir, "job_post_${System.currentTimeMillis()}.jpg")
        FileOutputStream(file).use { out ->
            overlayBitmap.compress(Bitmap.CompressFormat.JPEG, 95, out)
        }

        val uri = FileProvider.getUriForFile(
            this,
            "${packageName}.fileprovider",
            file
        )

        val text = buildPostText()

        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "image/*"
            putExtra(Intent.EXTRA_STREAM, uri)
            // Text removed — overlay text is drawn on image via Canvas
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            if (targetPackage != null) setPackage(targetPackage)
        }

        try {
            startActivity(Intent.createChooser(intent, "İlanı paylaş"))
        } catch (e: Exception) {
            Toast.makeText(this, "Uygulama bulunamadı", Toast.LENGTH_SHORT).show()
        }
    }

    private fun buildPostText(): String {
        val pos = binding.etPosition.text.toString().trim()
        val vessel = binding.etVesselType.text.toString().trim()
        val desc = binding.etDescription.text.toString().trim()
        val salary = binding.etSalary.text.toString().trim()
        val contact = binding.etContact.text.toString().trim()

        val sb = StringBuilder()
        sb.appendLine("⚓ İŞ İLANI")
        if (pos.isNotBlank()) sb.appendLine("📋 $pos")
        if (vessel.isNotBlank()) sb.appendLine("🚢 $vessel")
        if (salary.isNotBlank()) sb.appendLine("💰 $salary")
        if (contact.isNotBlank()) sb.appendLine("📞 $contact")
        return sb.toString()
    }
}
