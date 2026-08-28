package com.crewintel.mobile.screens

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.utils.PrefsManager

class SettingsActivity : AppCompatActivity() {

    private lateinit var prefs: PrefsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = PrefsManager(this)
        showSettingsMenu()
    }

    private fun showSettingsMenu() {
        val items = arrayOf(
            "👤 Kullanıcı: ${prefs.userName ?: prefs.userEmail}",
            "🔑 Rol: ${prefs.userRole}",
            "🖥️ Sunucu: ${prefs.serverUrl}",
            "",
            "🔄 Sunucu Adresini Değiştir",
            "🚪 Çıkış Yap"
        )

        AlertDialog.Builder(this)
            .setTitle("Ayarlar")
            .setItems(items) { _, which ->
                when (which) {
                    3 -> showChangeServerDialog()
                    4 -> logout()
                    else -> {}
                }
            }
            .setOnCancelListener { finish() }
            .show()
    }

    private fun showChangeServerDialog() {
        val input = android.widget.EditText(this).apply {
            setText(prefs.serverUrl)
            hint = "http://192.168.1.100:8000"
        }

        AlertDialog.Builder(this)
            .setTitle("Sunucu Adresi")
            .setView(input)
            .setPositiveButton("Kaydet") { _, _ ->
                prefs.serverUrl = input.text.toString().trim()
                ApiClient.reset()
                Toast.makeText(this, "Sunucu güncellendi", Toast.LENGTH_SHORT).show()
                finish()
            }
            .setNegativeButton("İptal") { _, _ -> finish() }
            .show()
    }

    private fun logout() {
        prefs.clearSession()
        ApiClient.reset()
        startActivity(android.content.Intent(this, LoginActivity::class.java).apply {
            flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK or android.content.Intent.FLAG_ACTIVITY_CLEAR_TASK
        })
        finish()
    }
}
