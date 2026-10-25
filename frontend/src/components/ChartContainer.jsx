import React from 'react';

export default function ChartContainer({ title, subtitle, children, kicker = "ANALYTICS" }) {
  return (
    <div className="card space-y-3">
      <div>
        <p className="kicker" style={{ margin: '0 0 6px' }}>{kicker}</p>
        <h3 className="card-title">{title}</h3>
        {subtitle && <p className="text-xs text-[#69716d] mt-1">{subtitle}</p>}
      </div>
      <div className="pt-2">
        {children}
      </div>
    </div>
  );
}
