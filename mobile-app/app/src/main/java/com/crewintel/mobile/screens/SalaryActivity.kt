package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivitySalaryBinding
import com.crewintel.mobile.databinding.ItemPaymentBinding
import com.crewintel.mobile.models.Payment
import com.crewintel.mobile.models.PaymentRequest
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
                    val payments = response.body() ?: emptyList()
                    adapter.submitList(payments)
                    val total = payments.sumOf { it.amount }
                    binding.tvTotal.text = "Toplam: $total USD"
                }
            } catch (e: Exception) {
                Toast.makeText(this@SalaryActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }
}

class PaymentAdapter :
    androidx.recyclerview.widget.ListAdapter<Payment, PaymentAdapter.ViewHolder>(
        object : androidx.recyclerview.widget.DiffUtil.ItemCallback<Payment>() {
            override fun areItemsTheSame(old: Payment, new: Payment) = old.id == new.id
            override fun areContentsTheSame(old: Payment, new: Payment) = old == new
        }
    ) {
    class ViewHolder(val binding: ItemPaymentBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemPaymentBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val payment = getItem(position)
        holder.binding.tvName.text = payment.crewName
        holder.binding.tvAmount.text = "${payment.amount} ${payment.currency}"
        holder.binding.tvType.text = payment.paymentType
        holder.binding.tvDate.text = payment.paymentDate.substringBefore("T")
        holder.binding.tvDescription.text = payment.description
    }
}
