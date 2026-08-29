package com.crewintel.mobile.utils

import android.content.Context
import android.content.SharedPreferences
import com.crewintel.mobile.models.LoginResponse

class PrefsManager(context: Context) {
    // Use EncryptedSharedPreferences for sensitive data (tokens)
    private val securePrefs: SharedPreferences by lazy {
        try {
            val masterKey = androidx.security.crypto.MasterKey.Builder(context)
                .setKeyScheme(androidx.security.crypto.MasterKey.KeyScheme.AES256_GCM)
                .build()
            androidx.security.crypto.EncryptedSharedPreferences.create(
                context,
                "crewintel_secure_prefs",
                masterKey,
                androidx.security.crypto.EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                androidx.security.crypto.EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            )
        } catch (e: Exception) {
            // Fallback to regular prefs if keystore is unavailable
            context.getSharedPreferences("crewintel_prefs", Context.MODE_PRIVATE)
        }
    }

    // Regular prefs for non-sensitive data
    private val prefs: SharedPreferences =
        context.getSharedPreferences("crewintel_prefs", Context.MODE_PRIVATE)

    var serverUrl: String
        get() {
            val url = prefs.getString("server_url", null) ?: DEFAULT_SERVER_URL
            return normalizeUrl(url)
        }
        set(value) = prefs.edit().putString("server_url", normalizeUrl(value)).apply()

    var authToken: String?
        get() = securePrefs.getString("auth_token", null)
        set(value) = securePrefs.edit().putString("auth_token", value).apply()

    var refreshToken: String?
        get() = securePrefs.getString("refresh_token", null)
        set(value) = securePrefs.edit().putString("refresh_token", value).apply()

    var userEmail: String?
        get() = prefs.getString("user_email", null)
        set(value) = prefs.edit().putString("user_email", value).apply()

    var userRole: String?
        get() = prefs.getString("user_role", null)
        set(value) = prefs.edit().putString("user_role", value).apply()

    var userName: String?
        get() = prefs.getString("user_name", null)
        set(value) = prefs.edit().putString("user_name", value).apply()

    var userId: Int
        get() = prefs.getInt("user_id", -1)
        set(value) = prefs.edit().putInt("user_id", value).apply()

    fun isLoggedIn(): Boolean = authToken != null

    fun clearSession() {
        // Clear secure token storage
        securePrefs.edit()
            .remove("auth_token")
            .remove("refresh_token")
            .apply()
        // Clear regular prefs
        prefs.edit()
            .remove("user_email")
            .remove("user_role")
            .remove("user_name")
            .remove("user_id")
            .apply()
    }

    fun saveLogin(response: LoginResponse) {
        authToken = response.accessToken
        refreshToken = response.refreshToken
        userEmail = response.user.email
        userRole = response.user.role
        userName = response.user.fullName
        userId = response.user.id
    }

    companion object {
        // Default server URL — private IP for local dev, HTTPS for production
        private const val DEFAULT_SERVER_URL = "http://10.160.250.250:8000"
        // Production URL (uncomment when deploying with SSL):
        // private const val DEFAULT_SERVER_URL = "https://your-domain.com"

        fun normalizeUrl(url: String): String {
            var trimmed = url.trim().trimEnd('/')
            if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) {
                trimmed = "http://$trimmed"
            }
            return trimmed
        }
    }
}
