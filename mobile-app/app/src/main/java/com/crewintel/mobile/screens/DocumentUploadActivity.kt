package com.crewintel.mobile.screens

import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityDocUploadBinding
import com.crewintel.mobile.databinding.ItemSelectedFileBinding
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

class DocumentUploadActivity : AppCompatActivity() {

    private lateinit var binding: ActivityDocUploadBinding
    private lateinit var prefs: PrefsManager
    private val selectedFiles = mutableListOf<FileItem>()
    private val fileAdapter = SelectedFileAdapter(selectedFiles) { updateUI() }

    private val filePicker = registerForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris: List<Uri> ->
        for (uri in uris) {
            val item = uriToFileItem(uri)
            if (item != null && selectedFiles.none { it.name == item.name }) {
                selectedFiles.add(item)
            }
        }
        updateUI()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDocUploadBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.cardUploadArea.setOnClickListener { openFilePicker() }
        binding.btnUpload.setOnClickListener { uploadFiles() }

        binding.rvFiles.layoutManager = LinearLayoutManager(this)
        binding.rvFiles.adapter = fileAdapter
    }

    private fun openFilePicker() {
        filePicker.launch(arrayOf(
            "application/pdf",
            "image/*",
            "text/plain"
        ))
    }

    private fun uriToFileItem(uri: Uri): FileItem? {
        return try {
            val inputStream = contentResolver.openInputStream(uri) ?: return null
            val fileName = getFileName(uri)
            val tempFile = File(cacheDir, "upload_${System.currentTimeMillis()}_$fileName")
            tempFile.outputStream().use { output -> inputStream.copyTo(output) }
            inputStream.close()
            FileItem(file = tempFile, name = fileName, size = tempFile.length())
        } catch (e: Exception) {
            Toast.makeText(this, "Dosya okunamadı", Toast.LENGTH_SHORT).show()
            null
        }
    }

    private fun getFileName(uri: Uri): String {
        var name = "unknown_file"
        contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            if (cursor.moveToFirst() && nameIndex >= 0) {
                name = cursor.getString(nameIndex)
            }
        }
        return name
    }

    private fun updateUI() {
        binding.tvSelectedCount.text = "Seçilen dosya: ${selectedFiles.size}"
        binding.tvSelectedCount.visibility = if (selectedFiles.isNotEmpty()) View.VISIBLE else View.GONE
        binding.btnUpload.isEnabled = selectedFiles.isNotEmpty()
        fileAdapter.notifyDataSetChanged()
    }

    private fun uploadFiles() {
        if (selectedFiles.isEmpty()) return

        binding.progressBar.visibility = View.VISIBLE
        binding.btnUpload.isEnabled = false
        binding.tvStatus.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val parts = selectedFiles.map { item ->
                    val requestBody = item.file.asRequestBody("application/octet-stream".toMediaTypeOrNull())
                    MultipartBody.Part.createFormData("files", item.name, requestBody)
                }

                val response = api.batchUpload(parts)
                if (response.isSuccessful) {
                    val result = response.body()
                    val total = result?.total ?: 0
                    val dup = result?.duplicate ?: 0
                    val fail = result?.failed ?: 0
                    val msg = "✅ $total belge yüklendi" +
                            if (dup > 0) " ($dup tekrar)" else "" +
                            if (fail > 0) " ($fail hatalı)" else ""
                    binding.tvStatus.visibility = View.VISIBLE
                    binding.tvStatus.text = msg
                    binding.tvStatus.setTextColor(0xFF16a34a.toInt())
                    selectedFiles.clear()
                    updateUI()
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
                binding.btnUpload.isEnabled = selectedFiles.isNotEmpty()
            }
        }
    }

    data class FileItem(val file: File, val name: String, val size: Long)
}

class SelectedFileAdapter(
    private val items: List<DocumentUploadActivity.FileItem>,
    private val onUpdate: () -> Unit
) : RecyclerView.Adapter<SelectedFileAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemSelectedFileBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemSelectedFileBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = items[position]
        val ext = item.name.substringAfterLast(delimiter = '.', missingDelimiterValue = "").uppercase()
        val icon = when (ext) {
            "PDF" -> "📄"
            "JPG", "JPEG", "PNG", "GIF" -> "🖼️"
            "TXT" -> "📝"
            else -> "📎"
        }
        val sizeKB = item.size / 1024
        val sizeStr = if (sizeKB > 1024) "${sizeKB / 1024} MB" else "$sizeKB KB"

        holder.binding.tvFileName.text = "$icon ${item.name}"
        holder.binding.tvFileSize.text = sizeStr
        holder.binding.btnRemove.setOnClickListener {
            val pos = holder.adapterPosition
            if (pos != RecyclerView.NO_POSITION) {
                (items as MutableList).removeAt(pos)
                notifyItemRemoved(pos)
                onUpdate()
            }
        }
    }
}
