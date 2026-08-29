package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityShipListBinding
import com.crewintel.mobile.databinding.ItemShipBinding
import com.crewintel.mobile.models.Ship
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class ShipListActivity : AppCompatActivity() {

    private lateinit var binding: ActivityShipListBinding
    private lateinit var prefs: PrefsManager
    private val adapter = ShipAdapter { ship -> showShipDetail(ship) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityShipListBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.rvShips.layoutManager = LinearLayoutManager(this)
        binding.rvShips.adapter = adapter

        loadShips()
    }

    private fun loadShips() {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvEmpty.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getShips()
                if (response.isSuccessful) {
                    val ships = response.body() ?: emptyList()
                    binding.tvCount.text = "${ships.size} gemi"

                    if (ships.isEmpty()) {
                        binding.tvEmpty.visibility = View.VISIBLE
                    } else {
                        adapter.submitList(ships)
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@ShipListActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun showShipDetail(ship: Ship) {
        AlertDialog.Builder(this)
            .setTitle("🚢 ${ship.name}")
            .setMessage(buildString {
                appendLine("IMO: ${ship.imoNumber ?: "—"}")
                appendLine("Tip: ${ship.shipType ?: "—"}")
                appendLine("Bayrak: ${ship.flag ?: "—"}")
                appendLine("Durum: ${ship.status ?: "—"}")
            })
            .setPositiveButton("Tamam", null)
            .show()
    }
}

class ShipAdapter(
    private val onClick: (Ship) -> Unit
) : androidx.recyclerview.widget.ListAdapter<Ship, ShipAdapter.ViewHolder>(
    object : androidx.recyclerview.widget.DiffUtil.ItemCallback<Ship>() {
        override fun areItemsTheSame(old: Ship, new: Ship) = old.id == new.id
        override fun areContentsTheSame(old: Ship, new: Ship) = old == new
    }
) {
    class ViewHolder(val binding: ItemShipBinding) : androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemShipBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val ship = getItem(position)
        holder.binding.tvShipName.text = ship.name
        holder.binding.tvShipType.text = ship.shipType ?: "Gemi"
        holder.binding.tvIMO.text = if (ship.imoNumber != null) "IMO: ${ship.imoNumber}" else ""
        holder.binding.tvFlag.text = if (ship.flag != null) "🏁 ${ship.flag}" else ""

        val status = ship.status ?: "active"
        holder.binding.tvStatus.text = status
        val statusColor = when (status.lowercase()) {
            "active" -> 0xFF16a34a.toInt()
            "maintenance" -> 0xFFF97316.toInt()
            "inactive" -> 0xFF6B7280.toInt()
            else -> 0xFF3B82F6.toInt()
        }
        holder.binding.tvStatus.setBackgroundColor(statusColor)

        holder.itemView.setOnClickListener { onClick(ship) }
    }
}
