import React from 'react';

export default function InfoHint({ text, className = "" }) {
  if (!text) return null;
  return (
    <span className={`info-hint ${className}`} tabIndex={0} role="tooltip" aria-label={text}>
      <span className="hint-trigger" aria-hidden="true">?</span>
      <span className="hint-box">{text}</span>
    </span>
  );
}
