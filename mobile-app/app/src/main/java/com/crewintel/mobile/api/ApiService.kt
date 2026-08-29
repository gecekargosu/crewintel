package com.crewintel.mobile.api

import com.crewintel.mobile.models.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ── Auth ──────────────────────────────────────────────
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    // ── Health ────────────────────────────────────────────
    @GET("health")
    suspend fun health(): Response<HealthResponse>

    @GET("api/ai/health")
    suspend fun aiHealth(): Response<AIHealthResponse>

    // ── Dashboard ─────────────────────────────────────────
    @GET("api/dashboard/summary")
    suspend fun dashboardSummary(): Response<DashboardSummary>

    // ── Crew ──────────────────────────────────────────────
    @GET("api/crew/")
    suspend fun getCrewList(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 100
    ): Response<List<CrewMember>>

    @GET("api/crew/{id}")
    suspend fun getCrewDetail(@Path("id") id: Int): Response<CrewMember>

    @POST("api/crew/")
    suspend fun createCrew(@Body crew: CrewMember): Response<CrewMember>

    @PUT("api/crew/{id}")
    suspend fun updateCrew(@Path("id") id: Int, @Body crew: CrewMember): Response<CrewMember>

    @DELETE("api/crew/{id}")
    suspend fun deleteCrew(@Path("id") id: Int): Response<Unit>

    // ── Documents ─────────────────────────────────────────
    @GET("api/documents/")
    suspend fun getDocuments(
        @Query("crew_member_id") crewId: Int? = null,
        @Query("document_type") docType: String? = null,
        @Query("match_status") matchStatus: String? = null,
        @Query("expiry_status") expiryStatus: String? = null
    ): Response<List<Document>>

    @GET("api/documents/{id}")
    suspend fun getDocumentDetail(@Path("id") id: Int): Response<Document>

    @DELETE("api/documents/{id}")
    suspend fun deleteDocument(@Path("id") id: Int): Response<Unit>

    @Multipart
    @POST("api/documents/upload")
    suspend fun uploadDocument(
        @Part files: List<MultipartBody.Part>
    ): Response<List<Document>>

    @Multipart
    @POST("api/documents/batch")
    suspend fun batchUpload(
        @Part files: List<MultipartBody.Part>
    ): Response<BatchResponse>

    // ── Ships ─────────────────────────────────────────────
    @GET("api/ships/")
    suspend fun getShips(): Response<List<Ship>>

    @GET("api/ships/{id}")
    suspend fun getShipDetail(@Path("id") id: Int): Response<Ship>

    // ── Contracts ─────────────────────────────────────────
    @GET("api/contracts/")
    suspend fun getContracts(
        @Query("crew_member_id") crewId: Int? = null
    ): Response<List<Contract>>

    // ── AI ────────────────────────────────────────────────
    @POST("api/ai/analyze")
    suspend fun aiAnalyze(@Body request: AIAnalyzeRequest): Response<AIAnalyzeResponse>

    @POST("api/ai/match")
    suspend fun aiMatch(@Body request: AIAnalyzeRequest): Response<Map<String, Any>>

    // ── Notifications ─────────────────────────────────────
    @GET("api/notifications/")
    suspend fun getNotifications(
        @Query("unread_only") unreadOnly: Boolean = false
    ): Response<List<NotificationItem>>

    @POST("api/notifications/{id}/read")
    suspend fun markNotificationRead(@Path("id") id: Int): Response<Unit>

    @POST("api/notifications/generate")
    suspend fun generateAlerts(): Response<Map<String, Any>>

    @POST("api/notifications/send-email")
    suspend fun sendEmail(@Body request: Map<String, Any>): Response<Map<String, Any>>

    @POST("api/notifications/send-bulk")
    suspend fun sendBulkEmail(@Body request: Map<String, Any>): Response<Map<String, Any>>

    // ── Audit Logs ────────────────────────────────────────
    @GET("api/audit-logs/")
    suspend fun getAuditLogs(
        @Query("limit") limit: Int = 50,
        @Query("action") action: String? = null,
        @Query("entity") entity: String? = null
    ): Response<List<Map<String, Any>>>
}
