package com.crewintel.mobile.screens

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityQuickContactBinding
import com.crewintel.mobile.databinding.ItemCrewContactBinding
import com.crewintel.mobile.models.CrewMember
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class QuickContactActivity : AppCompatActivity() {

    private lateinit var binding: ActivityQuickContactBinding
    private lateinit var prefs: PrefsManager
    private val adapter = CrewContactAdapter()
    private var allCrew = listOf<CrewMember>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityQuickContactBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.rvCrew.layoutManager = LinearLayoutManager(this)
        binding.rvCrew.adapter = adapter

        binding.etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                filterCrew(s?.toString() ?: "")
            }
            override fun afterTextChanged(s: Editable?) {}
        })

        loadCrew()
    }

    private fun loadCrew() {
        binding.progressBar.visibility = View.VISIBLE
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getCrewList()
                if (response.isSuccessful) {
                    allCrew = response.body() ?: emptyList()
                    adapter.submitList(allCrew)
                }
            } catch (e: Exception) {
                Toast.makeText(this@QuickContactActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun filterCrew(query: String) {
        if (query.isBlank()) {
            adapter.submitList(allCrew)
            return
        }
        val lower = query.lowercase()
        val filtered = allCrew.filter {
            it.firstName.lowercase().contains(lower) ||
            it.lastName.lowercase().contains(lower) ||
            "${it.firstName} ${it.lastName}".lowercase().contains(lower) ||
            (it.position?.lowercase()?.contains(lower) == true) ||
            (it.rank?.lowercase()?.contains(lower) == true)
        }
        adapter.submitList(filtered)
    }
}

class CrewContactAdapter : androidx.recyclerview.widget.ListAdapter<CrewMember, CrewContactAdapter.ViewHolder>(
    object : androidx.recyclerview.widget.DiffUtil.ItemCallback<CrewMember>() {
        override fun areItemsTheSame(old: CrewMember, new: CrewMember) = old.id == new.id
        override fun areContentsTheSame(old: CrewMember, new: CrewMember) = old == new
    }
) {
    class ViewHolder(val binding: ItemCrewContactBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemCrewContactBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val crew = getItem(holder.adapterPosition)
        val ctx = holder.itemView.context
        holder.binding.tvName.text = "${crew.firstName} ${crew.lastName}"
        holder.binding.tvPosition.text = crew.position ?: crew.rank ?: "Personel"
        holder.binding.tvPhone.text = crew.phone ?: "Telefon yok"

        val phone = crew.phone?.replace("[^0-9+]", "") ?: ""

        // WhatsApp
        holder.binding.btnWhatsApp.setOnClickListener {
            if (phone.isBlank()) { Toast.makeText(ctx, "Telefon yok", Toast.LENGTH_SHORT).show(); return@setOnClickListener }
            try {
                ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("whatsapp://send?phone=$phone&text=Merhaba ${crew.firstName}")))
            } catch (_: Exception) { Toast.makeText(ctx, "WhatsApp yüklü değil", Toast.LENGTH_SHORT).show() }
        }

        // Telegram
        holder.binding.btnTelegram.setOnClickListener {
            try {
                ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("tg://resolve?domain=${crew.firstName.lowercase()}")))
            } catch (_: Exception) {
                // Fallback: open Telegram web
                try {
                    ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/")))
                } catch (_: Exception) { Toast.makeText(ctx, "Telegram yüklü değil", Toast.LENGTH_SHORT).show() }
            }
        }

        // Call
        holder.binding.btnCall.setOnClickListener {
            if (phone.isBlank()) { Toast.makeText(ctx, "Telefon yok", Toast.LENGTH_SHORT).show(); return@setOnClickListener }
            ctx.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:$phone")))
        }

        // SMS
        holder.binding.btnSMS.setOnClickListener {
            if (phone.isBlank()) { Toast.makeText(ctx, "Telefon yok", Toast.LENGTH_SHORT).show(); return@setOnClickListener }
            ctx.startActivity(Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:$phone")))
        }

        // Email
        holder.binding.btnEmail.setOnClickListener {
            if (crew.email.isNullOrBlank()) { Toast.makeText(ctx, "E-posta yok", Toast.LENGTH_SHORT).show(); return@setOnClickListener }
            ctx.startActivity(Intent(Intent.ACTION_SENDTO, Uri.parse("mailto:${crew.email}")))
        }
    }
}
