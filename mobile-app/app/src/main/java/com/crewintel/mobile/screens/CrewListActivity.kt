package com.crewintel.mobile.screens

import android.content.Intent
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.R
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityCrewListBinding
import com.crewintel.mobile.models.CrewMember
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class CrewListActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCrewListBinding
    private lateinit var prefs: PrefsManager
    private var allCrew = listOf<CrewMember>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCrewListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = PrefsManager(this)
        ApiClient.init(this)
        binding.toolbar.setNavigationOnClickListener { finish() }

        binding.etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) { filterList(s.toString()) }
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
                    binding.tvCount.text = "${allCrew.size} personel"
                    displayList(allCrew)
                }
            } catch (e: Exception) {
                binding.tvEmpty.text = "Bağlantı hatası: ${e.localizedMessage}"
                binding.tvEmpty.visibility = View.VISIBLE
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun filterList(query: String) {
        val filtered = allCrew.filter {
            it.firstName.contains(query, ignoreCase = true) ||
            it.lastName.contains(query, ignoreCase = true) ||
            it.position?.contains(query, ignoreCase = true) == true ||
            it.nationality?.contains(query, ignoreCase = true) == true
        }
        binding.tvCount.text = "${filtered.size} / ${allCrew.size} personel"
        displayList(filtered)
    }

    private fun displayList(crew: List<CrewMember>) {
        if (crew.isEmpty()) {
            binding.tvEmpty.visibility = View.VISIBLE
            binding.rvCrew.visibility = View.GONE
        } else {
            binding.tvEmpty.visibility = View.GONE
            binding.rvCrew.visibility = View.VISIBLE
            binding.rvCrew.layoutManager = LinearLayoutManager(this)
            binding.rvCrew.adapter = CrewAdapter(crew) { selected ->
                val intent = Intent(this, CrewDetailActivity::class.java)
                intent.putExtra("crew_id", selected.id)
                intent.putExtra("crew_name", "${selected.firstName} ${selected.lastName}")
                startActivity(intent)
            }
        }
    }

    class CrewAdapter(
        private val items: List<CrewMember>,
        private val onClick: (CrewMember) -> Unit
    ) : RecyclerView.Adapter<CrewAdapter.VH>() {

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val tvAvatar: TextView = view.findViewById(R.id.tvAvatar)
            val tvName: TextView = view.findViewById(R.id.tvName)
            val tvPosition: TextView = view.findViewById(R.id.tvPosition)
            val tvStatus: TextView = view.findViewById(R.id.tvStatus)
            val tvAvailability: TextView = view.findViewById(R.id.tvAvailability)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val view = LayoutInflater.from(parent.context).inflate(R.layout.item_crew, parent, false)
            return VH(view)
        }

        override fun onBindViewHolder(holder: VH, position: Int) {
            val crew = items[position]
            holder.tvAvatar.text = "${crew.firstName.firstOrNull() ?: ""}${crew.lastName.firstOrNull() ?: ""}"
            holder.tvName.text = "${crew.firstName} ${crew.lastName}"
            holder.tvPosition.text = "${crew.position ?: "?"} · ${crew.nationality ?: "?"}"

            // Status badge
            when (crew.status) {
                "active" -> {
                    holder.tvStatus.text = "AKTİF"
                    holder.tvStatus.setTextColor(0xFF16A34A.toInt())
                    holder.tvStatus.setBackgroundColor(0xFFDCFCE7.toInt())
                }
                else -> {
                    holder.tvStatus.text = crew.status?.uppercase() ?: "?"
                    holder.tvStatus.setTextColor(0xFF64748B.toInt())
                    holder.tvStatus.setBackgroundColor(0xFFF1F5F9.toInt())
                }
            }

            // Availability
            when (crew.availability) {
                "on_board" -> {
                    holder.tvAvailability.text = "🔵 Denizde"
                    holder.tvAvailability.setTextColor(0xFF2563EB.toInt())
                }
                "available" -> {
                    holder.tvAvailability.text = "🟢 Müsait"
                    holder.tvAvailability.setTextColor(0xFF16A34A.toInt())
                }
                else -> {
                    holder.tvAvailability.text = ""
                }
            }

            holder.itemView.setOnClickListener { onClick(crew) }
        }

        override fun getItemCount() = items.size
    }
}
