package com.crewintel.mobile.models

import com.google.gson.annotations.SerializedName

// ── Dashboard ──────────────────────────────────────────────
data class DashboardSummary(
    @SerializedName("totalCrew") val totalCrew: Int = 0,
    @SerializedName("activeShips") val activeShips: Int = 0,
    @SerializedName("totalDocuments") val totalDocuments: Int = 0,
    @SerializedName("expiringDocuments") val expiringDocuments: Int = 0,
    @SerializedName("expiredDocuments") val expiredDocuments: Int = 0,
    @SerializedName("urgentDocuments") val urgentDocuments: Int = 0,
    @SerializedName("unmatchedDocuments") val unmatchedDocuments: Int = 0,
    @SerializedName("warnings") val warnings: Warnings = Warnings(),
    @SerializedName("health") val health: Map<String, Any>? = null
)

data class Warnings(
    @SerializedName("expired") val expired: Int = 0,
    @SerializedName("expiring_soon") val expiringSoon: Int = 0,
    @SerializedName("no_match") val noMatch: Int = 0
)

// ── Crew ───────────────────────────────────────────────────
data class CrewMember(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("first_name") val firstName: String = "",
    @SerializedName("last_name") val lastName: String = "",
    @SerializedName("position") val position: String = "",
    @SerializedName("rank") val rank: String? = null,
    @SerializedName("nationality") val nationality: String? = null,
    @SerializedName("experience_years") val experienceYears: Int? = null,
    @SerializedName("availability") val availability: String? = null,
    @SerializedName("email") val email: String? = null,
    @SerializedName("phone") val phone: String? = null,
    @SerializedName("status") val status: String = "active",
    @SerializedName("documents") val documents: List<Document> = emptyList()
)

data class Document(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("name") val name: String = "",
    @SerializedName("document_type") val documentType: String = "",
    @SerializedName("expiry_date") val expiryDate: String? = null,
    @SerializedName("status") val status: String = "",
    @SerializedName("expiry_status") val expiryStatus: String = "",
    @SerializedName("ship_name") val shipName: String? = null,
    @SerializedName("match_status") val matchStatus: String? = null,
    @SerializedName("match_confidence") val matchConfidence: Double? = null,
    @SerializedName("original_filename") val originalFilename: String? = null,
    @SerializedName("crew_member_id") val crewMemberId: Int? = null
)

// ── Ship ───────────────────────────────────────────────────
data class Ship(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("name") val name: String = "",
    @SerializedName("imo_number") val imoNumber: String? = null,
    @SerializedName("ship_type") val shipType: String = "",
    @SerializedName("flag") val flag: String = "",
    @SerializedName("status") val status: String = "active",
    @SerializedName("crew_count") val crewCount: Int = 0
)

// ── Note ───────────────────────────────────────────────────
data class Note(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("title") val title: String = "",
    @SerializedName("body") val body: String = "",
    @SerializedName("priority") val priority: String = "normal",
    @SerializedName("done") val done: Boolean = false,
    @SerializedName("created_at") val createdAt: String = ""
)

data class NoteRequest(
    val title: String,
    val body: String = "",
    val priority: String = "normal"
)

data class NoteUpdateRequest(
    val title: String? = null,
    val body: String? = null,
    val priority: String? = null,
    val done: Boolean? = null
)

// ── Payment ────────────────────────────────────────────────
data class Payment(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("crew_member_id") val crewMemberId: Int = 0,
    @SerializedName("crew_name") val crewName: String = "",
    @SerializedName("amount") val amount: Double = 0.0,
    @SerializedName("currency") val currency: String = "USD",
    @SerializedName("payment_type") val paymentType: String = "salary",
    @SerializedName("description") val description: String = "",
    @SerializedName("payment_date") val paymentDate: String = ""
)

data class PaymentRequest(
    @SerializedName("crew_member_id") val crewMemberId: Int,
    val amount: Double,
    val currency: String = "USD",
    @SerializedName("payment_type") val paymentType: String = "salary",
    val description: String = ""
)

// ── GitHub Stats ───────────────────────────────────────────
data class GithubStats(
    @SerializedName("stars") val stars: Int = 0,
    @SerializedName("forks") val forks: Int = 0,
    @SerializedName("watchers") val watchers: Int = 0,
    @SerializedName("open_issues") val openIssues: Int = 0,
    @SerializedName("language") val language: String = "",
    @SerializedName("url") val url: String = ""
)

// ── Audit Log ──────────────────────────────────────────────
data class AuditLog(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("action") val action: String = "",
    @SerializedName("entity_type") val entityType: String = "",
    @SerializedName("entity_id") val entityId: Int = 0,
    @SerializedName("details") val details: String = "",
    @SerializedName("created_at") val createdAt: String = "",
    @SerializedName("user") val user: String = ""
)

// ── Notification ───────────────────────────────────────────
data class Notification(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("type") val type: String = "",
    @SerializedName("title") val title: String = "",
    @SerializedName("message") val message: String = "",
    @SerializedName("read") val read: Boolean = false,
    @SerializedName("created_at") val createdAt: String = ""
)

// ── Document Upload ────────────────────────────────────────
data class DocumentUploadResponse(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("filename") val filename: String = "",
    @SerializedName("status") val status: String = "",
    @SerializedName("matched") val matched: Boolean = false,
    @SerializedName("crew_member_id") val crewMemberId: Int? = null
)

data class DocumentUploadBatchResponse(
    @SerializedName("uploaded") val uploaded: Int = 0,
    @SerializedName("matched") val matched: Int = 0,
    @SerializedName("duplicate") val duplicate: Int = 0,
    @SerializedName("failed") val failed: Int = 0,
    @SerializedName("duplicate_files") val duplicateFiles: List<String> = emptyList()
)


// ── Auth ──────────────────────────────────────────────────
data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("refresh_token") val refreshToken: String = "",
    @SerializedName("token_type") val tokenType: String = "bearer",
    @SerializedName("user") val user: UserInfo = UserInfo()
)

data class UserInfo(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("email") val email: String = "",
    @SerializedName("full_name") val fullName: String = "",
    @SerializedName("role") val role: String = ""
)