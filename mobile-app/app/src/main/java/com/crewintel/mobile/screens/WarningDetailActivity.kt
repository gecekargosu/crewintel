package com.crewintel.mobile.screens

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.View
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
        ApiClient.init(this)

        val filterType = intent.getStringExtra(EXTRA_FILTER_TYPE) ?: FILTER_EXPIRED
        val title = intent.getStringExtra(EXTRA_TITLE) ?: "Uyarı Detayları"

        binding.tvTitle.text = title
        binding.btnBack.setOnClickListener { finish() }
        binding.rvDocuments.layoutManager = LinearLayoutManager(this)
        binding.rvDocuments.adapter = adapter

        loadDocuments(filterType)
    }

    private fun loadDocuments(filterType: String) {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvEmpty.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)

                // Fetch ALL documents and filter client-side for reliability
                val response = api.getDocuments()
                Log.d("WarningDetail", "API response code: ${response.code()}, body size: ${response.body()?.size}")

                if (response.isSuccessful) {
                    val allDocs = response.body() ?: emptyList()
                    Log.d("WarningDetail", "Total docs: ${allDocs.size}, filter: $filterType")

                    val filtered = when (filterType) {
                        FILTER_EXPIRED -> allDocs.filter {
                            it.expiryStatus == "expired"
                        }
                        FILTER_URGENT -> allDocs.filter {
                            it.expiryStatus == "urgent"
                        }
                        FILTER_APPROACHING -> allDocs.filter {
                            it.expiryStatus == "approaching"
                        }
                        FILTER_UNMATCHED -> allDocs.filter {
                            it.matchStatus == "unmatched"
                        }
                        else -> allDocs
                    }

                    Log.d("WarningDetail", "Filtered docs: ${filtered.size}")

                    if (filtered.isEmpty()) {
                        binding.tvEmpty.visibility = View.VISIBLE
                        binding.tvEmpty.text = when (filterType) {
                            FILTER_EXPIRED -> "✅ Süresi dolmuş belge bulunmuyor"
                            FILTER_URGENT -> "✅ Acil belge bulunmuyor"
                            FILTER_APPROACHING -> "✅ Yaklaşan belge bulunmuyor"
                            FILTER_UNMATCHED -> "✅ Eşleşmemiş belge bulunmuyor"
                            else -> "Bu kategoride belge bulunamadı"
                        }
                    } else {
                        adapter.submitList(filtered)
                        binding.tvCount.text = "${filtered.size} belge"
                        binding.tvCount.visibility = View.VISIBLE
                    }
                } else {
                    Log.e("WarningDetail", "API error: ${response.code()} - ${response.errorBody()?.string()}")
                    binding.tvEmpty.visibility = View.VISIBLE
                    binding.tvEmpty.text = "Sunucu hatası: ${response.code()}"
                }
            } catch (e: Exception) {
                Log.e("WarningDetail", "Exception: ${e.message}", e)
                Toast.makeText(this@WarningDetailActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
                binding.tvEmpty.visibility = View.VISIBLE
                binding.tvEmpty.text = "Bağlantı hatası: ${e.message}"
            } finally {
                binding.progressBar.visibility = View.GONE
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
            doc.matchStatus == "unmatched" -> 0xFFEF4444.toInt()
            doc.expiryStatus == "expired" -> 0xFFEF4444.toInt()
            doc.expiryStatus == "urgent" -> 0xFFF97316.toInt()
            doc.expiryStatus == "approaching" -> 0xFFEAB308.toInt()
            doc.matchStatus == "matched" -> 0xFF22C55E.toInt()
            else -> 0xFF6B7280.toInt()
        }
        holder.binding.tvDocStatus.setTextColor(color)

        if (doc.expiryDate != null) {
            holder.binding.tvExpiry.text = "Bitiş: ${doc.expiryDate}"
            holder.binding.tvExpiry.visibility = View.VISIBLE
        } else {
            holder.binding.tvExpiry.visibility = View.GONE
        }

        holder.itemView.setOnClickListener {
            if (doc.crewMemberId != null) {
                val intent = Intent(holder.itemView.context, CrewDetailActivity::class.java)
                intent.putExtra("crew_id", doc.crewMemberId)
                holder.itemView.context.startActivity(intent)
            }
        }
    }
}
