import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, ArrowLeft } from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';

export default function NotFound() {
  usePageTitle('Page Not Found');

  return (
    <div className="card max-w-lg mx-auto my-12 text-center p-8 space-y-4">
      <div className="h-12 w-12 rounded-full bg-[#fdecea] text-[#c0392b] flex items-center justify-center mx-auto">
        <Compass className="h-6 w-6" />
      </div>
      <div>
        <p className="kicker" style={{ margin: 0 }}>404 NAVIGATION ERROR</p>
        <h2 className="text-xl font-bold text-[#18201d]">Destination Route Not Found</h2>
        <p className="text-xs text-[#69716d] mt-1">
          The requested URL path is not a recognized operational dispatch or commuter destination.
        </p>
      </div>
      <div className="pt-2">
        <Link
          to="/office/overview"
          className="coral-button text-xs inline-flex items-center gap-1.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Return to Transport Office Overview</span>
        </Link>
      </div>
    </div>
  );
}
