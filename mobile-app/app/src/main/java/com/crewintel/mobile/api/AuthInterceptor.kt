package com.crewintel.mobile.api

import android.content.Context
import android.content.Intent
import com.crewintel.mobile.screens.LoginActivity
import com.crewintel.mobile.utils.PrefsManager
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.Response

/**
 * Intercepts 401 responses, tries refresh token, then redirects to login if still unauthorized.
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

        // If 401 Unauthorized, try refresh token
        if (response.code == 401) {
            response.close()

            // Try to get new access token using refresh token
            val refreshToken = prefs.refreshToken
            if (refreshToken != null) {
                val refreshed = tryRefreshToken(refreshToken)
                if (refreshed) {
                    // Retry original request with new token
                    val retryRequest = chain.request().newBuilder().apply {
                        prefs.authToken?.let { token ->
                            addHeader("Authorization", "Bearer $token")
                        }
                        addHeader("Content-Type", "application/json")
                    }.build()
                    return chain.proceed(retryRequest)
                }
            }

            // Refresh failed, redirect to login
            prefs.clearSession()
            val intent = Intent(context, LoginActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                putExtra("session_expired", true)
            }
            context.startActivity(intent)
            // Return a fresh 401 response instead of the closed one
            return Response.Builder()
                .request(request)
                .protocol(okhttp3.Protocol.HTTP_1_1)
                .code(401)
                .message("Unauthorized - session expired")
                .body(okhttp3.ResponseBody.create(null, ByteArray(0)))
                .build()
        }

        return response
    }

    private fun tryRefreshToken(refreshToken: String): Boolean {
        return try {
            val client = okhttp3.OkHttpClient.Builder().build()
            val body = """{"refresh_token":"$refreshToken"}"""
            val request = okhttp3.Request.Builder()
                .url("${prefs.serverUrl.trimEnd('/')}/api/auth/refresh")
                .post(okhttp3.RequestBody.create(
                    "application/json".toMediaTypeOrNull(),
                    body
                ))
                .build()

            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val json = org.json.JSONObject(response.body?.string() ?: "")
                val newToken = json.getString("access_token")
                prefs.authToken = newToken
                true
            } else {
                false
            }
        } catch (e: Exception) {
            false
        }
    }
}
