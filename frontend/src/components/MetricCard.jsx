import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, badge, tone = 'sage' }) {
  const badgeClasses = {
    sage: 'badge-sage',
    coral: 'badge-coral',
    blue: 'badge-blue',
    yellow: 'badge-yellow',
    rose: 'badge-rose',
  }[tone] || 'badge-sage';

  return (
    <div className="card flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <p className="kicker" style={{ margin: 0 }}>{title}</p>
          {badge && <span className={`badge ${badgeClasses}`}>{badge}</span>}
        </div>
        <div className="stat-number my-1">{value}</div>
      </div>
      <div className="flex items-center justify-between pt-3 border-t border-[#edf1ed] mt-2">
        <span className="text-xs text-[#69716d]">{subtitle}</span>
        {Icon && (
          <div className="text-[#69716d]">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
    </div>
  );
}
