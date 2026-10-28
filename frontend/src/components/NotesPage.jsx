import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";

import { API_URL } from "../config";
import { apiErrorMessage } from "../utils/apiError";

const PRIORITIES = ["low", "normal", "high", "urgent"];

/**
 * Operasyon notları — kullanıcıya özel, veritabanında saklanır.
 *
 * Eskiden notlar yalnızca mobil uygulamada (bellekte) vardı; masaüstünde
 * karşılığı yoktu. Bu ekran /api/notes uçlarını kullanır.
 */
export default function NotesPage({ crewList = [] }) {
  const { t } = useTranslation();
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: "",
    body: "",
    priority: "normal",
    crew_member_id: "",
  });

  const loadNotes = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/notes/`);
      setNotes(response.data);
      setError(null);
    } catch (err) {
      setError(apiErrorMessage(err, t));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      await axios.post(`${API_URL}/api/notes/`, {
        title: form.title.trim(),
        body: form.body,
        priority: form.priority,
        crew_member_id: form.crew_member_id ? Number(form.crew_member_id) : null,
      });
      setForm({ title: "", body: "", priority: "normal", crew_member_id: "" });
      await loadNotes();
    } catch (err) {
      alert(apiErrorMessage(err, t));
    } finally {
      setSaving(false);
    }
  }

  async function toggleDone(note) {
    try {
      await axios.put(`${API_URL}/api/notes/${note.id}`, { done: !note.done });
      await loadNotes();
    } catch (err) {
      alert(apiErrorMessage(err, t));
    }
  }

  async function removeNote(note) {
    if (!window.confirm(t("notesPage.deleteConfirm"))) return;
    try {
      await axios.delete(`${API_URL}/api/notes/${note.id}`);
      await loadNotes();
    } catch (err) {
      alert(apiErrorMessage(err, t));
    }
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>{t("notesPage.title")}</h2>
      <p style={{ color: "#64748b", marginTop: -6 }}>{t("notesPage.subtitle")}</p>

      <form className="panel" onSubmit={handleSubmit} style={{ marginBottom: "20px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: "12px" }}>
          <div>
            <label className="section-label">{t("notesPage.noteTitle")}</label>
            <input
              className="form-input"
              value={form.title}
              maxLength={200}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="section-label">{t("notesPage.priority")}</label>
            <select
              className="form-input"
              value={form.priority}
              onChange={(event) => setForm({ ...form, priority: event.target.value })}
            >
              {PRIORITIES.map((priority) => (
                <option key={priority} value={priority}>
                  {t(`notesPage.priorities.${priority}`)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="section-label">{t("notesPage.relatedCrew")}</label>
            <select
              className="form-input"
              value={form.crew_member_id}
              onChange={(event) => setForm({ ...form, crew_member_id: event.target.value })}
            >
              <option value="">{t("common.all")}</option>
              {crewList.map((crew) => (
                <option key={crew.id} value={crew.id}>
                  {crew.first_name} {crew.last_name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div style={{ marginTop: "12px" }}>
          <label className="section-label">{t("common.notes")}</label>
          <textarea
            className="form-input"
            rows={3}
            value={form.body}
            onChange={(event) => setForm({ ...form, body: event.target.value })}
          />
        </div>
        <button className="primary-button" type="submit" disabled={saving} style={{ marginTop: "12px" }}>
          {saving ? t("common.saving") : t("common.add")}
        </button>
      </form>

      {error && <div className="panel" style={{ color: "#b91c1c" }}>{error}</div>}
      {loading && <p>{t("common.loading")}</p>}

      {!loading && notes.length === 0 && <div className="panel">{t("common.noData")}</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {notes.map((note) => (
          <div
            key={note.id}
            className="panel"
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "12px",
              alignItems: "flex-start",
              opacity: note.done ? 0.6 : 1,
              borderLeft: `5px solid ${note.priority === "urgent" ? "#dc2626" : note.priority === "high" ? "#f97316" : "#94a3b8"}`,
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                <strong
                  style={{
                    color: "#0f172a",
                    textDecoration: note.done ? "line-through" : "none",
                  }}
                >
                  {note.title}
                </strong>
                <span className="badge" style={{ background: "#f1f5f9", color: "#475569", fontSize: "11px", padding: "2px 8px", borderRadius: "10px" }}>
                  {t(`notesPage.priorities.${note.priority}`)}
                </span>
                {note.crew_member_id && (
                  <span className="badge" style={{ background: "#eff6ff", color: "#1d4ed8", fontSize: "11px", padding: "2px 8px", borderRadius: "10px" }}>
                    #{note.crew_member_id}
                  </span>
                )}
              </div>
              {note.body && <p style={{ margin: "8px 0 0 0", color: "#475569", whiteSpace: "pre-wrap" }}>{note.body}</p>}
              <small style={{ color: "#94a3b8" }}>{note.created_at?.slice(0, 16).replace("T", " ")}</small>
            </div>
            <div style={{ display: "flex", gap: "6px" }}>
              <button className="secondary-button" onClick={() => toggleDone(note)} type="button">
                {note.done ? t("notesPage.reopen") : t("notesPage.markDone")}
              </button>
              <button className="secondary-button" onClick={() => removeNote(note)} type="button">
                {t("common.delete")}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
