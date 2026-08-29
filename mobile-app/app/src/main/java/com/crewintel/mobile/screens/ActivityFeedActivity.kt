package com.crewintel.mobile.screens

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityFeedBinding
import com.crewintel.mobile.databinding.ItemFeedBinding
import com.crewintel.mobile.models.AuditLog
import com.crewintel.mobile.models.Notification
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class ActivityFeedActivity : AppCompatActivity() {

    private lateinit var binding: ActivityFeedBinding
    private lateinit var prefs: PrefsManager
    private val adapter = FeedAdapter()
    private var currentTab = "all"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityFeedBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)
        ApiClient.init(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.rvFeed.layoutManager = LinearLayoutManager(this)
        binding.rvFeed.adapter = adapter

        binding.tabAll.setOnClickListener { switchTab("all") }
        binding.tabAlerts.setOnClickListener { switchTab("alerts") }
        binding.tabActivity.setOnClickListener { switchTab("activity") }

        loadFeed()
    }

    private fun switchTab(tab: String) {
        currentTab = tab
        val active = 0xFF1e3a5f.toInt()
        val inactive = 0xFF64748b.toInt()
        val bgActive = 0xFFe2e8f0.toInt()
        val bgInactive = 0x00000000
        binding.tabAll.setTextColor(if (tab == "all") active else inactive)
        binding.tabAll.setBackgroundColor(if (tab == "all") bgActive else bgInactive)
        binding.tabAlerts.setTextColor(if (tab == "alerts") active else inactive)
        binding.tabAlerts.setBackgroundColor(if (tab == "alerts") bgActive else bgInactive)
        binding.tabActivity.setTextColor(if (tab == "activity") active else inactive)
        binding.tabActivity.setBackgroundColor(if (tab == "activity") bgActive else bgInactive)
        loadFeed()
    }

    private fun loadFeed() {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvEmpty.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val items = mutableListOf<FeedItem>()

                if (currentTab == "all" || currentTab == "activity") {
                    try {
                        val response = api.getAuditLogs()
                        if (response.isSuccessful) {
                            val logs = response.body() ?: emptyList()
                            for (log in logs) {
                                items.add(FeedItem(
                                    id = log.id,
                                    type = "audit",
                                    title = formatAction(log.action),
                                    message = log.details,
                                    icon = getAuditIcon(log.action),
                                    time = log.createdAt,
                                    entity = log.entityType,
                                    entityId = log.entityId
                                ))
                            }
                        }
                    } catch (_: Exception) {}
                }

                if (currentTab == "all" || currentTab == "alerts") {
                    try {
                        val response = api.getNotifications()
                        if (response.isSuccessful) {
                            val notifications = response.body() ?: emptyList()
                            for (notif in notifications) {
                                items.add(FeedItem(
                                    id = notif.id,
                                    type = "notification",
                                    title = notif.title,
                                    message = notif.message,
                                    icon = getNotifIcon(notif.type),
                                    time = notif.createdAt,
                                    entity = notif.type,
                                    entityId = null,
                                    isRead = notif.read
                                ))
                            }
                        }
                    } catch (_: Exception) {}
                }

                items.sortByDescending { it.time }

                if (items.isEmpty()) {
                    binding.tvEmpty.visibility = View.VISIBLE
                } else {
                    adapter.submitList(items)
                }
            } catch (e: Exception) {
                Toast.makeText(this@ActivityFeedActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun formatAction(action: String): String = when {
        action.contains("created") || action.contains("added") -> "Yeni Ekleme"
        action.contains("updated") -> "Guncelleme"
        action.contains("deleted") -> "Silme"
        action.contains("uploaded") -> "Yukleme"
        action.contains("email") -> "E-posta"
        action.contains("login") -> "Giris"
        action.contains("matched") -> "Eslestirme"
        else -> action
    }

    private fun getAuditIcon(action: String): String = when {
        action.contains("created") || action.contains("added") -> "+"
        action.contains("updated") -> "E"
        action.contains("deleted") -> "X"
        action.contains("uploaded") -> "^"
        action.contains("email") -> "@"
        action.contains("login") -> ">"
        else -> "*"
    }

    private fun getNotifIcon(type: String): String = when (type) {
        "email" -> "@"
        "whatsapp" -> "W"
        "push" -> "!"
        else -> "!"
    }

    data class FeedItem(
        val id: Int,
        val type: String,
        val title: String,
        val message: String,
        val icon: String,
        val time: String,
        val entity: String = "",
        val entityId: Int? = null,
        val isRead: Boolean = true
    )
}

class FeedAdapter : androidx.recyclerview.widget.ListAdapter<ActivityFeedActivity.FeedItem, FeedAdapter.ViewHolder>(
    object : androidx.recyclerview.widget.DiffUtil.ItemCallback<ActivityFeedActivity.FeedItem>() {
        override fun areItemsTheSame(old: ActivityFeedActivity.FeedItem, new: ActivityFeedActivity.FeedItem) = old.id == new.id && old.type == new.type
        override fun areContentsTheSame(old: ActivityFeedActivity.FeedItem, new: ActivityFeedActivity.FeedItem) = old == new
    }
) {
    class ViewHolder(val binding: ItemFeedBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemFeedBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = getItem(position)
        holder.binding.tvIcon.text = item.icon
        holder.binding.tvTitle.text = item.title
        holder.binding.tvMessage.text = item.message
        holder.binding.tvTime.text = formatTime(item.time)

        if (!item.isRead) {
            holder.binding.tvBadge.visibility = View.VISIBLE
            holder.binding.tvBadge.text = "YENI"
            holder.binding.tvBadge.setBackgroundColor(0xFFdc2626.toInt())
        } else {
            holder.binding.tvBadge.visibility = View.GONE
        }

        holder.itemView.setOnClickListener {
            if (item.entity == "crew_member" && item.entityId != null) {
                val intent = Intent(holder.itemView.context, CrewDetailActivity::class.java)
                intent.putExtra("crew_id", item.entityId)
                holder.itemView.context.startActivity(intent)
            }
        }
    }

    private fun formatTime(isoTime: String): String {
        if (isoTime.isBlank()) return ""
        return try {
            val clean = isoTime.replace("T", " ").substringBefore(".")
            if (clean.length > 16) clean.substring(5, 16) else clean
        } catch (_: Exception) { isoTime }
    }
}
