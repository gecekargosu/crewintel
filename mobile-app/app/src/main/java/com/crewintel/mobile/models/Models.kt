package com.crewintel.mobile.models

import com.google.gson.annotations.SerializedName

// ── Auth ──────────────────────────────────────────────────
data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    val user: UserResponse
)

data class UserResponse(
    val id: Int,
    val email: String,
    @SerializedName("full_name") val fullName: String,
    val role: String,
    @SerializedName("is_active") val isActive: Boolean
)

// ── Crew ──────────────────────────────────────────────────
data class CrewMember(
    val id: Int,
    @SerializedName("first_name") val firstName: String,
    @SerializedName("last_name") val lastName: String,
    val position: String? = null,
    val rank: String? = null,
    val nationality: String? = null,
    val status: String = "active",
    val email: String? = null,
    val phone: String? = null,
    @SerializedName("experience_years") val experienceYears: Int? = null,
    @SerializedName("date_of_birth") val dateOfBirth: String? = null,
    val availability: String? = null,
    @SerializedName("passport_number") val passportNumber: String? = null,
    @SerializedName("seaman_book_number") val seamanBookNumber: String? = null
)

// ── Document ──────────────────────────────────────────────
data class Document(
    val id: Int,
    @SerializedName("original_filename") val originalFilename: String,
    @SerializedName("document_type") val documentType: String,
    @SerializedName("match_status") val matchStatus: String,
    @SerializedName("match_confidence") val matchConfidence: Int? = null,
    @SerializedName("expiry_date") val expiryDate: String? = null,
    @SerializedName("expiry_status") val expiryStatus: String? = null,
    @SerializedName("crew_member_id") val crewMemberId: Int? = null,
    @SerializedName("created_at") val createdAt: String? = null,
    val archived: Boolean = false
)

data class DocumentListResponse(
    val total: Int,
    val documents: List<Document>
)

// ── Ship ──────────────────────────────────────────────────
data class Ship(
    val id: Int,
    val name: String,
    val imo: String? = null,
    val type: String? = null,
    val flag: String? = null,
    val status: String? = null
)

// ── Dashboard ─────────────────────────────────────────────
data class DashboardSummary(
    @SerializedName("totalCrew") val totalCrew: Int = 0,
    @SerializedName("totalPersonnel") val totalPersonnel: Int = 0,
    @SerializedName("activePersonnel") val activePersonnel: Int = 0,
    @SerializedName("activeShips") val activeShips: Int = 0,
    @SerializedName("totalDocuments") val totalDocuments: Int = 0,
    @SerializedName("expiringDocuments") val expiringDocuments: Int = 0,
    @SerializedName("expiredDocuments") val expiredDocuments: Int = 0,
    @SerializedName("urgentDocuments") val urgentDocuments: Int = 0,
    @SerializedName("unmatchedDocuments") val unmatchedDocuments: Int = 0,
    @SerializedName("activeContracts") val activeContracts: Int = 0
)

// ── Contract ──────────────────────────────────────────────
data class Contract(
    val id: Int,
    @SerializedName("crew_member_id") val crewMemberId: Int,
    @SerializedName("ship_id") val shipId: Int? = null,
    val status: String = "active",
    @SerializedName("start_date") val startDate: String? = null,
    @SerializedName("end_date") val endDate: String? = null,
    val position: String? = null
)

// ── Notification ──────────────────────────────────────────
data class NotificationItem(
    val id: Int,
    val title: String,
    val message: String,
    val channel: String? = null,
    val status: String? = null,
    @SerializedName("entity_type") val entityType: String? = null,
    @SerializedName("entity_id") val entityId: Int? = null,
    val link: String? = null,
    val read: Boolean = false,
    @SerializedName("created_at") val createdAt: String? = null
)

// ── AI ────────────────────────────────────────────────────
data class AIAnalyzeRequest(
    val text: String,
    val language: String = "auto"
)

data class AIAnalyzeResponse(
    val status: String,
    val documentType: String? = null,
    val entities: Map<String, Any>? = null,
    val suggestions: List<String>? = null,
    val confidence: Double? = null
)

// ── Health ────────────────────────────────────────────────
data class HealthResponse(
    val status: String,
    val environment: String? = null
)

data class AIHealthResponse(
    val status: String,
    @SerializedName("llm_available") val llmAvailable: Boolean = false,
    val model: String? = null,
    val provider: String? = null
)

// ── Batch Upload ──────────────────────────────────────────
data class BatchResponse(
    @SerializedName("batch_id") val batchId: String,
    val status: String,
    val total: Int,
    val processed: Int,
    val matched: Int = 0,
    val duplicate: Int = 0,
    val failed: Int = 0,
    @SerializedName("duplicate_files") val duplicateFiles: List<String> = emptyList()
)
