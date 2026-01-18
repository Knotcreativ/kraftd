import React, { useState } from 'react';
import Breadcrumb from '../components/Breadcrumb';
import AlertPreferences from '../components/AlertPreferences';
import './PreferencesPage.css';

type PreferenceTab = 'alerts' | 'notifications' | 'display' | 'data';

interface PreferenceSection {
  id: PreferenceTab;
  label: string;
  icon: string;
  description: string;
}

/**
 * Preferences Landing Page
 * Central hub for all user preferences and settings
 * Includes alerts, notifications, display, and data management
 */
const PreferencesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PreferenceTab>('alerts');

  const sections: PreferenceSection[] = [
    {
      id: 'alerts',
      label: 'Alert Settings',
      icon: '🔔',
      description: 'Configure alert thresholds and severity levels',
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: '📬',
      description: 'Manage notification methods and preferences',
    },
    {
      id: 'display',
      label: 'Display',
      icon: '🎨',
      description: 'Customize appearance and theme',
    },
    {
      id: 'data',
      label: 'Data & Privacy',
      icon: '🔒',
      description: 'Manage data storage and privacy settings',
    },
  ];

  return (
    <div className="preferences-page">
      <Breadcrumb />

      <div className="preferences-container">
        {/* Header */}
        <div className="preferences-header">
          <div className="preferences-header-content">
            <h1 className="preferences-title">⚙️ Preferences</h1>
            <p className="preferences-subtitle">
              Manage your account settings, alerts, and notification preferences
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="preferences-tabs">
          <nav className="preferences-nav" aria-label="Preference sections">
            {sections.map((section) => (
              <button
                key={section.id}
                className={`preference-tab ${activeTab === section.id ? 'active' : ''}`}
                onClick={() => setActiveTab(section.id)}
                aria-selected={activeTab === section.id}
                aria-label={section.label}
              >
                <span className="tab-icon">{section.icon}</span>
                <span className="tab-label">{section.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content Area */}
        <div className="preferences-content">
          {/* Alert Settings Tab */}
          {activeTab === 'alerts' && (
            <div className="preference-section">
              <div className="section-header">
                <h2>{sections[0].label}</h2>
                <p className="section-description">{sections[0].description}</p>
              </div>
              <AlertPreferences />
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="preference-section">
              <div className="section-header">
                <h2>{sections[1].label}</h2>
                <p className="section-description">{sections[1].description}</p>
              </div>
              <div className="notification-settings">
                <div className="settings-card">
                  <h3>Email Notifications</h3>
                  <label className="settings-toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-label">Receive email alerts</span>
                  </label>
                  <p className="setting-hint">Daily digest of important events</p>
                </div>

                <div className="settings-card">
                  <h3>SMS Notifications</h3>
                  <label className="settings-toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-label">Receive SMS alerts</span>
                  </label>
                  <p className="setting-hint">Instant alerts for critical events</p>
                </div>

                <div className="settings-card">
                  <h3>In-App Notifications</h3>
                  <label className="settings-toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-label">Show in-app notifications</span>
                  </label>
                  <p className="setting-hint">Real-time notifications while using the app</p>
                </div>
              </div>
            </div>
          )}

          {/* Display Tab */}
          {activeTab === 'display' && (
            <div className="preference-section">
              <div className="section-header">
                <h2>{sections[2].label}</h2>
                <p className="section-description">{sections[2].description}</p>
              </div>
              <div className="display-settings">
                <div className="settings-card">
                  <h3>Theme</h3>
                  <div className="theme-selector">
                    <label className="theme-option">
                      <input type="radio" name="theme" value="light" defaultChecked />
                      <span className="theme-label">☀️ Light</span>
                    </label>
                    <label className="theme-option">
                      <input type="radio" name="theme" value="dark" />
                      <span className="theme-label">🌙 Dark</span>
                    </label>
                    <label className="theme-option">
                      <input type="radio" name="theme" value="auto" />
                      <span className="theme-label">🔄 Auto</span>
                    </label>
                  </div>
                </div>

                <div className="settings-card">
                  <h3>Sidebar</h3>
                  <label className="settings-toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-label">Collapse sidebar by default</span>
                  </label>
                  <p className="setting-hint">Show/hide navigation sidebar on startup</p>
                </div>

                <div className="settings-card">
                  <h3>Animations</h3>
                  <label className="settings-toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-label">Enable animations</span>
                  </label>
                  <p className="setting-hint">Smooth transitions and visual effects</p>
                </div>
              </div>
            </div>
          )}

          {/* Data & Privacy Tab */}
          {activeTab === 'data' && (
            <div className="preference-section">
              <div className="section-header">
                <h2>{sections[3].label}</h2>
                <p className="section-description">{sections[3].description}</p>
              </div>
              <div className="data-settings">
                <div className="settings-card warning">
                  <h3>Data Retention</h3>
                  <p>Historical data is retained for 12 months for analysis and reporting.</p>
                  <button className="settings-button secondary">Learn More</button>
                </div>

                <div className="settings-card">
                  <h3>Data Export</h3>
                  <p>Download a copy of all your data in a standard format.</p>
                  <button className="settings-button secondary">Export My Data</button>
                </div>

                <div className="settings-card danger">
                  <h3>Delete Account</h3>
                  <p>Permanently delete your account and all associated data.</p>
                  <button className="settings-button danger">Delete Account</button>
                </div>

                <div className="settings-card">
                  <h3>Privacy</h3>
                  <label className="settings-toggle">
                    <input type="checkbox" defaultChecked />
                    <span className="toggle-label">Allow analytics tracking</span>
                  </label>
                  <p className="setting-hint">Help us improve by sharing usage data</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="preferences-footer">
          <p className="footer-text">
            Changes are saved automatically. Last updated: {new Date().toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PreferencesPage;
