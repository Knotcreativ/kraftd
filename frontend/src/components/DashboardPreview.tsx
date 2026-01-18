import React from 'react';
import DashboardBuilder, { DashboardProfile } from './DashboardBuilder';
import './DashboardPreview.css';

interface DashboardPreviewProps {
  onProfileChange?: (profile: DashboardProfile) => void;
}

/**
 * Dashboard Preview Component
 * 
 * Wraps DashboardBuilder with additional preview features and integrations.
 * Provides a complete dashboard customization interface with:
 * - Multiple dashboard profiles
 * - Drag-and-drop widget reordering
 * - Widget library with 6 widget types
 * - Size management (small/medium/large)
 * - localStorage persistence
 * - Professional UI with edit/view modes
 */
const DashboardPreview: React.FC<DashboardPreviewProps> = ({ onProfileChange }) => {
  const handleProfileChange = (profile: DashboardProfile) => {
    onProfileChange?.(profile);
  };

  const handleSaveProfile = (profile: DashboardProfile) => {
    // Save happens automatically in DashboardBuilder via localStorage
    // This callback can be extended for additional actions
    console.log('Dashboard profile saved:', profile.name);
  };

  return (
    <div className="dashboard-preview-wrapper">
      <DashboardBuilder
        onProfileChange={handleProfileChange}
        onSaveProfile={handleSaveProfile}
      />
      
      {/* Quick Tips */}
      <div className="dashboard-tips">
        <details>
          <summary>💡 Tips & Tricks</summary>
          <div className="tips-content">
            <h4>Getting Started</h4>
            <ul>
              <li><strong>Edit Layout:</strong> Click the "Edit Layout" button to customize your dashboard</li>
              <li><strong>Add Widgets:</strong> Select from the widget library while in edit mode</li>
              <li><strong>Reorder:</strong> Drag widgets to change their position</li>
              <li><strong>Resize:</strong> Use the dropdown in each widget to change its size</li>
              <li><strong>Remove:</strong> Click the × button to remove a widget</li>
            </ul>
            
            <h4>Dashboard Profiles</h4>
            <ul>
              <li><strong>Multiple Profiles:</strong> Create separate dashboards for different purposes</li>
              <li><strong>Default Profile:</strong> Your primary dashboard is marked as DEFAULT</li>
              <li><strong>Switch Profiles:</strong> Click tabs to switch between profiles</li>
              <li><strong>Create Profile:</strong> Click "+ New Profile" (in edit mode) to add one</li>
              <li><strong>Auto-Save:</strong> All changes are automatically saved to your browser</li>
            </ul>
            
            <h4>Widget Types</h4>
            <ul>
              <li>📊 <strong>Price Trends:</strong> Historical price movements and analysis</li>
              <li>⚠️ <strong>Alert Summary:</strong> Current alerts and notifications</li>
              <li>🔍 <strong>Anomalies:</strong> Detected anomalies and outliers</li>
              <li>📡 <strong>Supplier Signals:</strong> Supplier performance indicators</li>
              <li>📈 <strong>Trend Forecast:</strong> Predicted trends and forecasts</li>
              <li>📌 <strong>Key Metrics:</strong> Important KPIs at a glance</li>
            </ul>
          </div>
        </details>
      </div>
    </div>
  );
};

export default DashboardPreview;
