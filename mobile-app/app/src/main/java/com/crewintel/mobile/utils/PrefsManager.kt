package com.crewintel.mobile.utils

import android.content.Context
import android.content.SharedPreferences
import com.crewintel.mobile.models.LoginResponse

class PrefsManager(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("crewintel_prefs", Context.MODE_PRIVATE)

    var serverUrl: String
        get() = prefs.getString("server_url", "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000"
        set(value) = prefs.edit().putString("server_url", value).apply()

    var authToken: String?
        get() = prefs.getString("auth_token", null)
        set(value) = prefs.edit().putString("auth_token", value).apply()

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
        prefs.edit()
            .remove("auth_token")
            .remove("user_email")
            .remove("user_role")
            .remove("user_name")
            .remove("user_id")
            .apply()
    }

    fun saveLogin(response: LoginResponse) {
        authToken = response.accessToken
        userEmail = response.user.email
        userRole = response.user.role
        userName = response.user.fullName
        userId = response.user.id
    }
}
