export const colors = {
  primary: "#4f46e5",
  primaryHover: "#4338ca",
  accent: "#8b5cf6",
  sidebar: "#0f172a",
  background: "#f8fafc",
  surface: "#ffffff",
  border: "rgba(226, 232, 240, 0.8)",
  textPrimary: "#1e293b",
  textSecondary: "#64748b",
  textMuted: "#94a3b8",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
} as const;

export const shadows = {
  sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.07)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.08)",
  indigoGlow: "0 4px 14px 0 rgba(79, 70, 229, 0.3)",
} as const;

export const radius = {
  sm: "6px",
  md: "8px",
  lg: "12px",
  xl: "16px",
  full: "9999px",
} as const;

export const spacing = {
  sidebarWidth: "280px",
  headerHeight: "64px",
} as const;
