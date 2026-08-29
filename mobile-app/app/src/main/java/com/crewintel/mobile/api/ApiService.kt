package com.crewintel.mobile.api

import com.crewintel.mobile.models.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ── Auth ───────────────────────────────────────────────
    @POST("api/auth/login")
    suspend fun login(@Body creds: LoginRequest): Response<LoginResponse>

    @GET("api/auth/me")
    suspend fun getMe(): Response<Any>

    @POST("api/auth/refresh")
    suspend fun refreshToken(@Body body: Map<String, String>): Response<Any>

    // ── Dashboard ──────────────────────────────────────────
    @GET("api/dashboard/summary")
    suspend fun dashboardSummary(): Response<DashboardSummary>

    @GET("api/dashboard/github-stats")
    suspend fun getGithubStats(): Response<GithubStats>

    // ── Crew ───────────────────────────────────────────────
    @GET("api/crew/")
    suspend fun getCrewList(
        @Query("search") search: String? = null,
        @Query("limit") limit: Int = 100
    ): Response<List<CrewMember>>

    @GET("api/crew/{id}")
    suspend fun getCrewDetail(@Path("id") id: Int): Response<CrewMember>

    // ── Ships ──────────────────────────────────────────────
    @GET("api/ships/")
    suspend fun getShips(): Response<List<Ship>>

    @GET("api/ships/{id}")
    suspend fun getShipDetail(@Path("id") id: Int): Response<Ship>

    // ── Documents ──────────────────────────────────────────
    @GET("api/documents/")
    suspend fun getDocuments(
        @Query("crew_member_id") crewId: Int? = null,
        @Query("expiry_status") expiryStatus: String? = null
    ): Response<List<Document>>

    @GET("api/documents/{id}")
    suspend fun getDocumentDetail(@Path("id") id: Int): Response<Document>

    @Multipart
    @POST("api/documents/upload")
    suspend fun uploadDocument(
        @Part file: MultipartBody.Part,
        @Part("crew_member_id") crewId: RequestBody?,
        @Part("document_type") docType: RequestBody?
    ): Response<DocumentUploadResponse>

    @Multipart
    @POST("api/documents/batch-upload")
    suspend fun batchUploadDocuments(
        @Part files: List<MultipartBody.Part>,
        @Part("crew_member_id") crewId: RequestBody? = null
    ): Response<DocumentUploadBatchResponse>

    // ── Notes ──────────────────────────────────────────────
    @GET("api/notes/")
    suspend fun getNotes(): Response<List<Note>>

    @POST("api/notes/")
    suspend fun createNote(@Body note: NoteRequest): Response<Note>

    @PUT("api/notes/{id}")
    suspend fun updateNote(
        @Path("id") id: Int,
        @Body note: NoteUpdateRequest
    ): Response<Note>

    @DELETE("api/notes/{id}")
    suspend fun deleteNote(@Path("id") id: Int): Response<Unit>

    // ── Salary ─────────────────────────────────────────────
    @GET("api/salary/")
    suspend fun getPayments(): Response<List<Payment>>

    @POST("api/salary/")
    suspend fun createPayment(@Body payment: PaymentRequest): Response<Payment>

    // ── Audit Logs ─────────────────────────────────────────
    @GET("api/audit/")
    suspend fun getAuditLogs(): Response<List<AuditLog>>

    // ── Notifications ──────────────────────────────────────
    @GET("api/notifications/")
    suspend fun getNotifications(): Response<List<Notification>>

    // ── Cookies (Social Downloader) ────────────────────────
    @GET("api/social/downloader/cookies")
    suspend fun getCookiesStatus(): Response<Any>

    @POST("api/social/downloader/cookies")
    suspend fun saveCookies(@Body body: Map<String, String>): Response<Any>

    // ── Social Downloader ──────────────────────────────────
    @POST("api/social/downloader/analyze")
    suspend fun analyzeUrl(@Body body: Map<String, String>): Response<Any>

    @POST("api/social/downloader/download")
    suspend fun startDownload(@Body body: Map<String, String>): Response<Any>

    @GET("api/social/downloader/history")
    suspend fun getDownloadHistory(): Response<Any>

    @GET("api/social/downloader/{taskId}/status")
    suspend fun getDownloadStatus(@Path("taskId") taskId: String): Response<Any>

    @GET("api/social/downloader/{taskId}/file")
    suspend fun getDownloadFile(@Path("taskId") taskId: String): Response<Any>

    @DELETE("api/social/downloader/{taskId}")
    suspend fun deleteDownload(@Path("taskId") taskId: String): Response<Any>

    // ── Email ──────────────────────────────────────────────
    @POST("api/email/send")
    suspend fun sendEmail(@Body body: Map<String, String>): Response<Any>

    // ── AI ──────────────────────────────────────────────
    @POST("api/ai/analyze")
    suspend fun analyzeDocument(@Body body: Map<String, String>): Response<Any>

    // ── Jobs ───────────────────────────────────────────────
    @GET("api/jobs/")
    suspend fun getJobs(): Response<Any>
}


