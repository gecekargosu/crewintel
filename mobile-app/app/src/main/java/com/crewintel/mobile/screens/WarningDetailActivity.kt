package com.crewintel.mobile.screens

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityWarningDetailBinding
import com.crewintel.mobile.models.Document
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class WarningDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityWarningDetailBinding
    private lateinit var prefs: PrefsManager
    private val adapter = WarningDocAdapter()

    companion object {
        const val EXTRA_FILTER_TYPE = "filter_type"
        const val EXTRA_TITLE = "title"
        const val FILTER_EXPIRED = "expired"
        const val FILTER_URGENT = "urgent"
        const val FILTER_APPROACHING = "approaching"
        const val FILTER_UNMATCHED = "unmatched"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityWarningDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = PrefsManager(this)

        val filterType = intent.getStringExtra(EXTRA_FILTER_TYPE) ?: FILTER_EXPIRED
        val title = intent.getStringExtra(EXTRA_TITLE) ?: "Uyarı Detayları"

        binding.tvTitle.text = title
        binding.btnBack.setOnClickListener { finish() }
        binding.rvDocuments.layoutManager = LinearLayoutManager(this)
        binding.rvDocuments.adapter = adapter

        loadDocuments(filterType)
    }

    private fun loadDocuments(filterType: String) {
        binding.progressBar.visibility = android.view.View.VISIBLE
        binding.tvEmpty.visibility = android.view.View.GONE

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getDocuments(matchStatus = filterType)
                if (response.isSuccessful) {
                    val docs = response.body() ?: emptyList()
                    if (docs.isEmpty()) {
                        binding.tvEmpty.visibility = android.view.View.VISIBLE
                        binding.tvEmpty.text = "Bu kategoride belge bulunamadı"
                    } else {
                        adapter.submitList(docs)
                        binding.tvCount.text = "${docs.size} belge"
                    }
                } else {
                    // Try alternative: fetch all and filter client-side
                    val allDocs = api.getDocuments()
                    if (allDocs.isSuccessful) {
                        val docs = allDocs.body() ?: emptyList()
                        val filtered = when (filterType) {
                            FILTER_EXPIRED -> docs.filter { it.expiryStatus == "expired" || it.matchStatus == "expired" }
                            FILTER_URGENT -> docs.filter { it.expiryStatus == "urgent" }
                            FILTER_APPROACHING -> docs.filter { it.expiryStatus == "approaching" }
                            FILTER_UNMATCHED -> docs.filter { it.matchStatus == "unmatched" }
                            else -> docs
                        }
                        if (filtered.isEmpty()) {
                            binding.tvEmpty.visibility = android.view.View.VISIBLE
                            binding.tvEmpty.text = "Bu kategoride belge bulunamadı"
                        } else {
                            adapter.submitList(filtered)
                            binding.tvCount.text = "${filtered.size} belge"
                        }
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@WarningDetailActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = android.view.View.GONE
            }
        }
    }
}

class WarningDocAdapter : androidx.recyclerview.widget.ListAdapter<Document, WarningDocAdapter.ViewHolder>(
    object : androidx.recyclerview.widget.DiffUtil.ItemCallback<Document>() {
        override fun areItemsTheSame(old: Document, new: Document) = old.id == new.id
        override fun areContentsTheSame(old: Document, new: Document) = old == new
    }
) {

    class ViewHolder(val binding: com.crewintel.mobile.databinding.ItemWarningDocBinding) :
        androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
        val binding = com.crewintel.mobile.databinding.ItemWarningDocBinding.inflate(
            android.view.LayoutInflater.from(parent.context), parent, false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val doc = getItem(position)
        holder.binding.tvDocName.text = doc.originalFilename
        holder.binding.tvDocType.text = doc.documentType.uppercase()
        holder.binding.tvDocStatus.text = doc.matchStatus

        // Status color
        val color = when {
            doc.matchStatus == "unmatched" -> 0xFFEF4444.toInt() // Red
            doc.expiryStatus == "expired" -> 0xFFEF4444.toInt() // Red
            doc.expiryStatus == "urgent" -> 0xFFF97316.toInt() // Orange
            doc.expiryStatus == "approaching" -> 0xFFEAB308.toInt() // Yellow
            doc.matchStatus == "matched" -> 0xFF22C55E.toInt() // Green
            else -> 0xFF6B7280.toInt() // Gray
        }
        holder.binding.tvDocStatus.setTextColor(color)

        // Expiry date
        if (doc.expiryDate != null) {
            holder.binding.tvExpiry.text = "Bitiş: ${doc.expiryDate}"
            holder.binding.tvExpiry.visibility = android.view.View.VISIBLE
        } else {
            holder.binding.tvExpiry.visibility = android.view.View.GONE
        }

        // Click to open crew detail
        holder.itemView.setOnClickListener {
            if (doc.crewMemberId != null) {
                val intent = Intent(holder.itemView.context, CrewDetailActivity::class.java)
                intent.putExtra("crew_id", doc.crewMemberId)
                holder.itemView.context.startActivity(intent)
            }
        }
    }
}
