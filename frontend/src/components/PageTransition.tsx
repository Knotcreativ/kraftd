import React from 'react';
import './PageTransition.css';

interface PageTransitionProps {
  children: React.ReactNode;
}

/**
 * Page Transition Component
 * Provides fade-in animation when pages load
 * Creates smooth visual transition between different pages
 */
const PageTransition: React.FC<PageTransitionProps> = ({ children }) => {
  return <div className="page-transition">{children}</div>;
};

export default PageTransition;
