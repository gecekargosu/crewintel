// CREWINTEL Mobile — i18n Types
// Type-safe translation keys

export type SupportedLanguage = 'tr' | 'en' | 'ru' | 'ar';

export interface LanguageOption {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag: string;
  dir: 'ltr' | 'rtl';
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷', dir: 'ltr' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧', dir: 'ltr' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺', dir: 'ltr' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', dir: 'rtl' },
];

export const DEFAULT_LANGUAGE: SupportedLanguage = 'tr';

// Translation key structure
export interface Translations {
  // App
  appName: string;
  appSubtitle: string;

  // Navigation
  nav: {
    home: string;
    jobs: string;
    applications: string;
    documents: string;
    messages: string;
    profile: string;
  };

  // Auth
  auth: {
    loginTitle: string;
    registerTitle: string;
    email: string;
    password: string;
    passwordConfirm: string;
    firstName: string;
    lastName: string;
    phone: string;
    loginButton: string;
    loginLoading: string;
    registerButton: string;
    registerLoading: string;
    noAccount: string;
    registerLink: string;
    hasAccount: string;
    loginLink: string;
    pendingApproval: string;
    pendingDescription: string;
    pendingSteps: string;
    backToLogin: string;
    logout: string;
    logoutConfirm: string;

    staffOnlyTitle: string;
    staffOnlyHint: string;

    forgotHint: string;
  };

  // Home
  home: {
    greeting: string;
    user: string;
    heroTitle: string;
    heroSubtitle: string;
    heroCta: string;
    profileCompletion: string;
    availabilityStatus: string;
    documents: string;
    contracts: string;
    notifications: string;
    expiring: string;
    expiringDocuments: string;
    expiringInDays: string;
    daysRemaining: string;
    recommendedJobs: string;
    seeAll: string;
    recentNotifications: string;
    quickActions: string;
    noJobsHint: string;
    matchScore: string;
    browseJobs: string;
    viewProfile: string;
    myApplications: string;
  };

  // Jobs
  jobs: {
    title: string;
    count: string;
    position: string;
    company: string;
    location: string;
    vesselType: string;
    salary: string;
    duration: string;
    months: string;
    active: string;
    empty: string;
    emptyDescription: string;
    detail: string;
    details: string;
    description: string;
    requirements: string;
    apply: string;
    applying: string;
    applied: string;
    confirmApply: string;
    confirmApplyMessage: string;
  };

  // Applications
  applications: {
    title: string;
    count: string;
    matchScore: string;
    appliedAt: string;
    source: string;
    mobile: string;
    empty: string;
    emptyDescription: string;
    browseJobs: string;
    statusPending: string;
    statusReviewing: string;
    statusApproved: string;
    statusShortlisted: string;
    statusRejected: string;
    statusUnknown: string;
  };

  // Messages
  messages: {
    title: string;
    empty: string;
    emptyDescription: string;
    typePlaceholder: string;
    noMessages: string;
    conversation: string;

    userFallback: string;
    noMessage: string;
  };

  // Profile
  profile: {
    title: string;
    personalInfo: string;
    maritimeInfo: string;
    documents: string;
    preferences: string;
    position: string;
    nationality: string;
    telephone: string;
    email: string;
    dateOfBirth: string;
    address: string;
    rank: string;
    coc: string;
    seaService: string;
    years: string;
    valid: string;
    expired: string;
    expiringSoon: string;
    noDate: string;
    preferredRank: string;
    preferredVessel: string;
    jobStatus: string;
    jobSeeking: string;
    notDefined: string;
    activeDuty: string;
    logoutButton: string;
    language: string;

    availableNow: string;
    availableSoon: string;
    jobPassive: string;

    contactTitle: string;
    contactUpdated: string;

    onLeave: string;
    notAvailable: string;
  };

  // Common
  common: {
    save: string;
    cancel: string;
    close: string;
    confirm: string;
    delete: string;
    retry: string;
    loading: string;
    error: string;
    success: string;
    back: string;
    more: string;
    less: string;
    days: string;
    months: string;
    year: string;
    years: string;
  };

  // Errors
  errors: {
    network: string;
    unknown: string;
    invalidCredentials: string;
    sessionExpired: string;
    unauthorized: string;
    notFound: string;
    validation: string;
    server: string;
    uploadFailed: string;
    loadFailed: string;
  };

  // Validation
  validation: {
    required: string;
    invalidEmail: string;
    passwordTooShort: string;
    passwordMismatch: string;
    invalidPhone: string;
  };

  // Dates
  dates: {
    today: string;
    yesterday: string;
    daysAgo: string;
    hoursAgo: string;
    minutesAgo: string;
    justNow: string;
  };

  // Crew documents tab
  documentsTab: {
    title: string;
    subtitle: string;
    uploadTitle: string;
    uploadHint: string;
    uploadButton: string;
    uploadDone: string;
    uploadDoneHint: string;
    uploadError: string;
    loadError: string;
    empty: string;
    issueDate: string;
    expiryDate: string;
    status: string;

    statusExpired: string;
    statusUrgent: string;
    statusApproaching: string;
    statusValid: string;
    statusPendingApproval: string;
    statusPending: string;
    statusProcessing: string;
    statusNoDate: string;
    statusUnknown: string;
    typePassport: string;
    typeSeamanBook: string;
    typeStcw: string;
    typeGoc: string;
    typeMedical: string;
    typeContract: string;
    typeCv: string;
    typeOther: string;
    detailsTitle: string;
  };
}
