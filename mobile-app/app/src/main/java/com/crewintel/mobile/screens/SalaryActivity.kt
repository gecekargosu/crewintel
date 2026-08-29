package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivitySalaryBinding
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class SalaryActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySalaryBinding
    private lateinit var prefs: PrefsManager
    private val adapter = PaymentAdapter()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySalaryBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.btnAdd.setOnClickListener { showAddDialog() }
        binding.rvPayments.layoutManager = LinearLayoutManager(this)
        binding.rvPayments.adapter = adapter

        loadPayments()
    }

    private fun loadPayments() {
        binding.progressBar.visibility = View.VISIBLE
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getPayments()
                if (response.isSuccessful) {
                    val body = response.body()
                    val payments = if (body is List<*>) body.filterIsInstance<Map<String, Any>>() else emptyList()
                    if (payments.isEmpty()) {
                        binding.tvEmpty.visibility = View.VISIBLE
                    } else {
                        binding.tvEmpty.visibility = View.GONE
                        adapter.submitList(payments)
                        val total = payments.sumOf { (it["amount"] as? Number)?.toDouble() ?: 0.0 }
                        val currency = payments.firstOrNull()?.get("currency")?.toString() ?: "USD"
                        binding.tvTotal.text = "Toplam: $total $currency (${payments.size} kayıt)"
                        binding.tvTotal.visibility = View.VISIBLE
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@SalaryActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun showAddDialog() {
        val crewInput = EditText(this).apply { hint = "Personel ID" }
        val amountInput = EditText(this).apply { hint = "Tutar (USD)"; inputType = android.text.InputType.TYPE_CLASS_NUMBER or android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL }
        val descInput = EditText(this).apply { hint = "Açıklama (maaş, bonus, avans)" }

        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(48, 24, 48, 0)
            addView(crewInput)
            addView(amountInput)
            addView(descInput)
        }

        AlertDialog.Builder(this)
            .setTitle("💰 Yeni Ödeme")
            .setView(layout)
            .setPositiveButton("Kaydet") { _, _ ->
                val crewId = crewInput.text.toString().toIntOrNull()
                val amount = amountInput.text.toString().toDoubleOrNull()
                val desc = descInput.text.toString().trim()
                if (crewId != null && amount != null && amount > 0) {
                    addPayment(crewId, amount, desc)
                } else {
                    Toast.makeText(this, "Geçerli bilgi girin", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("İptal", null)
            .show()
    }

    private fun addPayment(crewId: Int, amount: Double, description: String) {
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                api.createPayment(mapOf(
                    "crew_member_id" to crewId,
                    "amount" to amount,
                    "currency" to "USD",
                    "payment_type" to "salary",
                    "description" to description
                ))
                loadPayments()
            } catch (e: Exception) {
                Toast.makeText(this@SalaryActivity, "Kaydedilemedi", Toast.LENGTH_SHORT).show()
            }
        }
    }
}

class PaymentAdapter : androidx.recyclerview.widget.ListAdapter<Map<String, Any>, PaymentAdapter.ViewHolder>(
    object : androidx.recyclerview.widget.DiffUtil.ItemCallback<Map<String, Any>>() {
        override fun areItemsTheSame(old: Map<String, Any>, new: Map<String, Any>) = old["id"] == new["id"]
        override fun areContentsTheSame(old: Map<String, Any>, new: Map<String, Any>) = old == new
    }
) {
    class ViewHolder(val binding: com.crewintel.mobile.databinding.ItemNoteBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = com.crewintel.mobile.databinding.ItemNoteBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val payment = getItem(position)
        val amount = payment["amount"]?.toString() ?: "0"
        val currency = payment["currency"]?.toString() ?: "USD"
        val desc = payment["description"]?.toString() ?: ""
        val date = payment["payment_date"]?.toString() ?: ""

        holder.binding.tvTitle.text = "💰 $amount $currency"
        holder.binding.tvBody.text = if (desc.isNotBlank()) desc else "Ödeme"
        holder.binding.tvDate.text = date
        holder.binding.viewPriority.setBackgroundColor(0xFF16a34a.toInt())
        holder.binding.btnDone.visibility = View.GONE
        holder.binding.btnDelete.visibility = View.GONE
    }
}
