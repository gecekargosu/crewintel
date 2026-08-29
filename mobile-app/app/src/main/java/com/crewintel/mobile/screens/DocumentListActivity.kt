package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.R
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityDocumentsBinding
import com.crewintel.mobile.models.Document
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class DocumentListActivity : AppCompatActivity() {

    private lateinit var binding: ActivityDocumentsBinding
    private lateinit var prefs: PrefsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDocumentsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = PrefsManager(this)
        ApiClient.init(this)
        binding.toolbar.setNavigationOnClickListener { finish() }

        loadDocuments()
    }

    private fun loadDocuments() {
        binding.progressBar.visibility = View.VISIBLE
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getDocuments()
                if (response.isSuccessful) {
                    val docs = response.body() ?: emptyList()
                    binding.tvCount.text = "${docs.size} belge"

                    if (docs.isEmpty()) {
                        binding.tvEmpty.visibility = View.VISIBLE
                        binding.rvDocs.visibility = View.GONE
                    } else {
                        binding.tvEmpty.visibility = View.GONE
                        binding.rvDocs.visibility = View.VISIBLE
                        binding.rvDocs.layoutManager = LinearLayoutManager(this@DocumentListActivity)
                        binding.rvDocs.adapter = DocListAdapter(docs) { doc ->
                            showDocDetail(doc)
                        }
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@DocumentListActivity, "Hata: ${e.localizedMessage}", Toast.LENGTH_LONG).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun showDocDetail(doc: Document) {
        val emoji = when (doc.documentType) {
            "passport" -> "📘"; "medical" -> "🏥"; "stcw" -> "📜"
            "cv" -> "📋"; "contract" -> "📝"; "seaman_book" -> "⚓"; "goc" -> "📡"
            else -> "📄"
        }
        val statusText = when (doc.expiryStatus) {
            "expired" -> "🔴 Süresi dolmuş"; "urgent" -> "🟠 Acil"
            "approaching" -> "🟡 Yaklaşıyor"; "valid" -> "🟢 Geçerli"
            else -> "⚪ ${doc.expiryStatus}"
        }
        val matchText = when (doc.matchStatus) {
            "matched" -> "✅ Eşleşmiş"; "review_required" -> "⚠️ İnceleme"
            "conflict" -> "❌ Çelişki"; "unmatched" -> "⚪ Eşleşmemiş"
            else -> doc.matchStatus
        }

        AlertDialog.Builder(this)
            .setTitle("$emoji ${doc.originalFilename}")
            .setMessage(buildString {
                appendLine("Tip: ${doc.documentType}")
                appendLine("Durum: $statusText")
                appendLine("Eşleşme: $matchText")
                appendLine("Güven: %${doc.matchConfidence ?: 0}")
                if (doc.expiryDate != null) appendLine("Bitiş: ${doc.expiryDate}")
                if (doc.crewMemberId != null) appendLine("Personel ID: ${doc.crewMemberId}")
            })
            .setPositiveButton("Tamam", null)
            .show()
    }

    class DocListAdapter(
        private val items: List<Document>,
        private val onClick: (Document) -> Unit
    ) : RecyclerView.Adapter<DocListAdapter.VH>() {

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val tvType: TextView = view.findViewById(R.id.tvDocType)
            val tvName: TextView = view.findViewById(R.id.tvDocName)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val view = LayoutInflater.from(parent.context).inflate(R.layout.item_document, parent, false)
            return VH(view)
        }

        override fun onBindViewHolder(holder: VH, position: Int) {
            val doc = items[position]
            val emoji = when (doc.documentType) {
                "passport" -> "📘"; "medical" -> "🏥"; "stcw" -> "📜"
                "cv" -> "📋"; "contract" -> "📝"; "seaman_book" -> "⚓"; "goc" -> "📡"
                else -> "📄"
            }
            val matchIcon = when (doc.matchStatus) {
                "matched" -> "✅"; "review_required" -> "⚠️"; "conflict" -> "❌"
                else -> "⚪"
            }
            holder.tvType.text = "$emoji ${doc.documentType}"
            holder.tvName.text = "$matchIcon ${doc.originalFilename}"
            holder.itemView.setOnClickListener { onClick(doc) }
        }

        override fun getItemCount() = items.size
    }
}
