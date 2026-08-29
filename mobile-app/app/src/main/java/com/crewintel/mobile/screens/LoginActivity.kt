package com.crewintel.mobile.screens

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityLoginBinding
import com.crewintel.mobile.models.LoginRequest
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private lateinit var prefs: PrefsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = PrefsManager(this)
        ApiClient.init(this)

        // Kayıtlı bilgileri doldur
        binding.etServerUrl.setText(prefs.serverUrl)
        binding.etEmail.setText(prefs.userEmail ?: "")

        // Session suresi dolmus mu?
        if (intent.getBooleanExtra("session_expired", false)) {
            Toast.makeText(this, "Oturum sureniz dolmus, lutfen tekrar giris yapin", Toast.LENGTH_LONG).show()
        }

        binding.btnLogin.setOnClickListener { attemptLogin() }
    }

    private fun attemptLogin() {
        val serverUrl = binding.etServerUrl.text.toString().trim()
        val email = binding.etEmail.text.toString().trim()
        val password = binding.etPassword.text.toString().trim()

        if (email.isEmpty() || password.isEmpty()) {
            showError("E-posta ve şifre gerekli")
            return
        }

        if (serverUrl.isEmpty()) {
            showError("Sunucu adresi gerekli")
            return
        }

        // URL'yi kaydet
        prefs.serverUrl = serverUrl
        ApiClient.reset()

        showLoading(true)

        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.login(LoginRequest(email, password))

                if (response.isSuccessful) {
                    val body = response.body()!!
                    prefs.saveLogin(body)

                    Toast.makeText(
                        this@LoginActivity,
                        "Hoş geldin, ${body.user.fullName}!",
                        Toast.LENGTH_SHORT
                    ).show()

                    startActivity(Intent(this@LoginActivity, DashboardActivity::class.java))
                    finish()
                } else {
                    showError("E-posta veya şifre hatalı (${response.code()})")
                }
            } catch (e: Exception) {
                showError("Bağlantı hatası: ${e.localizedMessage}")
            } finally {
                showLoading(false)
            }
        }
    }

    private fun showError(msg: String) {
        binding.tvError.text = msg
        binding.tvError.visibility = View.VISIBLE
    }

    private fun showLoading(show: Boolean) {
        binding.progressBar.visibility = if (show) View.VISIBLE else View.GONE
        binding.btnLogin.isEnabled = !show
    }
}
