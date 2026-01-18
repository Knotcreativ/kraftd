import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Breadcrumb.css';

interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: string;
}

/**
 * Breadcrumb Navigation Component
 * Shows navigation hierarchy and current page location
 * Includes home icon, page labels, and clickable navigation links
 */
const Breadcrumb: React.FC = () => {
  const location = useLocation();

  // Define breadcrumb paths for each route
  const breadcrumbMap: { [key: string]: BreadcrumbItem[] } = {
    '/dashboard': [
      { label: 'Home', path: '/dashboard', icon: '🏠' },
      { label: 'Dashboard', icon: '📊' },
    ],
    '/analytics': [
      { label: 'Home', path: '/dashboard', icon: '🏠' },
      { label: 'Analytics', icon: '📈' },
    ],
    '/analytics/charts': [
      { label: 'Home', path: '/dashboard', icon: '🏠' },
      { label: 'Analytics', path: '/analytics', icon: '📈' },
      { label: 'Charts', icon: '📊' },
    ],
    '/dashboard/custom': [
      { label: 'Home', path: '/dashboard', icon: '🏠' },
      { label: 'Dashboard', path: '/dashboard', icon: '📊' },
      { label: 'Custom Builder', icon: '🛠️' },
    ],
    '/preferences': [
      { label: 'Home', path: '/dashboard', icon: '🏠' },
      { label: 'Preferences', icon: '⚙️' },
    ],
    '/preferences/alerts': [
      { label: 'Home', path: '/dashboard', icon: '🏠' },
      { label: 'Preferences', path: '/preferences', icon: '⚙️' },
      { label: 'Alert Settings', icon: '🔔' },
    ],
    '/preferences/notifications': [
      { label: 'Home', path: '/dashboard', icon: '🏠' },
      { label: 'Preferences', path: '/preferences', icon: '⚙️' },
      { label: 'Notifications', icon: '📬' },
    ],
  };

  // Get breadcrumbs for current path
  const currentPath = location.pathname;
  const breadcrumbs = breadcrumbMap[currentPath] || [
    { label: 'Home', path: '/dashboard', icon: '🏠' },
  ];

  return (
    <nav className="breadcrumb-nav" aria-label="Breadcrumb">
      <ol className="breadcrumb-list">
        {breadcrumbs.map((item, index) => (
          <li key={index} className="breadcrumb-item">
            {item.path ? (
              <>
                <Link to={item.path} className="breadcrumb-link">
                  {item.icon && <span className="breadcrumb-icon">{item.icon}</span>}
                  <span className="breadcrumb-label">{item.label}</span>
                </Link>
                {index < breadcrumbs.length - 1 && (
                  <span className="breadcrumb-separator">/</span>
                )}
              </>
            ) : (
              <>
                <span className="breadcrumb-current">
                  {item.icon && <span className="breadcrumb-icon">{item.icon}</span>}
                  <span className="breadcrumb-label">{item.label}</span>
                </span>
              </>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

export default Breadcrumb;
