import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  Activity,
  ClipboardList,
  FileText,
  Folder,
  LayoutDashboard,
  Menu,
  Ship,
  Upload,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const emptyCrewForm = {
  first_name: "",
  last_name: "",
  position: "",
  nationality: "",
};

function App() {
  const [crew, setCrew] = useState([]);
  const [ships, setShips] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [apiStatus, setApiStatus] = useState("Kontrol ediliyor...");
  const [menuOpen, setMenuOpen] = useState(true);
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedCrewId, setSelectedCrewId] = useState(null);
  const [selectedShipId, setSelectedShipId] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [crewForm, setCrewForm] = useState(emptyCrewForm);
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expirySummary, setExpirySummary] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState(null);
  const [stagedFiles, setStagedFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({});
  const [uploadResults, setUploadResults] = useState({});
  const [uploadProgress, setUploadProgress] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const crewById = useMemo(
    () => Object.fromEntries(crew.map((member) => [member.id, member])),
    [crew],
  );
  const shipById = useMemo(
    () => Object.fromEntries(ships.map((ship) => [ship.id, ship])),
    [ships],
  );
  const selectedCrew = crewById[selectedCrewId];
  const selectedShip = shipById[selectedShipId];

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [health, crewResponse, shipsResponse, assignmentsResponse, contractsResponse, expiryResponse] = await Promise.all([
        axios.get(`${API_URL}/health`),
        axios.get(`${API_URL}/api/crew/`),
        axios.get(`${API_URL}/api/ships/`),
        axios.get(`${API_URL}/api/assignments/`),
        axios.get(`${API_URL}/api/contracts/`),
        axios.get(`${API_URL}/api/expiration/summary`),
      ]);
      setApiStatus(health.data.status === "healthy" ? "Sistem Aktif" : "Sorun Var");
      setCrew(crewResponse.data);
      setShips(shipsResponse.data);
      setAssignments(assignmentsResponse.data);
      setContracts(contractsResponse.data);
      setExpirySummary(expiryResponse.data);
    } catch {
      setApiStatus("Backend Bağlantısı Yok");
    }
  }

  function handleFormChange(event) {
    const { name, value } = event.target;
    setCrewForm((currentForm) => ({ ...currentForm, [name]: value }));
  }

  async function handleCrewSubmit(event) {
    event.preventDefault();
    setFormError("");
    setIsSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/crew/`, {
        ...crewForm,
        nationality: crewForm.nationality || null,
      });
      setCrewForm(emptyCrewForm);
      setIsFormOpen(false);
      await loadData();
    } catch {
      setFormError("Personel kaydedilemedi. Alanları ve backend bağlantısını kontrol edin.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function openCrewDetail(crewId) {
    setSelectedCrewId(crewId);
    setActivePage("crew-detail");
  }

  function openShipDetail(shipId) {
    setSelectedShipId(shipId);
    setActivePage("ship-detail");
  }

  async function loadDocuments() {
    setDocumentsLoading(true);
    setDocumentsError(null);
    try {
      const response = await axios.get(`${API_URL}/api/documents/`);
      setDocuments(response.data);
    } catch {
      setDocumentsError("Belgeler yüklenirken bir hata oluştu. Backend bağlantısını kontrol edin.");
    } finally {
      setDocumentsLoading(false);
    }
  }

  function openDocumentsPage() {
    setActivePage("documents");
    loadDocuments();
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function computeUploadSummary() {
    if (isUploading) return null;
    const attempted = stagedFiles.filter((file) => {
      const s = uploadStatus[fileKey(file)];
      return s === "success" || s === "duplicate" || s === "error";
    });
    if (attempted.length === 0) return null;

    let matched = 0;
    let pending = 0;
    let duplicate = 0;
    let error = 0;
    attempted.forEach((file) => {
      const key = fileKey(file);
      const s = uploadStatus[key];
      if (s === "duplicate") duplicate += 1;
      else if (s === "error") error += 1;
      else if (s === "success") {
        // "success" upload'in basarili oldugunu gosterir; belgenin bir crew member'a
        // eslesip eslesmedigi ayri bir backend alani: document.match_status.
        // CSS'te "matched"/"pending" kategorileri buna gore ayriliyor ("unmatched" da
        // pending kovasina dahil ediliyor, ayri bir CSS sinifi yok).
        const matchStatus = uploadResults[key]?.document?.match_status;
        if (matchStatus === "matched") matched += 1;
        else pending += 1;
      }
    });
    return { total: attempted.length, matched, pending, duplicate, error };
  }

  function addStagedFiles(newFiles) {
    setStagedFiles((prev) => {
      const existingKeys = new Set(prev.map((file) => `${file.name}_${file.size}`));
      const deduped = newFiles.filter((file) => !existingKeys.has(`${file.name}_${file.size}`));
      return [...prev, ...deduped];
    });
  }

  function removeStagedFile(index) {
    setStagedFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function handleFileInputChange(event) {
    addStagedFiles(Array.from(event.target.files));
    event.target.value = "";
  }

  function handleDragOver(event) {
    event.preventDefault();
    setDragActive(true);
  }

  function handleDragLeave(event) {
    event.preventDefault();
    setDragActive(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragActive(false);
    addStagedFiles(Array.from(event.dataTransfer.files));
  }

  function fileKey(file) {
    return `${file.name}_${file.size}`;
  }

  async function uploadSingleFile(file) {
    const key = fileKey(file);
    setUploadStatus((prev) => ({ ...prev, [key]: "uploading" }));
    setUploadProgress((prev) => ({ ...prev, [key]: null }));

    const formData = new FormData();
    formData.append("files", file);
    const requestSentAt = Date.now();

    try {
      const response = await axios.post(`${API_URL}/api/documents/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            setUploadProgress((prev) => ({ ...prev, [key]: percent }));
          }
        },
      });
      const document = response.data[0];
      // Backend duplicate icin ayri bir flag dondurmuyor (bkz. 7B-01).
      // Heuristik: created_at, istek atilmadan hemen once yakalanan zamandan
      // belirgin sekilde eskiyse (ESIK'ten fazla), bu mevcut bir kayittir -> duplicate.
      // created_at backend'de tz-naive UTC olarak donuyor, bu yuzden "Z" eklenerek parse ediliyor.
      const DUPLICATE_THRESHOLD_MS = 3000;
      const createdAtMs = new Date(`${document.created_at}Z`).getTime();
      const isDuplicate = !Number.isNaN(createdAtMs) && (requestSentAt - createdAtMs) > DUPLICATE_THRESHOLD_MS;
      const finalStatus = isDuplicate ? "duplicate" : "success";
      setUploadStatus((prev) => ({ ...prev, [key]: finalStatus }));
      setUploadResults((prev) => ({ ...prev, [key]: { document, duplicate: isDuplicate } }));
      return { status: finalStatus, document };
    } catch (error) {
      // 7B-01'de yalnızca 422 (bos dosya) ve 413 (boyut asimi) backend'de dogrulandi;
      // baska kodlar icin ozel bir yorum uydurulmuyor, gelen ham HTTP status ve
      // backend detail mesaji oldugu gibi tasiniyor.
      const httpStatus = error.response?.status ?? null;
      const backendDetail = error.response?.data?.detail;
      const hasBackendDetail = typeof backendDetail === "string";
      const isNetworkError = !error.response;
      const message = hasBackendDetail
        ? backendDetail
        : isNetworkError
          ? "Sunucuya bağlanılamadı (ağ hatası)."
          : (error.message || "Yükleme başarısız.");
      setUploadStatus((prev) => ({ ...prev, [key]: "error" }));
      setUploadResults((prev) => ({
        ...prev,
        [key]: { error: message, httpStatus, source: isNetworkError ? "network" : "backend" },
      }));
      return { status: "error", error: message, httpStatus };
    }
  }

  async function uploadStagedFiles() {
    if (isUploading) return;
    setIsUploading(true);

    for (const file of stagedFiles) {
      const key = fileKey(file);
      if (uploadStatus[key] === "uploading" || uploadStatus[key] === "success") continue;
      await uploadSingleFile(file);
    }

    setIsUploading(false);
    loadDocuments();
  }

  async function retryUpload(file) {
    const key = fileKey(file);
    // Yalnizca gercekten "error" durumundaki dosya tekrar denenir.
    // success/duplicate dosyalar bu fonksiyona hic ulasmiyor (buton yalnizca
    // status === "error" iken render ediliyor), ayrica cift-tiklama korumasi:
    if (uploadStatus[key] !== "error") return;
    await uploadSingleFile(file);
    loadDocuments();
  }

  function renderCrewForm() {
    if (!isFormOpen) return null;
    return (
      <form className="crew-form" onSubmit={handleCrewSubmit}>
        <label>Ad<input name="first_name" value={crewForm.first_name} onChange={handleFormChange} required /></label>
        <label>Soyad<input name="last_name" value={crewForm.last_name} onChange={handleFormChange} required /></label>
        <label>Pozisyon<input name="position" value={crewForm.position} onChange={handleFormChange} required /></label>
        <label>Uyruk<input name="nationality" value={crewForm.nationality} onChange={handleFormChange} /></label>
        {formError && <p className="form-error">{formError}</p>}
        <div className="form-actions">
          <button className="secondary-button" type="button" onClick={() => setIsFormOpen(false)}>Vazgeç</button>
          <button className="primary-button" type="submit" disabled={isSubmitting}>{isSubmitting ? "Kaydediliyor..." : "Kaydet"}</button>
        </div>
      </form>
    );
  }

  function renderCrewList() {
    return (
      <section className="panel">
        <div className="panel-header"><div><h2>Personel</h2><p>Tüm personel kayıtları</p></div>
          <button className="primary-button" onClick={() => { setFormError(""); setIsFormOpen(true); }}><UserPlus size={18} /> Personel Ekle</button>
        </div>
        {renderCrewForm()}
        <div className="entity-list">
          {crew.map((member) => <button className="entity-row" key={member.id} onClick={() => openCrewDetail(member.id)}><strong>{member.first_name} {member.last_name}</strong><span>{member.position} · {member.status}</span></button>)}
          {crew.length === 0 && <div className="empty"><Users size={42} /><h3>Henüz personel bulunmuyor</h3></div>}
        </div>
      </section>
    );
  }

  function formatProfileData(profileData) {
    if (!profileData || Object.keys(profileData).length === 0) return "—";
    return JSON.stringify(profileData, null, 2);
  }

  function renderCrewDetail() {
    return (
      <section className="panel detail-panel">
        <button className="back-button" onClick={() => setActivePage("crew")}>← Personel listesine dön</button>
        {selectedCrew ? (
          <>
            <h2>{selectedCrew.first_name} {selectedCrew.last_name}</h2>
            <p className="section-label">Temel Bilgiler</p>
            <div className="detail-grid">
              <span>Pozisyon</span>      <strong>{selectedCrew.position || "—"}</strong>
              <span>Rütbe</span>         <strong>{selectedCrew.rank || "—"}</strong>
              <span>Uyruk</span>         <strong>{selectedCrew.nationality || "—"}</strong>
              <span>Durum</span>         <strong>{selectedCrew.status}</strong>
              <span>E-posta</span>       <strong>{selectedCrew.email || "—"}</strong>
              <span>Telefon</span>       <strong>{selectedCrew.phone || "—"}</strong>
            </div>
            <p className="section-label">Kişisel Bilgiler</p>
            <div className="detail-grid">
              <span>Doğum Yeri</span>          <strong>{selectedCrew.birth_place || "—"}</strong>
              <span>Memleket</span>             <strong>{selectedCrew.hometown || "—"}</strong>
              <span>Medeni Durum</span>         <strong>{selectedCrew.marital_status || "—"}</strong>
              <span>Deniz Tecrübesi (yıl)</span> <strong>{selectedCrew.experience_years != null ? selectedCrew.experience_years : "—"}</strong>
              <span>Deniz Hizmeti (ay)</span>   <strong>{selectedCrew.sea_service_months != null ? selectedCrew.sea_service_months : "—"}</strong>
              <span>Diller</span>               <strong>{selectedCrew.languages || "—"}</strong>
            </div>
            <p className="section-label">Ek Bilgiler</p>
            <div className="detail-grid">
              <span>Eğitim</span>  <strong>{selectedCrew.education_summary || "—"}</strong>
              <span>Notlar</span>  <strong>{selectedCrew.notes || "—"}</strong>
            </div>
            {selectedCrew.profile_data && Object.keys(selectedCrew.profile_data).length > 0 && (
              <>
                <p className="section-label">Profil Verisi</p>
                <pre className="profile-data-block">{formatProfileData(selectedCrew.profile_data)}</pre>
              </>
            )}
          </>
        ) : (
          <p>Personel bulunamadı.</p>
        )}
      </section>
    );
  }

  function renderDocumentsList() {
    const uploadSummary = computeUploadSummary();
    return (
      <section className="panel">
        <div className="panel-header"><div><h2>Belgeler</h2><p>Yüklenen personel belgeleri</p></div></div>
        {uploadSummary && (
          <div className="upload-summary">
            <div className="upload-stat matched"><strong>{uploadSummary.matched}</strong><span>Eşleşti</span></div>
            <div className="upload-stat pending"><strong>{uploadSummary.pending}</strong><span>Eşleşme bekliyor</span></div>
            <div className="upload-stat duplicate"><strong>{uploadSummary.duplicate}</strong><span>Zaten yüklenmiş</span></div>
            <div className="upload-stat error"><strong>{uploadSummary.error}</strong><span>Hatalı</span></div>
          </div>
        )}
        <div
          className={`upload-zone ${dragActive ? "drag-over" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={36} />
          <h3>Belgeleri buraya sürükleyin</h3>
          <p>veya tıklayarak seçin — PDF, TXT (çoklu dosya desteklenir)</p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt"
            style={{ display: "none" }}
            onChange={handleFileInputChange}
          />
        </div>
        {stagedFiles.length > 0 && (
          <div className="file-list">
            {stagedFiles.map((file, index) => {
              const key = fileKey(file);
              const status = uploadStatus[key] || "pending";
              const result = uploadResults[key];
              const progress = uploadProgress[key];
              const statusLabel =
                status === "uploading" ? (typeof progress === "number" ? `Yükleniyor... %${progress}` : "Yükleniyor...") :
                status === "success" ? "Yüklendi" :
                status === "duplicate" ? "Zaten yüklenmiş (duplicate)" :
                status === "error" ? `Hata${result?.httpStatus ? ` (HTTP ${result.httpStatus})` : ""}: ${result?.error || "bilinmiyor"}` :
                "Bekliyor";
              return (
                <div className="file-item" key={`${file.name}_${file.size}_${index}`}>
                  <span className="file-item-name">{file.name}</span>
                  <span>{formatFileSize(file.size)}</span>
                  <span className="file-item-status">{statusLabel}</span>
                  {status === "error" && (
                    <button className="icon-button" type="button" onClick={() => retryUpload(file)}>
                      Tekrar Dene
                    </button>
                  )}
                  <button className="icon-button" type="button" onClick={() => removeStagedFile(index)} disabled={status === "uploading"}>
                    <X size={16} />
                  </button>
                </div>
              );
            })}
            <button className="primary-button" type="button" onClick={uploadStagedFiles} disabled={isUploading}>
              {isUploading ? "Yükleniyor..." : `${stagedFiles.length} dosyayı yükle`}
            </button>
          </div>
        )}
        {documentsLoading && <p>Belgeler yükleniyor...</p>}
        {documentsError && <p className="form-error">{documentsError}</p>}
        {!documentsLoading && !documentsError && (
          documents.length === 0 ? (
            <div className="empty"><Folder size={42} /><h3>Henüz belge bulunmuyor</h3></div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Dosya Adı</th>
                  <th>Belge Tipi</th>
                  <th>Eşleşme Durumu</th>
                  <th>Geçerlilik</th>
                  <th>Personel</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => {
                  const matchedCrew = doc.crew_member_id ? crewById[doc.crew_member_id] : null;
                  return (
                    <tr key={doc.id}>
                      <td>{doc.original_filename}</td>
                      <td><span className={`badge badge-type-${doc.document_type}`}>{doc.document_type}</span></td>
                      <td><span className={`badge badge-${doc.match_status}`}>{doc.match_status}</span></td>
                      <td>{doc.expiry_status ? <span className={`badge badge-${doc.expiry_status.replace(/_/g, "-")}`}>{doc.expiry_status}</span> : "—"}</td>
                      <td>{matchedCrew ? `${matchedCrew.first_name} ${matchedCrew.last_name}` : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )
        )}
      </section>
    );
  }

  function renderPage() {
    if (activePage === "crew") return renderCrewList();
    if (activePage === "ships") return <section className="panel"><div className="panel-header"><div><h2>Gemiler</h2><p>Gemi kayıtları</p></div></div><div className="entity-list">{ships.map((ship) => <button className="entity-row" key={ship.id} onClick={() => openShipDetail(ship.id)}><strong>{ship.name}</strong><span>{ship.imo_number || "IMO belirtilmemiş"} · {ship.status}</span></button>)}{ships.length === 0 && <div className="empty"><Ship size={42} /><h3>Henüz gemi bulunmuyor</h3></div>}</div></section>;
    if (activePage === "assignments") return <section className="panel"><div className="panel-header"><div><h2>Gemi Personeli</h2><p>Aktif ve geçmiş atamalar</p></div></div><div className="entity-list">{assignments.map((assignment) => <div className="entity-row static-row" key={assignment.id}><strong>{crewById[assignment.crew_member_id]?.first_name} {crewById[assignment.crew_member_id]?.last_name}</strong><span>{shipById[assignment.ship_id]?.name} · {assignment.position} · {assignment.status}</span></div>)}{assignments.length === 0 && <div className="empty"><ClipboardList size={42} /><h3>Henüz atama bulunmuyor</h3></div>}</div></section>;
    if (activePage === "contracts") return <section className="panel"><div className="panel-header"><div><h2>Kontratlar</h2><p>Personel kontrat kayıtları</p></div></div><div className="entity-list">{contracts.map((contract) => <div className="entity-row static-row" key={contract.id}><strong>{contract.contract_number}</strong><span>{crewById[contract.crew_member_id]?.first_name} {crewById[contract.crew_member_id]?.last_name} · {contract.status}</span></div>)}{contracts.length === 0 && <div className="empty"><FileText size={42} /><h3>Henüz kontrat bulunmuyor</h3></div>}</div></section>;
    if (activePage === "documents") return renderDocumentsList();
    if (activePage === "crew-detail") return renderCrewDetail();
    if (activePage === "ship-detail") { const shipAssignments = assignments.filter((assignment) => assignment.ship_id === selectedShipId); return <section className="panel detail-panel"><button className="back-button" onClick={() => setActivePage("ships")}>← Gemi listesine dön</button>{selectedShip ? <><h2>{selectedShip.name}</h2><div className="detail-grid"><span>IMO</span><strong>{selectedShip.imo_number || "—"}</strong><span>Bayrak</span><strong>{selectedShip.flag || "—"}</strong><span>Tür</span><strong>{selectedShip.ship_type || "—"}</strong><span>Şirket</span><strong>{selectedShip.company || "—"}</strong><span>Durum</span><strong>{selectedShip.status}</strong></div><h3>Gemi Personeli</h3><div className="entity-list">{shipAssignments.map((assignment) => <div className="entity-row static-row" key={assignment.id}><strong>{crewById[assignment.crew_member_id]?.first_name} {crewById[assignment.crew_member_id]?.last_name}</strong><span>{assignment.position} · {assignment.status}</span></div>)}{shipAssignments.length === 0 && <p>Bu gemi için atama bulunmuyor.</p>}</div></> : <p>Gemi bulunamadı.</p>}</section>; }
    return <>
      <div className="welcome"><div><h2>Hoş Geldiniz</h2><p>Crew operasyonlarını, personel bilgilerini ve gemi kadrolarını tek merkezden yönetin.</p></div></div>
      <div className="cards">
        <div className="card"><div className="card-icon"><Users size={24} /></div><div><span>Toplam Personel</span><strong>{crew.length}</strong></div></div>
        <div className="card"><div className="card-icon"><Ship size={24} /></div><div><span>Toplam / Aktif Gemi</span><strong>{ships.length} / {ships.filter((ship) => ship.status === "active").length}</strong></div></div>
        <div className="card"><div className="card-icon"><Activity size={24} /></div><div><span>Aktif Personel / Kontrat</span><strong>{crew.filter((member) => member.status === "active").length} / {contracts.filter((contract) => contract.status === "active").length}</strong></div></div>
      </div>
      {expirySummary !== null && (
        <>
          <p className="section-label">Belge Geçerlilik Durumu</p>
          <div className="cards">
            <div className="card"><div className="card-icon danger"><FileText size={24} /></div><div><span>Süresi Geçmiş</span><strong>{expirySummary.expired}</strong></div></div>
            <div className="card"><div className="card-icon warning"><FileText size={24} /></div><div><span>Acil (≤30 gün)</span><strong>{expirySummary.urgent}</strong></div></div>
            <div className="card"><div className="card-icon purple"><FileText size={24} /></div><div><span>Yaklaşıyor (≤90 gün)</span><strong>{expirySummary.approaching}</strong></div></div>
            <div className="card"><div className="card-icon success"><FileText size={24} /></div><div><span>Geçerli</span><strong>{expirySummary.valid}</strong></div></div>
          </div>
        </>
      )}
      {renderCrewList()}
    </>;
  }

  const navigation = [
    ["dashboard", LayoutDashboard, "Dashboard"], ["crew", Users, "Personel"], ["ships", Ship, "Gemiler"], ["assignments", ClipboardList, "Gemi Personeli"], ["contracts", FileText, "Kontratlar"], ["documents", Folder, "Belgeler"],
  ];

  return <div className="app"><aside className={`sidebar ${menuOpen ? "open" : "closed"}`}><div className="logo"><Ship size={30} />{menuOpen && <span>CREWINTEL</span>}</div><nav>{navigation.map(([page, Icon, label]) => <button className={`nav-item ${activePage === page ? "active" : ""}`} key={page} onClick={() => (page === "documents" ? openDocumentsPage() : setActivePage(page))}><Icon size={20} />{menuOpen && <span>{label}</span>}</button>)}</nav><button className="menu-button" onClick={() => setMenuOpen(!menuOpen)}><Menu size={20} /></button></aside><main className="main"><header className="topbar"><div><h1>CREWINTEL</h1><p>Gemi Personeli ve İnsan Kaynakları Yönetim Sistemi</p></div><div className="status"><Activity size={18} /><span>{apiStatus}</span></div></header><section className="content">{renderPage()}</section></main></div>;
}

export default App;


