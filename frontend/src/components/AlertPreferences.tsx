import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './AlertPreferences.css';

// Types
export interface AlertPreference {
  id: string;
  userId: string;
  severityThresholds: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  notificationMethods: {
    email: boolean;
    sms: boolean;
    inApp: boolean;
    webhook: boolean;
  };
  quietHours: {
    enabled: boolean;
    startTime: string; // HH:MM format
    endTime: string; // HH:MM format
  };
  alertFrequency: 'immediate' | 'hourly' | 'daily' | 'weekly';
  skipWeekends: boolean;
  createdAt: string;
  updatedAt: string;
}

interface AlertPreferencesProps {
  onSave?: (preferences: AlertPreference) => void;
}

const DEFAULT_PREFERENCES: AlertPreference = {
  id: '',
  userId: '',
  severityThresholds: {
    critical: 90,
    high: 75,
    medium: 50,
    low: 25,
  },
  notificationMethods: {
    email: true,
    sms: false,
    inApp: true,
    webhook: false,
  },
  quietHours: {
    enabled: false,
    startTime: '22:00',
    endTime: '08:00',
  },
  alertFrequency: 'immediate',
  skipWeekends: false,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

const AlertPreferences: React.FC<AlertPreferencesProps> = ({ onSave }) => {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState<AlertPreference>(DEFAULT_PREFERENCES);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>('severity');

  // Load preferences from localStorage on mount
  useEffect(() => {
    const savedPreferences = localStorage.getItem(`alertPreferences_${user?.id}`);
    if (savedPreferences) {
      try {
        const parsed = JSON.parse(savedPreferences);
        setPreferences(parsed);
      } catch (error) {
        console.error('Failed to load alert preferences:', error);
      }
    } else {
      setPreferences({
        ...DEFAULT_PREFERENCES,
        id: `prefs_${Date.now()}`,
        userId: user?.id || '',
      });
    }
  }, [user?.id]);

  const handleSeverityChange = (level: keyof AlertPreference['severityThresholds'], value: number) => {
    setPreferences(prev => ({
      ...prev,
      severityThresholds: {
        ...prev.severityThresholds,
        [level]: value,
      },
      updatedAt: new Date().toISOString(),
    }));
    setHasChanges(true);
  };

  const handleNotificationMethodChange = (method: keyof AlertPreference['notificationMethods']) => {
    setPreferences(prev => ({
      ...prev,
      notificationMethods: {
        ...prev.notificationMethods,
        [method]: !prev.notificationMethods[method],
      },
      updatedAt: new Date().toISOString(),
    }));
    setHasChanges(true);
  };

  const handleQuietHoursChange = (field: keyof AlertPreference['quietHours'], value: any) => {
    setPreferences(prev => ({
      ...prev,
      quietHours: {
        ...prev.quietHours,
        [field]: value,
      },
      updatedAt: new Date().toISOString(),
    }));
    setHasChanges(true);
  };

  const handleAlertFrequencyChange = (frequency: AlertPreference['alertFrequency']) => {
    setPreferences(prev => ({
      ...prev,
      alertFrequency: frequency,
      updatedAt: new Date().toISOString(),
    }));
    setHasChanges(true);
  };

  const handleSkipWeekendsChange = () => {
    setPreferences(prev => ({
      ...prev,
      skipWeekends: !prev.skipWeekends,
      updatedAt: new Date().toISOString(),
    }));
    setHasChanges(true);
  };

  const handleSavePreferences = async () => {
    setIsSaving(true);
    setSaveMessage(null);

    try {
      // Save to localStorage
      localStorage.setItem(`alertPreferences_${user?.id}`, JSON.stringify(preferences));
      
      // In a real app, you would save to the backend here
      // await apiClient.saveAlertPreferences(preferences);
      
      setHasChanges(false);
      setSaveMessage({ type: 'success', text: 'Alert preferences saved successfully!' });
      onSave?.(preferences);
      
      // Clear message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      setSaveMessage({ type: 'error', text: 'Failed to save preferences. Please try again.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetPreferences = () => {
    if (window.confirm('Are you sure you want to reset to default preferences?')) {
      setPreferences({
        ...DEFAULT_PREFERENCES,
        id: preferences.id,
        userId: preferences.userId,
      });
      setHasChanges(true);
    }
  };

  return (
    <div className="alert-preferences">
      {/* Header */}
      <div className="preferences-header">
        <h1>Alert Preferences</h1>
        <p className="subtitle">Customize how and when you receive alerts</p>
      </div>

      {/* Save Message */}
      {saveMessage && (
        <div className={`alert-message ${saveMessage.type}`}>
          <span>{saveMessage.type === 'success' ? '✓' : '✕'} {saveMessage.text}</span>
        </div>
      )}

      {/* Preferences Sections */}
      <div className="preferences-container">
        {/* Severity Thresholds Section */}
        <section className="preferences-section">
          <button
            className="section-header"
            onClick={() => setExpandedSection(expandedSection === 'severity' ? null : 'severity')}
          >
            <span className="section-icon">⚠️</span>
            <h2>Alert Severity Thresholds</h2>
            <span className="expand-icon">{expandedSection === 'severity' ? '▼' : '▶'}</span>
          </button>

          {expandedSection === 'severity' && (
            <div className="section-content">
              <p className="section-description">
                Set the threshold at which alerts are triggered for each severity level.
                Higher values = more sensitive alerts.
              </p>

              {/* Critical Threshold */}
              <div className="preference-item">
                <div className="item-header">
                  <label className="item-label">
                    <span className="severity-badge critical">CRITICAL</span>
                    Threshold: {preferences.severityThresholds.critical}%
                  </label>
                  <span className="item-description">Highest priority alerts</span>
                </div>
                <div className="slider-wrapper">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={preferences.severityThresholds.critical}
                    onChange={(e) => handleSeverityChange('critical', parseInt(e.target.value))}
                    className="slider critical"
                  />
                </div>
              </div>

              {/* High Threshold */}
              <div className="preference-item">
                <div className="item-header">
                  <label className="item-label">
                    <span className="severity-badge high">HIGH</span>
                    Threshold: {preferences.severityThresholds.high}%
                  </label>
                  <span className="item-description">Important alerts</span>
                </div>
                <div className="slider-wrapper">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={preferences.severityThresholds.high}
                    onChange={(e) => handleSeverityChange('high', parseInt(e.target.value))}
                    className="slider high"
                  />
                </div>
              </div>

              {/* Medium Threshold */}
              <div className="preference-item">
                <div className="item-header">
                  <label className="item-label">
                    <span className="severity-badge medium">MEDIUM</span>
                    Threshold: {preferences.severityThresholds.medium}%
                  </label>
                  <span className="item-description">Standard alerts</span>
                </div>
                <div className="slider-wrapper">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={preferences.severityThresholds.medium}
                    onChange={(e) => handleSeverityChange('medium', parseInt(e.target.value))}
                    className="slider medium"
                  />
                </div>
              </div>

              {/* Low Threshold */}
              <div className="preference-item">
                <div className="item-header">
                  <label className="item-label">
                    <span className="severity-badge low">LOW</span>
                    Threshold: {preferences.severityThresholds.low}%
                  </label>
                  <span className="item-description">Informational alerts</span>
                </div>
                <div className="slider-wrapper">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={preferences.severityThresholds.low}
                    onChange={(e) => handleSeverityChange('low', parseInt(e.target.value))}
                    className="slider low"
                  />
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Notification Methods Section */}
        <section className="preferences-section">
          <button
            className="section-header"
            onClick={() => setExpandedSection(expandedSection === 'methods' ? null : 'methods')}
          >
            <span className="section-icon">📢</span>
            <h2>Notification Methods</h2>
            <span className="expand-icon">{expandedSection === 'methods' ? '▼' : '▶'}</span>
          </button>

          {expandedSection === 'methods' && (
            <div className="section-content">
              <p className="section-description">
                Choose how you want to receive notifications.
              </p>

              <div className="checkbox-group">
                {/* Email */}
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={preferences.notificationMethods.email}
                    onChange={() => handleNotificationMethodChange('email')}
                    className="checkbox-input"
                  />
                  <span className="checkbox-label">
                    <span className="method-icon">📧</span>
                    <span className="method-name">Email</span>
                    <span className="method-description">Receive alerts via email</span>
                  </span>
                </label>

                {/* SMS */}
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={preferences.notificationMethods.sms}
                    onChange={() => handleNotificationMethodChange('sms')}
                    className="checkbox-input"
                  />
                  <span className="checkbox-label">
                    <span className="method-icon">📱</span>
                    <span className="method-name">SMS</span>
                    <span className="method-description">Receive alerts via text message</span>
                  </span>
                </label>

                {/* In-App */}
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={preferences.notificationMethods.inApp}
                    onChange={() => handleNotificationMethodChange('inApp')}
                    className="checkbox-input"
                  />
                  <span className="checkbox-label">
                    <span className="method-icon">🔔</span>
                    <span className="method-name">In-App Notifications</span>
                    <span className="method-description">Show alerts within the application</span>
                  </span>
                </label>

                {/* Webhook */}
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={preferences.notificationMethods.webhook}
                    onChange={() => handleNotificationMethodChange('webhook')}
                    className="checkbox-input"
                  />
                  <span className="checkbox-label">
                    <span className="method-icon">🔗</span>
                    <span className="method-name">Webhook</span>
                    <span className="method-description">Send alerts to external system</span>
                  </span>
                </label>
              </div>
            </div>
          )}
        </section>

        {/* Quiet Hours Section */}
        <section className="preferences-section">
          <button
            className="section-header"
            onClick={() => setExpandedSection(expandedSection === 'quiet' ? null : 'quiet')}
          >
            <span className="section-icon">🌙</span>
            <h2>Quiet Hours</h2>
            <span className="expand-icon">{expandedSection === 'quiet' ? '▼' : '▶'}</span>
          </button>

          {expandedSection === 'quiet' && (
            <div className="section-content">
              <p className="section-description">
                Set a time period when you don't want to receive alerts (e.g., during off-hours).
              </p>

              <div className="preference-item">
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={preferences.quietHours.enabled}
                    onChange={(e) => handleQuietHoursChange('enabled', e.target.checked)}
                    className="toggle-input"
                  />
                  <span className="toggle-track"></span>
                  <span className="toggle-label-text">Enable Quiet Hours</span>
                </label>
              </div>

              {preferences.quietHours.enabled && (
                <>
                  <div className="time-picker-group">
                    <div className="time-picker-item">
                      <label htmlFor="start-time">Start Time</label>
                      <input
                        id="start-time"
                        type="time"
                        value={preferences.quietHours.startTime}
                        onChange={(e) => handleQuietHoursChange('startTime', e.target.value)}
                        className="time-input"
                      />
                    </div>
                    <div className="time-picker-item">
                      <label htmlFor="end-time">End Time</label>
                      <input
                        id="end-time"
                        type="time"
                        value={preferences.quietHours.endTime}
                        onChange={(e) => handleQuietHoursChange('endTime', e.target.value)}
                        className="time-input"
                      />
                    </div>
                  </div>

                  <div className="preference-item">
                    <label className="toggle-label">
                      <input
                        type="checkbox"
                        checked={preferences.skipWeekends}
                        onChange={handleSkipWeekendsChange}
                        className="toggle-input"
                      />
                      <span className="toggle-track"></span>
                      <span className="toggle-label-text">Skip Weekends</span>
                    </label>
                    <span className="item-description">Don't send alerts on Saturday and Sunday</span>
                  </div>
                </>
              )}
            </div>
          )}
        </section>

        {/* Alert Frequency Section */}
        <section className="preferences-section">
          <button
            className="section-header"
            onClick={() => setExpandedSection(expandedSection === 'frequency' ? null : 'frequency')}
          >
            <span className="section-icon">⏱️</span>
            <h2>Alert Frequency</h2>
            <span className="expand-icon">{expandedSection === 'frequency' ? '▼' : '▶'}</span>
          </button>

          {expandedSection === 'frequency' && (
            <div className="section-content">
              <p className="section-description">
                How often do you want to receive alerts?
              </p>

              <div className="radio-group">
                <label className="radio-item">
                  <input
                    type="radio"
                    name="frequency"
                    value="immediate"
                    checked={preferences.alertFrequency === 'immediate'}
                    onChange={(e) => handleAlertFrequencyChange(e.target.value as any)}
                    className="radio-input"
                  />
                  <span className="radio-label">
                    <span className="radio-title">🚀 Immediate</span>
                    <span className="radio-description">Receive alerts as soon as they occur</span>
                  </span>
                </label>

                <label className="radio-item">
                  <input
                    type="radio"
                    name="frequency"
                    value="hourly"
                    checked={preferences.alertFrequency === 'hourly'}
                    onChange={(e) => handleAlertFrequencyChange(e.target.value as any)}
                    className="radio-input"
                  />
                  <span className="radio-label">
                    <span className="radio-title">⏰ Hourly</span>
                    <span className="radio-description">Receive summary emails every hour</span>
                  </span>
                </label>

                <label className="radio-item">
                  <input
                    type="radio"
                    name="frequency"
                    value="daily"
                    checked={preferences.alertFrequency === 'daily'}
                    onChange={(e) => handleAlertFrequencyChange(e.target.value as any)}
                    className="radio-input"
                  />
                  <span className="radio-label">
                    <span className="radio-title">📅 Daily</span>
                    <span className="radio-description">Receive summary emails once per day</span>
                  </span>
                </label>

                <label className="radio-item">
                  <input
                    type="radio"
                    name="frequency"
                    value="weekly"
                    checked={preferences.alertFrequency === 'weekly'}
                    onChange={(e) => handleAlertFrequencyChange(e.target.value as any)}
                    className="radio-input"
                  />
                  <span className="radio-label">
                    <span className="radio-title">📊 Weekly</span>
                    <span className="radio-description">Receive summary emails once per week</span>
                  </span>
                </label>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Action Buttons */}
      <div className="preferences-actions">
        <button
          className="btn btn-primary"
          onClick={handleSavePreferences}
          disabled={!hasChanges || isSaving}
        >
          {isSaving ? 'Saving...' : '💾 Save Preferences'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleResetPreferences}
        >
          ↻ Reset to Default
        </button>
      </div>

      {/* Last Updated */}
      <div className="preferences-footer">
        <p>Last updated: {new Date(preferences.updatedAt).toLocaleString()}</p>
      </div>
    </div>
  );
};

export default AlertPreferences;
