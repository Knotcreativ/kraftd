import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';
import './DashboardBuilder.css';

// Types
export interface DashboardWidget {
  id: string;
  type: 'price' | 'alert' | 'anomaly' | 'signal' | 'trend' | 'kpi';
  title: string;
  size: 'small' | 'medium' | 'large';
  position: number;
}

export interface DashboardProfile {
  id: string;
  name: string;
  description: string;
  isDefault: boolean;
  widgets: DashboardWidget[];
  createdAt: string;
  updatedAt: string;
}

interface DashboardBuilderProps {
  onProfileChange?: (profile: DashboardProfile) => void;
  onSaveProfile?: (profile: DashboardProfile) => void;
}

// Available widget types
const AVAILABLE_WIDGETS = [
  { id: 'price', type: 'price' as const, title: 'Price Trends', icon: '📊' },
  { id: 'alert', type: 'alert' as const, title: 'Alert Summary', icon: '⚠️' },
  { id: 'anomaly', type: 'anomaly' as const, title: 'Anomalies', icon: '🔍' },
  { id: 'signal', type: 'signal' as const, title: 'Supplier Signals', icon: '📡' },
  { id: 'trend', type: 'trend' as const, title: 'Trend Forecast', icon: '📈' },
  { id: 'kpi', type: 'kpi' as const, title: 'Key Metrics', icon: '📌' },
];

const DashboardBuilder: React.FC<DashboardBuilderProps> = ({ onProfileChange, onSaveProfile }) => {
  const [profiles, setProfiles] = useState<DashboardProfile[]>([]);
  const [activeProfile, setActiveProfile] = useState<DashboardProfile | null>(null);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [newProfileName, setNewProfileName] = useState('');
  const [editMode, setEditMode] = useState(false);

  // Load profiles from localStorage on mount
  useEffect(() => {
    const savedProfiles = localStorage.getItem('dashboardProfiles');
    if (savedProfiles) {
      try {
        const parsed = JSON.parse(savedProfiles);
        setProfiles(parsed);
        const defaultProfile = parsed.find((p: DashboardProfile) => p.isDefault);
        if (defaultProfile) {
          setActiveProfile(defaultProfile);
          onProfileChange?.(defaultProfile);
        }
      } catch (error) {
        console.error('Failed to load dashboard profiles:', error);
      }
    } else {
      // Create default profile
      const defaultProfile = createDefaultProfile();
      setProfiles([defaultProfile]);
      setActiveProfile(defaultProfile);
      localStorage.setItem('dashboardProfiles', JSON.stringify([defaultProfile]));
    }
  }, [onProfileChange]);

  const createDefaultProfile = (): DashboardProfile => {
    return {
      id: 'default-' + Date.now(),
      name: 'Default Dashboard',
      description: 'Your primary dashboard',
      isDefault: true,
      widgets: [
        { id: '1', type: 'kpi', title: 'Key Metrics', size: 'medium', position: 0 },
        { id: '2', type: 'price', title: 'Price Trends', size: 'large', position: 1 },
        { id: '3', type: 'alert', title: 'Alert Summary', size: 'medium', position: 2 },
        { id: '4', type: 'anomaly', title: 'Anomalies', size: 'medium', position: 3 },
        { id: '5', type: 'signal', title: 'Supplier Signals', size: 'large', position: 4 },
        { id: '6', type: 'trend', title: 'Trend Forecast', size: 'medium', position: 5 },
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  };

  const handleDragEnd = (result: DropResult) => {
    if (!activeProfile) return;

    const { source, destination, draggableId } = result;

    // If dropped outside valid area, ignore
    if (!destination) return;

    // If dropped in same position, ignore
    if (source.index === destination.index) return;

    const updatedProfile = { ...activeProfile };
    const [movedWidget] = updatedProfile.widgets.splice(source.index, 1);
    updatedProfile.widgets.splice(destination.index, 0, movedWidget);

    // Update positions
    updatedProfile.widgets = updatedProfile.widgets.map((w, idx) => ({ ...w, position: idx }));
    updatedProfile.updatedAt = new Date().toISOString();

    setActiveProfile(updatedProfile);
    updateProfile(updatedProfile);
  };

  const updateProfile = (profile: DashboardProfile) => {
    const updated = profiles.map(p => (p.id === profile.id ? profile : p));
    setProfiles(updated);
    localStorage.setItem('dashboardProfiles', JSON.stringify(updated));
    onProfileChange?.(profile);
  };

  const handleAddWidget = (widgetType: typeof AVAILABLE_WIDGETS[0]) => {
    if (!activeProfile || !editMode) return;

    const newWidget: DashboardWidget = {
      id: 'widget-' + Date.now(),
      type: widgetType.type,
      title: widgetType.title,
      size: 'medium',
      position: activeProfile.widgets.length,
    };

    const updated = {
      ...activeProfile,
      widgets: [...activeProfile.widgets, newWidget],
      updatedAt: new Date().toISOString(),
    };

    setActiveProfile(updated);
    updateProfile(updated);
  };

  const handleRemoveWidget = (widgetId: string) => {
    if (!activeProfile) return;

    const updated = {
      ...activeProfile,
      widgets: activeProfile.widgets
        .filter(w => w.id !== widgetId)
        .map((w, idx) => ({ ...w, position: idx })),
      updatedAt: new Date().toISOString(),
    };

    setActiveProfile(updated);
    updateProfile(updated);
  };

  const handleResizeWidget = (widgetId: string, size: 'small' | 'medium' | 'large') => {
    if (!activeProfile) return;

    const updated = {
      ...activeProfile,
      widgets: activeProfile.widgets.map(w =>
        w.id === widgetId ? { ...w, size } : w
      ),
      updatedAt: new Date().toISOString(),
    };

    setActiveProfile(updated);
    updateProfile(updated);
  };

  const handleCreateProfile = () => {
    if (!newProfileName.trim()) return;

    const newProfile: DashboardProfile = {
      id: 'profile-' + Date.now(),
      name: newProfileName,
      description: `Dashboard created on ${new Date().toLocaleDateString()}`,
      isDefault: false,
      widgets: activeProfile?.widgets ? [...activeProfile.widgets] : [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const updated = [...profiles, newProfile];
    setProfiles(updated);
    setActiveProfile(newProfile);
    setNewProfileName('');
    setShowProfileForm(false);
    localStorage.setItem('dashboardProfiles', JSON.stringify(updated));
  };

  const handleDeleteProfile = (profileId: string) => {
    const updated = profiles.filter(p => p.id !== profileId);
    const nextActive = updated[0];
    setProfiles(updated);
    setActiveProfile(nextActive || null);
    localStorage.setItem('dashboardProfiles', JSON.stringify(updated));
  };

  const handleSwitchProfile = (profile: DashboardProfile) => {
    setActiveProfile(profile);
    setEditMode(false);
    onProfileChange?.(profile);
  };

  if (!activeProfile) {
    return (
      <div className="dashboard-builder">
        <div className="no-profile-message">
          <p>No dashboard profiles found. Creating default...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-builder">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>{activeProfile.name}</h1>
          <p className="profile-description">{activeProfile.description}</p>
        </div>
        <div className="header-right">
          <button
            className={`edit-mode-btn ${editMode ? 'active' : ''}`}
            onClick={() => setEditMode(!editMode)}
          >
            {editMode ? '✓ Done Editing' : '✏️ Edit Layout'}
          </button>
          <button className="save-btn" onClick={() => onSaveProfile?.(activeProfile)}>
            💾 Save
          </button>
        </div>
      </div>

      {/* Profile Tabs */}
      <div className="profile-tabs">
        <div className="tabs-container">
          {profiles.map(profile => (
            <div
              key={profile.id}
              className={`tab ${profile.id === activeProfile.id ? 'active' : ''}`}
              onClick={() => handleSwitchProfile(profile)}
            >
              <span className="tab-name">{profile.name}</span>
              {profile.isDefault && <span className="default-badge">DEFAULT</span>}
              {editMode && (
                <button
                  className="delete-tab"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (profiles.length > 1) {
                      handleDeleteProfile(profile.id);
                    }
                  }}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          {editMode && (
            <button className="new-profile-btn" onClick={() => setShowProfileForm(true)}>
              + New Profile
            </button>
          )}
        </div>
      </div>

      {/* New Profile Form */}
      {showProfileForm && (
        <div className="new-profile-form">
          <input
            type="text"
            placeholder="Dashboard name (e.g., 'Trading View', 'Risk Alert View')"
            value={newProfileName}
            onChange={(e) => setNewProfileName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleCreateProfile();
            }}
            autoFocus
          />
          <button onClick={handleCreateProfile}>Create</button>
          <button onClick={() => setShowProfileForm(false)}>Cancel</button>
        </div>
      )}

      {/* Edit Mode - Widget Library */}
      {editMode && (
        <div className="widget-library">
          <h3>Available Widgets</h3>
          <div className="widget-grid">
            {AVAILABLE_WIDGETS.map(widget => (
              <button
                key={widget.id}
                className="widget-add-btn"
                onClick={() => handleAddWidget(widget)}
                title={`Add ${widget.title} widget`}
              >
                <span className="icon">{widget.icon}</span>
                <span className="label">{widget.title}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Dashboard Canvas */}
      <div className={`dashboard-canvas ${editMode ? 'edit-mode' : ''}`}>
        {editMode ? (
          // Edit Mode - Draggable
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="dashboard-widgets" type="WIDGET">
              {(provided: any, snapshot: any) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`widgets-container ${snapshot.isDraggingOver ? 'drag-over' : ''}`}
                >
                  {activeProfile.widgets.length === 0 ? (
                    <div className="empty-dashboard">
                      <p>No widgets on this dashboard.</p>
                      <p>Add widgets from the library above.</p>
                    </div>
                  ) : (
                    activeProfile.widgets.map((widget, index) => (
                      <Draggable key={widget.id} draggableId={widget.id} index={index}>
                        {(provided: any, snapshot: any) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className={`widget-card ${widget.size} ${snapshot.isDragging ? 'dragging' : ''}`}
                          >
                            <div className="widget-header">
                              <h3>{widget.title}</h3>
                              <div className="widget-controls">
                                <select
                                  value={widget.size}
                                  onChange={(e) =>
                                    handleResizeWidget(widget.id, e.target.value as any)
                                  }
                                  className="size-selector"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <option value="small">Small</option>
                                  <option value="medium">Medium</option>
                                  <option value="large">Large</option>
                                </select>
                                <button
                                  className="remove-btn"
                                  onClick={() => handleRemoveWidget(widget.id)}
                                  title="Remove widget"
                                >
                                  ✕
                                </button>
                              </div>
                            </div>
                            <div className="widget-content">
                              <p className="widget-type">{widget.type.toUpperCase()}</p>
                              <p className="drag-hint">☰ Drag to reorder</p>
                            </div>
                          </div>
                        )}
                      </Draggable>
                    ))
                  )}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        ) : (
          // View Mode - Static Display
          <div className="widgets-container view-mode">
            {activeProfile.widgets.length === 0 ? (
              <div className="empty-dashboard">
                <p>No widgets on this dashboard.</p>
                <p>Click "Edit Layout" to add widgets.</p>
              </div>
            ) : (
              activeProfile.widgets.map(widget => (
                <div key={widget.id} className={`widget-card ${widget.size}`}>
                  <div className="widget-header">
                    <h3>{widget.title}</h3>
                  </div>
                  <div className="widget-content">
                    <p className="placeholder">Widget content loads here</p>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Info Footer */}
      <div className="dashboard-footer">
        <p>
          {editMode ? (
            <>
              <strong>Edit Mode:</strong> Drag widgets to reorder, click × to remove, or
              select size from dropdown
            </>
          ) : (
            <>
              <strong>View Mode:</strong> Click "Edit Layout" to customize your dashboard
            </>
          )}
        </p>
        <p className="last-updated">
          Last updated: {new Date(activeProfile.updatedAt).toLocaleString()}
        </p>
      </div>
    </div>
  );
};

export default DashboardBuilder;
