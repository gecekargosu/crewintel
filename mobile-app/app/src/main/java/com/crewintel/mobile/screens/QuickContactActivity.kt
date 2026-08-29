package com.crewintel.mobile.screens

import android.content.Intent
import android.net.Uri
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
import com.crewintel.mobile.databinding.ActivityQuickContactBinding
import com.crewintel.mobile.databinding.ItemCrewContactBinding
import com.crewintel.mobile.models.CrewMember
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class QuickContactActivity : AppCompatActivity() {

    private lateinit var binding: ActivityQuickContactBinding
    private lateinit var prefs: PrefsManager
    private val adapter = CrewContactAdapter()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityQuickContactBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.rvCrew.layoutManager = LinearLayoutManager(this)
        binding.rvCrew.adapter = adapter

        loadCrew()
    }

    private fun loadCrew() {
        binding.progressBar.visibility = View.VISIBLE
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getCrewList()
                if (response.isSuccessful) {
                    val crew = response.body() ?: emptyList()
                    adapter.submitList(crew)
                }
            } catch (e: Exception) {
                Toast.makeText(this@QuickContactActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
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
        val crew = getItem(position)
        holder.binding.tvName.text = "${crew.firstName} ${crew.lastName}"
        holder.binding.tvPosition.text = crew.position ?: crew.rank ?: "Personel"
        holder.binding.tvPhone.text = crew.phone ?: "Telefon yok"

        // WhatsApp
        holder.binding.btnWhatsApp.setOnClickListener {
            if (crew.phone.isNullOrBlank()) {
                Toast.makeText(holder.itemView.context, "Telefon numarası yok", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val phone = crew.phone.replace("[^0-9+]", "")
            val intent = Intent(Intent.ACTION_VIEW).apply {
                data = Uri.parse("whatsapp://send?phone=$phone&text=Merhaba ${crew.firstName}")
            }
            try {
                holder.itemView.context.startActivity(intent)
            } catch (e: Exception) {
                Toast.makeText(holder.itemView.context, "WhatsApp yüklü değil", Toast.LENGTH_SHORT).show()
            }
        }

        // Phone call
        holder.binding.btnCall.setOnClickListener {
            if (crew.phone.isNullOrBlank()) {
                Toast.makeText(holder.itemView.context, "Telefon numarası yok", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:${crew.phone}"))
            holder.itemView.context.startActivity(intent)
        }

        // SMS
        holder.binding.btnMessage.setOnClickListener {
            if (crew.phone.isNullOrBlank()) {
                Toast.makeText(holder.itemView.context, "Telefon numarası yok", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val intent = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:${crew.phone}"))
            holder.itemView.context.startActivity(intent)
        }
    }
}
