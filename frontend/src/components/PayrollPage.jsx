import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";

import { API_URL } from "../config";
import { apiErrorMessage } from "../utils/apiError";

const PAYMENT_TYPES = ["salary", "bonus", "advance", "other"];
const CURRENCIES = ["USD", "EUR", "TRY", "GBP"];

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Maaş / ödeme takibi.
 *
 * Kayıtlar veritabanında tutulur; önceki sürümde bellek listesi olduğu için
 * sunucu yeniden başlayınca kayboluyordu.
 */
export default function PayrollPage({ crewList = [], canWrite = false }) {
  const { t } = useTranslation();
  const [payments, setPayments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [filterCrew, setFilterCrew] = useState("");
  const [form, setForm] = useState({
    crew_member_id: "",
    amount: "",
    currency: "USD",
    payment_type: "salary",
    description: "",
    payment_date: todayIso(),
  });

  const loadPayments = useCallback(async () => {
    setLoading(true);
    try {
      const params = filterCrew ? { crew_member_id: Number(filterCrew) } : {};
      const [listResponse, summaryResponse] = await Promise.all([
        axios.get(`${API_URL}/api/salary/`, { params }),
        axios.get(`${API_URL}/api/salary/summary`),
      ]);
      setPayments(listResponse.data);
      setSummary(summaryResponse.data);
      setError(null);
    } catch (err) {
      setError(apiErrorMessage(err, t));
    } finally {
      setLoading(false);
    }
  }, [filterCrew, t]);

  useEffect(() => {
    loadPayments();
  }, [loadPayments]);

  function crewName(crewId) {
    const crew = crewList.find((item) => item.id === crewId);
    return crew ? `${crew.first_name} ${crew.last_name}` : `#${crewId}`;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!form.crew_member_id || !form.amount) return;
    setSaving(true);
    try {
      await axios.post(`${API_URL}/api/salary/`, {
        crew_member_id: Number(form.crew_member_id),
        amount: Number(form.amount),
        currency: form.currency,
        payment_type: form.payment_type,
        description: form.description,
        payment_date: form.payment_date,
      });
      setForm({ ...form, amount: "", description: "" });
      await loadPayments();
    } catch (err) {
      alert(apiErrorMessage(err, t));
    } finally {
      setSaving(false);
    }
  }

  async function removePayment(payment) {
    if (!window.confirm(t("payroll.deleteConfirm"))) return;
    try {
      await axios.delete(`${API_URL}/api/salary/${payment.id}`);
      await loadPayments();
    } catch (err) {
      alert(apiErrorMessage(err, t));
    }
  }

  const totals = summary?.totals_by_currency || {};

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>{t("payroll.title")}</h2>
      <p style={{ color: "#64748b", marginTop: -6 }}>{t("payroll.subtitle")}</p>

      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "20px" }}>
        {Object.keys(totals).length === 0 && (
          <div className="panel" style={{ flex: 1 }}>{t("common.noData")}</div>
        )}
        {Object.entries(totals).map(([currency, total]) => (
          <div className="panel" key={currency} style={{ flex: "1 1 180px" }}>
            <p className="section-label" style={{ margin: 0 }}>{currency}</p>
            <h3 style={{ margin: "6px 0 0 0", color: "#ea580c" }}>
              {total.toLocaleString(undefined, { minimumFractionDigits: 2 })} {currency}
            </h3>
          </div>
        ))}
      </div>

      {canWrite && (
        <form className="panel" onSubmit={handleSubmit} style={{ marginBottom: "20px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "12px" }}>
            <div>
              <label className="section-label">{t("crew.title")}</label>
              <select
                className="form-input"
                value={form.crew_member_id}
                onChange={(event) => setForm({ ...form, crew_member_id: event.target.value })}
                required
              >
                <option value="">-- {t("crew.title")} --</option>
                {crewList.map((crew) => (
                  <option key={crew.id} value={crew.id}>
                    {crew.first_name} {crew.last_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="section-label">{t("payroll.amount")}</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0.01"
                value={form.amount}
                onChange={(event) => setForm({ ...form, amount: event.target.value })}
                required
              />
            </div>
            <div>
              <label className="section-label">{t("payroll.currency")}</label>
              <select
                className="form-input"
                value={form.currency}
                onChange={(event) => setForm({ ...form, currency: event.target.value })}
              >
                {CURRENCIES.map((currency) => (
                  <option key={currency} value={currency}>{currency}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="section-label">{t("payroll.type")}</label>
              <select
                className="form-input"
                value={form.payment_type}
                onChange={(event) => setForm({ ...form, payment_type: event.target.value })}
              >
                {PAYMENT_TYPES.map((type) => (
                  <option key={type} value={type}>{t(`payroll.types.${type}`)}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 3fr", gap: "12px", marginTop: "12px" }}>
            <div>
              <label className="section-label">{t("payroll.paymentDate")}</label>
              <input
                className="form-input"
                type="date"
                value={form.payment_date}
                onChange={(event) => setForm({ ...form, payment_date: event.target.value })}
              />
            </div>
            <div>
              <label className="section-label">{t("payroll.description")}</label>
              <input
                className="form-input"
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </div>
          </div>
          <button className="primary-button" type="submit" disabled={saving} style={{ marginTop: "12px" }}>
            {saving ? t("common.saving") : t("payroll.addPayment")}
          </button>
        </form>
      )}

      <div className="panel" style={{ marginBottom: "12px", display: "flex", gap: "10px", alignItems: "center" }}>
        <label className="section-label" style={{ margin: 0 }}>{t("crew.title")}</label>
        <select
          className="form-input"
          style={{ maxWidth: "280px" }}
          value={filterCrew}
          onChange={(event) => setFilterCrew(event.target.value)}
        >
          <option value="">{t("common.all")}</option>
          {crewList.map((crew) => (
            <option key={crew.id} value={crew.id}>
              {crew.first_name} {crew.last_name}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="panel" style={{ color: "#b91c1c" }}>{error}</div>}
      {loading && <p>{t("common.loading")}</p>}
      {!loading && payments.length === 0 && <div className="panel">{t("common.noData")}</div>}

      {payments.length > 0 && (
        <div className="table-wrapper">
          <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "#64748b" }}>
                <th>{t("common.date")}</th>
                <th>{t("crew.title")}</th>
                <th>{t("payroll.type")}</th>
                <th>{t("payroll.amount")}</th>
                <th>{t("payroll.description")}</th>
                {canWrite && <th />}
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "9px 8px" }}>{payment.payment_date}</td>
                  <td style={{ padding: "9px 8px", fontWeight: 600 }}>{crewName(payment.crew_member_id)}</td>
                  <td style={{ padding: "9px 8px" }}>{t(`payroll.types.${payment.payment_type}`)}</td>
                  <td style={{ padding: "9px 8px" }}>
                    {payment.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} {payment.currency}
                  </td>
                  <td style={{ padding: "9px 8px", color: "#64748b" }}>{payment.description || "—"}</td>
                  {canWrite && (
                    <td style={{ padding: "9px 8px", textAlign: "right" }}>
                      <button className="secondary-button" type="button" onClick={() => removePayment(payment)}>
                        {t("common.delete")}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
