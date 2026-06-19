export const colors = {
  bg: 'var(--color-bg)',
  cardBg: 'var(--color-card-bg)',
  border: 'var(--color-border)',
  textPrimary: 'var(--color-text-primary)',
  textSecondary: 'var(--color-text-secondary)',
  textTertiary: 'var(--color-text-tertiary)',
  accent: '#2563EB',
  success: '#059669',
  warning: '#D97706',
  danger: '#DC2626',
  causes: {
    vehicle_breakdown: '#2563EB',
    accident: '#DC2626',
    water_logging: '#0891B2',
    construction: '#D97706',
    public_event: '#7C3AED',
    others: '#6B7280'
  }
};

export const typography = {
  fontFamily: "'Inter', 'Noto Sans Kannada', sans-serif",
  label: {
    fontFamily: "'Inter', sans-serif",
    fontSize: '11px',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: 'var(--color-text-secondary)',
    fontWeight: '600'
  },
  value: {
    fontFamily: "'Inter', sans-serif",
    fontSize: '14px',
    fontWeight: '500',
    color: 'var(--color-text-primary)'
  },
  body: {
    fontFamily: "'Inter', 'Noto Sans Kannada', sans-serif",
    fontSize: '13px',
    color: 'var(--color-text-primary)',
    lineHeight: '1.6'
  },
  header: {
    fontFamily: "'Inter', sans-serif",
    fontSize: '16px',
    fontWeight: '500',
    color: 'var(--color-text-primary)'
  },
  subtitle: {
    fontFamily: "'Inter', sans-serif",
    fontSize: '12px',
    color: 'var(--color-text-secondary)'
  }
};

export const layout = {
  pagePadding: '24px',
  cardPadding: '20px',
  gap: '16px'
};

export const cards = {
  base: {
    backgroundColor: 'var(--color-card-bg)',
    border: '1px solid var(--color-border)',
    borderRadius: '8px',
    boxShadow: 'none',
    padding: '20px',
    transition: 'transform 150ms ease, background-color 150ms ease, border-color 150ms ease'
  }
};

export const buttons = {
  primary: {
    backgroundColor: '#2563EB',
    color: '#FFFFFF', // Keep button text explicitly white since button bg is dark blue
    borderRadius: '6px',
    padding: '8px 16px',
    fontSize: '13px',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    fontFamily: "'Inter', sans-serif",
    transition: 'opacity 150ms ease'
  },
  secondary: {
    backgroundColor: 'var(--color-card-bg)',
    border: '1px solid var(--color-border)',
    borderRadius: '6px',
    color: 'var(--color-text-primary)',
    padding: '8px 16px',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    fontFamily: "'Inter', sans-serif",
    transition: 'background-color 150ms ease, color 150ms ease'
  }
};
