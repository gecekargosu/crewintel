package com.crewintel.mobile.api

import android.content.Context
import android.content.Intent
import com.crewintel.mobile.screens.LoginActivity
import com.crewintel.mobile.utils.PrefsManager
import okhttp3.Interceptor
import okhttp3.Response

/**
 * Intercepts 401 responses and redirects to LoginActivity.
 * Also adds Authorization header to all requests.
 */
class AuthInterceptor(
    private val context: Context,
    private val prefs: PrefsManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder().apply {
            prefs.authToken?.let { token ->
                addHeader("Authorization", "Bearer $token")
            }
            addHeader("Content-Type", "application/json")
        }.build()

        val response = chain.proceed(request)

        // If 401 Unauthorized, clear session and redirect to login
        if (response.code == 401) {
            // Clear token
            prefs.clearSession()

            // Redirect to LoginActivity (on main thread)
            val intent = Intent(context, LoginActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                putExtra("session_expired", true)
            }
            context.startActivity(intent)
        }

        return response
    }
}
