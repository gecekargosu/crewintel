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
import com.crewintel.mobile.models.Ship
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class ShipListActivity : AppCompatActivity() {

    private lateinit var prefs: PrefsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_documents)

        val toolbar = findViewById<com.google.android.material.appbar.MaterialToolbar>(R.id.toolbar)
        toolbar.title = "Gemiler"
        toolbar.setNavigationOnClickListener { finish() }

        prefs = PrefsManager(this)
        loadShips()
    }

    private fun loadShips() {
        val progressBar = findViewById<com.google.android.material.progressindicator.LinearProgressIndicator>(R.id.progressBar)
        val rvDocs = findViewById<RecyclerView>(R.id.rvDocs)
        val tvCount = findViewById<TextView>(R.id.tvCount)
        val tvEmpty = findViewById<TextView>(R.id.tvEmpty)

        progressBar.visibility = View.VISIBLE
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getShips()
                if (response.isSuccessful) {
                    val ships = response.body() ?: emptyList()
                    tvCount.text = "${ships.size} gemi"

                    if (ships.isEmpty()) {
                        tvEmpty.visibility = View.VISIBLE
                        rvDocs.visibility = View.GONE
                    } else {
                        tvEmpty.visibility = View.GONE
                        rvDocs.visibility = View.VISIBLE
                        rvDocs.layoutManager = this@ShipListActivity.let {
                            LinearLayoutManager(it)
                        }
                        rvDocs.adapter = ShipAdapter(ships) { ship ->
                            AlertDialog.Builder(this@ShipListActivity)
                                .setTitle("🚢 ${ship.name}")
                                .setMessage(buildString {
                                    appendLine("IMO: ${ship.imo ?: "—"}")
                                    appendLine("Tip: ${ship.type ?: "—"}")
                                    appendLine("Bayrak: ${ship.flag ?: "—"}")
                                    appendLine("Durum: ${ship.status ?: "—"}")
                                })
                                .setPositiveButton("Tamam", null)
                                .show()
                        }
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@ShipListActivity, "Hata: ${e.localizedMessage}", Toast.LENGTH_LONG).show()
            } finally {
                progressBar.visibility = View.GONE
            }
        }
    }

    class ShipAdapter(
        private val items: List<Ship>,
        private val onClick: (Ship) -> Unit
    ) : RecyclerView.Adapter<ShipAdapter.VH>() {
        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val tvType: TextView = view.findViewById(R.id.tvDocType)
            val tvName: TextView = view.findViewById(R.id.tvDocName)
        }
        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            return VH(LayoutInflater.from(parent.context).inflate(R.layout.item_document, parent, false))
        }
        override fun onBindViewHolder(holder: VH, position: Int) {
            val ship = items[position]
            holder.tvType.text = "🚢 ${ship.type ?: "Gemi"}"
            holder.tvName.text = ship.name
            holder.itemView.setOnClickListener { onClick(ship) }
        }
        override fun getItemCount() = items.size
    }
}
