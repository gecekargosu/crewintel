package com.crewintel.mobile.screens

import android.content.Intent
import android.net.Uri
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
import com.crewintel.mobile.databinding.ActivityCrewDetailBinding
import com.crewintel.mobile.models.Document
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class CrewDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCrewDetailBinding
    private lateinit var prefs: PrefsManager
    private var crewId = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCrewDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = PrefsManager(this)
        ApiClient.init(this)
        crewId = intent.getIntExtra("crew_id", -1)
        val crewName = intent.getStringExtra("crew_name") ?: ""

        binding.toolbar.title = crewName
        binding.toolbar.setNavigationOnClickListener { finish() }

        loadDetail()
    }

    private fun loadDetail() {
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)

                // Crew detail
                val crewResp = api.getCrewDetail(crewId)
                if (crewResp.isSuccessful) {
                    val crew = crewResp.body()!!
                    binding.tvAvatar.text = "${crew.firstName.firstOrNull() ?: ""}${crew.lastName.firstOrNull() ?: ""}"
                    binding.tvName.text = "${crew.firstName} ${crew.lastName}"
                    binding.tvPosition.text = "${crew.position ?: "?"} · ${crew.rank ?: "?"}"

                    val info = buildString {
                        appendLine("Pozisyon: ${crew.position ?: "—"}")
                        appendLine("Rütbe: ${crew.rank ?: "—"}")
                        appendLine("Uyruk: ${crew.nationality ?: "—"}")
                        appendLine("Durum: ${crew.status}")
                        appendLine("E-posta: ${crew.email ?: "—"}")
                        appendLine("Telefon: ${crew.phone ?: "—"}")
                        appendLine("Deneyim: ${crew.experienceYears ?: "—"} yıl")
                        appendLine("Müsaitlik: ${crew.availability ?: "—"}")
                    }
                    binding.tvInfo.text = info

                    // WhatsApp button
                    crew.phone?.let { phone ->
                        binding.btnWhatsApp.setOnClickListener {
                            val cleanPhone = phone.replace(Regex("[^0-9]"), "")
                            val msg = Uri.encode("Merhaba ${crew.firstName}, UMAY Admin'den bilgilendirme.")
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://wa.me/$cleanPhone?text=$msg"))
                            startActivity(intent)
                        }
                    } ?: run { binding.btnWhatsApp.isEnabled = false }

                    // Email button
                    binding.btnEmail.setOnClickListener {
                        val emailIntent = Intent(Intent.ACTION_SENDTO).apply {
                            data = Uri.parse("mailto:${crew.email}")
                            putExtra(Intent.EXTRA_SUBJECT, "UMAY Admin Bildirim")
                        }
                        try { startActivity(emailIntent) }
                        catch (_: Exception) { Toast.makeText(this@CrewDetailActivity, "E-posta uygulaması bulunamadı", Toast.LENGTH_SHORT).show() }
                    }

                    // Action buttons
                    binding.btnWhatsApp.visibility = if (crew.phone != null) View.VISIBLE else View.GONE
                    binding.btnEmail.visibility = if (crew.email != null) View.VISIBLE else View.GONE
                }

                // Documents
                val docResp = api.getDocuments(crewId = crewId)
                if (docResp.isSuccessful) {
                    val docs = docResp.body() ?: emptyList()
                    binding.rvDocuments.layoutManager = LinearLayoutManager(this@CrewDetailActivity)
                    binding.rvDocuments.adapter = DocAdapter(docs) { doc ->
                        showDocumentInfo(doc)
                    }
                }

            } catch (e: Exception) {
                Toast.makeText(this@CrewDetailActivity, "Hata: ${e.localizedMessage}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun showDocumentInfo(doc: Document) {
        val statusEmoji = when (doc.expiryStatus) {
            "expired" -> "🔴 Süresi dolmuş"
            "urgent" -> "🟠 Acil"
            "approaching" -> "🟡 Yaklaşıyor"
            "valid" -> "🟢 Geçerli"
            else -> "⚪ Belirsiz"
        }
        val matchEmoji = when (doc.matchStatus) {
            "matched" -> "✅ Eşleşmiş"
            "review_required" -> "⚠️ İnceleme gerekli"
            "conflict" -> "❌ Çelişki"
            "unmatched" -> "⚪ Eşleşmemiş"
            else -> "🔄 ${doc.matchStatus}"
        }

        AlertDialog.Builder(this)
            .setTitle(doc.originalFilename)
            .setMessage(buildString {
                appendLine("Tip: ${doc.documentType}")
                appendLine("Durum: $statusEmoji")
                appendLine("Eşleşme: $matchEmoji")
                appendLine("Güven: %${doc.matchConfidence ?: 0}")
                if (doc.expiryDate != null) appendLine("Bitiş: ${doc.expiryDate}")
            })
            .setPositiveButton("Tamam", null)
            .show()
    }

    class DocAdapter(
        private val items: List<Document>,
        private val onClick: (Document) -> Unit
    ) : RecyclerView.Adapter<DocAdapter.VH>() {

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val tvType: TextView = view.findViewById(R.id.tvDocType) ?: view.findViewById(android.R.id.text1)
            val tvName: TextView = view.findViewById(R.id.tvDocName) ?: view.findViewById(android.R.id.text2)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val view = LayoutInflater.from(parent.context).inflate(R.layout.item_document, parent, false)
            return VH(view)
        }

        override fun onBindViewHolder(holder: VH, position: Int) {
            val doc = items[position]
            val emoji = when (doc.documentType) {
                "passport" -> "📘"
                "medical" -> "🏥"
                "stcw" -> "📜"
                "cv" -> "📋"
                "contract" -> "📝"
                "seaman_book" -> "⚓"
                "goc" -> "📡"
                else -> "📄"
            }
            holder.tvType.text = "$emoji ${doc.documentType}"
            holder.tvName.text = doc.originalFilename
            holder.itemView.setOnClickListener { onClick(doc) }
        }

        override fun getItemCount() = items.size
    }
}
