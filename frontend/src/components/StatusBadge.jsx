import React from 'react';
import { Check, AlertCircle, AlertTriangle } from 'lucide-react';

export default function StatusBadge({ status, size = 'sm' }) {
  const normalized = (status || 'LOW').toUpperCase();

  const configs = {
    LOW: {
      label: 'Low Volume',
      badgeClass: 'badge-sage',
      icon: Check,
    },
    MODERATE: {
      label: 'Moderate',
      badgeClass: 'badge-yellow',
      icon: AlertCircle,
    },
    BUSY: {
      label: 'High Volume',
      badgeClass: 'badge-coral',
      icon: AlertTriangle,
    },
    OVERCROWDED: {
      label: 'Overcrowded',
      badgeClass: 'badge-rose',
      icon: AlertTriangle,
    },
  };

  const cfg = configs[normalized] || configs.LOW;
  const Icon = cfg.icon;

  return (
    <span className={`badge ${cfg.badgeClass} ${size === 'lg' ? 'py-1 px-2.5 text-xs' : 'py-0.5 px-2 text-[10px]'}`}>
      <Icon className={size === 'lg' ? 'h-3.5 w-3.5' : 'h-3 w-3'} />
      <span>{cfg.label}</span>
    </span>
  );
}
