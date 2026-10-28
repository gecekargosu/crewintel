import { useEffect, useState } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";

import { API_URL } from "../config";
import { apiErrorMessage } from "../utils/apiError";

/**
 * Personel portalı — "crew" rolündeki kullanıcının kendi ekranı.
 *
 * App.jsx içinde `renderPortal()` fonksiyonu olarak yaşarken React hook'ları
 * koşullu bir fonksiyonun içinde çağrılıyordu; sayfadan çıkıldığında hook
 * sayısı değiştiği için uygulama çökebiliyordu. Bu bileşen portalın kendi
 * state'ini ve veri yüklemesini bağımsız olarak yönetir.
 */
export default function PortalPage({ portalJobs, onApply, onToggleJobSeeking }) {
  const { t } = useTranslation();
  const [portalData, setPortalData] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [message, setMessage] = useState(null);
  const [contactForm, setContactForm] = useState({ phone: "", email: "" });

  useEffect(() => {
    let cancelled = false;
    axios
      .get(`${API_URL}/api/portal/me`)
      .then((res) => {
        if (cancelled) return;
        setPortalData(res.data);
        setContactForm({
          phone: res.data.profile.phone || "",
          email: res.data.profile.email || "",
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setLoadError(err.response?.status || 0);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function submitContact(event) {
    event.preventDefault();
    try {
      await axios.put(`${API_URL}/api/portal/contact`, contactForm);
      setMessage({ type: "success", text: t("profile.profileUpdated") });
    } catch (err) {
      setMessage({
        type: "error",
        text: apiErrorMessage(err, t, 'errors.generic'),
      });
    }
  }

  async function toggleJobSeeking() {
    const next = !portalData.profile.job_seeking;
    await onToggleJobSeeking(next);
    setPortalData((prev) => ({
      ...prev,
      profile: { ...prev.profile, job_seeking: next },
    }));
  }

  if (loadError) {
    return (
      <section className="panel" style={{ padding: "40px", textAlign: "center" }}>
        <h2 style={{ color: "#b91c1c", marginBottom: "10px" }}>{t("ui.portalErrorTitle")}</h2>
        <p style={{ color: "#475569" }}>{t("ui.portalErrorHint")}</p>
      </section>
    );
  }

  if (!portalData) {
    return (
      <section className="panel" style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
        {t("ui.portalLoading")}
      </section>
    );
  }

  const { profile, documents } = portalData;
  const requiredTypes = {
    passport: t("documentTypes.passport"),
    seaman_book: t("documentTypes.seaman_book"),
    stcw: t("documentTypes.stcw"),
    medical: t("documentTypes.medical"),
  };
  const presentTypes = documents.filter((doc) => !doc.archived).map((doc) => doc.document_type);
  const missingTypes = Object.keys(requiredTypes).filter((type) => !presentTypes.includes(type));
  const cardStyle = {
    background: "#f8fafc",
    padding: "20px",
    borderRadius: "12px",
    border: "1px solid #e2e8f0",
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>{t("profile.title")}</h2>
          <p>{t("profile.personalInfo")}</p>
        </div>
      </div>

      {message && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: "8px",
            marginBottom: "14px",
            fontWeight: "600",
            fontSize: "13px",
            background: message.type === "success" ? "#f0fdf4" : "#fef2f2",
            color: message.type === "success" ? "#15803d" : "#b91c1c",
          }}
        >
          {message.text}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px" }}>
        <div style={cardStyle}>
          <h3 style={{ margin: "0 0 14px 0", color: "#0f172a" }}>{t("profile.title")}</h3>
          <p style={{ margin: "0 0 6px 0", color: "#0f172a" }}>
            <strong>
              {profile.first_name} {profile.last_name}
            </strong>
          </p>
          <p style={{ margin: "0 0 4px 0", color: "#475569", fontSize: "13px" }}>
            {profile.position}
            {profile.rank ? " · " + profile.rank : ""}
          </p>
          <p style={{ margin: "0 0 4px 0", color: "#475569", fontSize: "13px" }}>
            {profile.nationality || ""} · {t("crew.experience")}: {profile.experience_years || 0}
          </p>
          {missingTypes.length > 0 ? (
            <p style={{ margin: "12px 0 0 0", color: "#b45309", fontWeight: "600", fontSize: "13px" }}>
              {t("documents.missingDocuments")}: {missingTypes.map((type) => requiredTypes[type]).join(", ")}
            </p>
          ) : (
            <p style={{ margin: "12px 0 0 0", color: "#15803d", fontWeight: "700", fontSize: "13px" }}>
              ✅ {t("documents.allDocumentsPresent")}
            </p>
          )}

          <div
            style={{
              marginTop: "16px",
              padding: "14px",
              background: profile.job_seeking ? "#f0fdf4" : "#f8fafc",
              border: `1px solid ${profile.job_seeking ? "#bbf7d0" : "#e2e8f0"}`,
              borderRadius: "10px",
            }}
          >
            <p
              style={{
                margin: "0 0 8px 0",
                fontSize: "13px",
                fontWeight: "700",
                color: profile.job_seeking ? "#15803d" : "#64748b",
              }}
            >
              {profile.job_seeking ? "🟢 " + t("ui.jobSeekingOn") : "⚪ " + t("ui.jobSeekingOff")}
            </p>
            <button
              className={profile.job_seeking ? "secondary-button" : "primary-button"}
              style={{ padding: "8px 14px", fontSize: "13px" }}
              onClick={toggleJobSeeking}
            >
              {profile.job_seeking ? t("ui.jobSeekingDisable") : t("ui.jobSeekingEnable")}
            </button>
            <p style={{ margin: "8px 0 0 0", fontSize: "12px", color: "#64748b" }}>{t("crew.jobSeekingHint")}</p>
          </div>

          <form onSubmit={submitContact} style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "10px" }}>
            <label style={{ fontSize: "12px", fontWeight: "bold", color: "#475569" }}>
              {t("common.phone")}
              <input
                className="form-input"
                style={{ width: "100%", padding: "9px", marginTop: "4px" }}
                value={contactForm.phone}
                onChange={(event) => setContactForm({ ...contactForm, phone: event.target.value })}
              />
            </label>
            <label style={{ fontSize: "12px", fontWeight: "bold", color: "#475569" }}>
              {t("common.email")}
              <input
                className="form-input"
                type="email"
                style={{ width: "100%", padding: "9px", marginTop: "4px" }}
                value={contactForm.email}
                onChange={(event) => setContactForm({ ...contactForm, email: event.target.value })}
              />
            </label>
            <button className="primary-button" type="submit" style={{ padding: "10px" }}>
              {t("profile.saveProfile")}
            </button>
          </form>
        </div>

        <div style={cardStyle}>
          <h3 style={{ margin: "0 0 14px 0", color: "#0f172a" }}>
            {t("documents.title")} ({documents.length})
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {documents.map((doc) => (
              <div
                key={doc.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "10px 12px",
                  background: "#fff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                }}
              >
                <div>
                  <strong style={{ fontSize: "13px", color: "#0f172a" }}>{doc.document_type}</strong>
                  <span style={{ display: "block", fontSize: "12px", color: "#64748b" }}>
                    {doc.original_filename}
                    {doc.expiry_date ? ` · ${t("contracts.endDate")}: ${doc.expiry_date}` : ""}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: "600",
                    color: doc.archived ? "#94a3b8" : doc.match_status === "matched" ? "#15803d" : "#b45309",
                  }}
                >
                  {doc.archived
                    ? t("common.archived")
                    : doc.match_status === "matched"
                      ? "✓ " + t("documents.valid")
                      : t("documents.pending")}
                </span>
              </div>
            ))}
            {documents.length === 0 && (
              <p style={{ color: "#64748b" }}>{t("ui.noneForYou")}</p>
            )}
          </div>
        </div>
      </div>

      <div style={{ marginTop: "24px" }}>
        <h3 style={{ margin: "0 0 14px 0", color: "#0f172a" }}>
          {t("jobs.title")} ({portalJobs.length})
        </h3>
        {portalJobs.length === 0 && (
          <div
            style={{
              padding: "24px",
              textAlign: "center",
              color: "#64748b",
              background: "#f8fafc",
              border: "2px dashed #cbd5e1",
              borderRadius: "12px",
            }}
          >
            {t("ui.noPublishedJobs")}
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px" }}>
          {portalJobs.map((job) => (
            <div key={job.id} style={cardStyle}>
              <strong style={{ fontSize: "15px", color: "#0f172a" }}>{job.title}</strong>
              <div style={{ color: "#64748b", fontSize: "13px", marginTop: "4px" }}>
                {job.ship_name ? `🚢 ${job.ship_name}` : "🚢 " + t("vessels.name")} · {job.position}
              </div>
              {job.salary && (
                <p style={{ margin: "8px 0 0 0", color: "#0f172a", fontWeight: "600", fontSize: "13px" }}>
                  💰 {job.salary} {job.currency}
                </p>
              )}
              {(job.contract_duration || job.join_date || job.application_deadline) && (
                <p style={{ margin: "4px 0 0 0", color: "#64748b", fontSize: "12px" }}>
                  {[
                    job.contract_duration && `${t("contracts.type")}: ${job.contract_duration}`,
                    job.join_date && `${t("contracts.startDate")}: ${job.join_date}`,
                    job.application_deadline && `${t("jobs.deadline")}: ${job.application_deadline}`,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              )}
              {job.requirements && (
                <p style={{ margin: "8px 0 0 0", color: "#475569", fontSize: "12px" }}>
                  <strong>{t("jobs.requirements")}:</strong> {job.requirements}
                </p>
              )}
              {job.application_status ? (
                <p style={{ margin: "10px 0 0 0", fontSize: "13px", fontWeight: "700", color: "#15803d" }}>
                  ✓ {t("applications.applied")} ({job.application_status})
                </p>
              ) : (
                <button
                  className="primary-button"
                  style={{ padding: "9px 16px", fontSize: "13px", marginTop: "10px" }}
                  onClick={() => onApply(job.id)}
                >
                  {t("jobs.apply")}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
