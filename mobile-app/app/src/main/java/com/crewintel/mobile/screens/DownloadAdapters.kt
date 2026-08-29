package com.crewintel.mobile.screens

import android.graphics.BitmapFactory
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.R
import kotlinx.coroutines.*
import java.net.URL

// ── Active Download Item ─────────────────────────────────────────────────────
data class ActiveDownload(
    val taskId: String,
    val title: String,
    val platform: String,
    val thumbnail: String,
    val startedAt: String,
)

class ActiveDownloadAdapter(
    private val items: MutableList<ActiveDownload> = mutableListOf()
) : RecyclerView.Adapter<ActiveDownloadAdapter.VH>() {

    class VH(view: View) : RecyclerView.ViewHolder(view) {
        val ivThumb: ImageView = view.findViewById(R.id.ivThumb)
        val tvTitle: TextView = view.findViewById(R.id.tvTitle)
        val tvStatus: TextView = view.findViewById(R.id.tvStatus)
        val progressBar: ProgressBar = view.findViewById(R.id.progressBar)
        val tvIcon: TextView = view.findViewById(R.id.tvIcon)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_active_download, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val item = items[position]
        holder.tvTitle.text = item.title.ifEmpty { "Indiriliyor..." }
        holder.tvStatus.text = "${getPlatformIcon(item.platform)} Indiriliyor..."
        holder.tvIcon.text = "⏳"
        holder.progressBar.isIndeterminate = true

        if (item.thumbnail.isNotEmpty()) {
            loadThumb(holder.ivThumb, item.thumbnail)
        }
    }

    override fun getItemCount() = items.size

    fun updateList(newItems: List<ActiveDownload>) {
        items.clear()
        items.addAll(newItems)
        notifyDataSetChanged()
    }

    private fun loadThumb(iv: ImageView, url: String) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val bitmap = BitmapFactory.decodeStream(URL(url).openStream())
                withContext(Dispatchers.Main) { iv.setImageBitmap(bitmap) }
            } catch (_: Exception) {}
        }
    }

    private fun getPlatformIcon(platform: String): String = when (platform) {
        "youtube" -> "▶️"
        "instagram" -> "📷"
        "tiktok" -> "🎵"
        "facebook" -> "📘"
        "pinterest" -> "📌"
        "twitter" -> "🐦"
        else -> "🎬"
    }
}

// ── Download History Item ────────────────────────────────────────────────────
data class HistoryItem(
    val taskId: String,
    val title: String,
    val platform: String,
    val fileName: String,
    val fileSize: Long,
    val thumbnail: String,
    val downloadedAt: String,
)

class DownloadHistoryAdapter(
    private val items: MutableList<HistoryItem> = mutableListOf(),
    private val onPlay: (HistoryItem) -> Unit = {}
) : RecyclerView.Adapter<DownloadHistoryAdapter.VH>() {

    class VH(view: View) : RecyclerView.ViewHolder(view) {
        val tvPlatformIcon: TextView = view.findViewById(R.id.tvPlatformIcon)
        val tvTitle: TextView = view.findViewById(R.id.tvTitle)
        val tvSize: TextView = view.findViewById(R.id.tvSize)
        val btnPlay: ImageView = view.findViewById(R.id.btnPlay)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_download_history, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val item = items[position]
        holder.tvPlatformIcon.text = getPlatformIcon(item.platform)
        holder.tvTitle.text = item.title.ifEmpty { item.fileName }
        holder.tvSize.text = formatSize(item.fileSize)
        holder.btnPlay.setOnClickListener { onPlay(item) }
    }

    override fun getItemCount() = items.size

    fun updateList(newItems: List<HistoryItem>) {
        items.clear()
        items.addAll(newItems)
        notifyDataSetChanged()
    }

    private fun formatSize(bytes: Long): String = when {
        bytes >= 1048576 -> String.format("%.1f MB", bytes / 1048576.0)
        bytes >= 1024 -> String.format("%.0f KB", bytes / 1024.0)
        else -> "$bytes B"
    }

    private fun getPlatformIcon(platform: String): String = when (platform) {
        "youtube" -> "▶️"
        "instagram" -> "📷"
        "tiktok" -> "🎵"
        "facebook" -> "📘"
        "pinterest" -> "📌"
        "twitter" -> "🐦"
        else -> "🎬"
    }
}
