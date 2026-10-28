import { useEffect, useState } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";

import { API_URL } from "../config";
import { apiErrorMessage } from "../utils/apiError";

/**
 * İsteğe bağlı yapay zekâ paneli.
 *
 * Anahtar tanımlı değilse (AI_API_KEY boş) hiçbir şey bozulmaz; panel
 * "yapılandırılmadı" bilgisini ve kurulum adımını gösterir.
 */
export default function AiPanel() {
  const { t } = useTranslation();
  const [health, setHealth] = useState(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get(`${API_URL}/api/ai/health`)
      .then((response) => setHealth(response.data))
      .catch(() => setHealth({ status: "not_configured", llm_available: false }));
  }, []);

  async function run(kind) {
    if (!text.trim()) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      if (kind === "summarize") {
        const response = await axios.post(`${API_URL}/api/ai/summarize`, { text });
        setResult({ type: "summarize", value: response.data.summary });
      } else {
        const response = await axios.post(`${API_URL}/api/ai/anomalies`, { text });
        setResult({ type: "anomalies", value: response.data });
      }
    } catch (err) {
      setError(apiErrorMessage(err, t));
    } finally {
      setBusy(false);
    }
  }

  if (health && health.status === "not_configured") {
    return (
      <div>
        <h2 style={{ marginTop: 0 }}>{t("aiPage.title")}</h2>
        <div className="panel" style={{ borderLeft: "5px solid #f59e0b" }}>
          <h3 style={{ marginTop: 0 }}>{t("aiPage.notConfigured")}</h3>
          <p style={{ color: "#475569" }}>{t("aiPage.notConfiguredHelp")}</p>
          <pre
            style={{
              background: "#0f172a",
              color: "#e2e8f0",
              padding: "12px",
              borderRadius: "8px",
              overflowX: "auto",
              fontSize: "13px",
            }}
          >
{`# .env dosyasına ekleyin (program kapanmadan etkin olur):
AI_API_KEY=anahtar
AI_BASE_URL=https://api.groq.com/openai/v1
AI_MODEL=llama-3.3-70b-versatile`}
          </pre>
          <p style={{ color: "#64748b", fontSize: "13px" }}>{t("aiPage.optionalNote")}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>{t("aiPage.title")}</h2>
      <p style={{ color: "#64748b", marginTop: -6 }}>{t("aiPage.subtitle")}</p>

      <div className="panel">
        <label className="section-label">{t("aiPage.textLabel")}</label>
        <textarea
          className="form-input"
          rows={8}
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={t("aiPage.textPlaceholder")}
        />
        <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
          <button className="primary-button" type="button" disabled={busy} onClick={() => run("summarize")}>
            {busy ? t("common.processing") : t("aiPage.summarize")}
          </button>
          <button className="secondary-button" type="button" disabled={busy} onClick={() => run("anomalies")}>
            {t("aiPage.anomalies")}
          </button>
        </div>
      </div>

      {error && <div className="panel" style={{ color: "#b91c1c" }}>{error}</div>}

      {result?.type === "summarize" && (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>{t("aiPage.summary")}</h3>
          <p style={{ whiteSpace: "pre-wrap", color: "#334155" }}>{result.value}</p>
        </div>
      )}

      {result?.type === "anomalies" && (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>{t("aiPage.anomalies")}</h3>
          <p style={{ color: "#475569" }}>{result.value.summary}</p>
          <ul style={{ paddingLeft: "18px" }}>
            {(result.value.anomalies || []).map((item, index) => (
              <li key={index} style={{ marginBottom: "8px" }}>
                <strong>{item.severity.toUpperCase()}</strong> — {item.description}
                {item.recommendation ? ` (${item.recommendation})` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
