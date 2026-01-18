import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './FilterPanel.css';

interface FilterState {
  startDate: Date;
  endDate: Date;
  itemId?: string;
  supplierId?: string;
  severity?: string;
  riskLevel?: string;
  displayMode: 'compact' | 'expanded';
}

interface FilterPanelProps {
  onFilterChange?: (filters: FilterState) => void;
  items?: string[];
  suppliers?: string[];
}

const SEVERITY_LEVELS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const RISK_LEVELS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL'];
const PRESETS = [
  { label: 'Last 7 Days', days: 7 },
  { label: 'Last 30 Days', days: 30 },
  { label: 'Last 90 Days', days: 90 },
  { label: 'Last Year', days: 365 },
];

const FilterPanel: React.FC<FilterPanelProps> = ({ 
  onFilterChange, 
  items = [],
  suppliers = []
}) => {
  // Initialize dates: default to last 30 days
  const today = new Date();
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const [filters, setFilters] = useState<FilterState>({
    startDate: thirtyDaysAgo,
    endDate: today,
    displayMode: 'compact',
  });

  const [savedPresets, setSavedPresets] = useState<FilterState[]>(() => {
    const saved = localStorage.getItem('filter_presets');
    return saved ? JSON.parse(saved) : [];
  });

  const [presetName, setPresetName] = useState('');
  const [showPresetInput, setShowPresetInput] = useState(false);

  // Notify parent component when filters change
  useEffect(() => {
    onFilterChange?.(filters);
  }, [filters]);

  const handleDateChange = (field: 'startDate' | 'endDate', date: Date | null) => {
    if (date) {
      setFilters(prev => ({
        ...prev,
        [field]: date,
      }));
    }
  };

  const handleFilterChange = (field: keyof Omit<FilterState, 'displayMode' | 'startDate' | 'endDate'>, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined,
    }));
  };

  const handlePresetClick = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    
    setFilters(prev => ({
      ...prev,
      startDate: start,
      endDate: end,
    }));
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      const newPreset: FilterState = {
        ...filters,
        displayMode: 'compact',
      };
      
      const updated = [...savedPresets, { ...newPreset, displayMode: 'compact' as const }];
      setSavedPresets(updated);
      localStorage.setItem('filter_presets', JSON.stringify(updated));
      setPresetName('');
      setShowPresetInput(false);
    }
  };

  const handleLoadPreset = (preset: FilterState) => {
    setFilters({
      startDate: new Date(preset.startDate),
      endDate: new Date(preset.endDate),
      itemId: preset.itemId,
      supplierId: preset.supplierId,
      severity: preset.severity,
      riskLevel: preset.riskLevel,
      displayMode: filters.displayMode,
    });
  };

  const handleDeletePreset = (index: number) => {
    const updated = savedPresets.filter((_, i) => i !== index);
    setSavedPresets(updated);
    localStorage.setItem('filter_presets', JSON.stringify(updated));
  };

  const handleClearFilters = () => {
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    setFilters({
      startDate: thirtyDaysAgo,
      endDate: today,
      displayMode: 'compact',
    });
  };

  const handleReset = () => {
    setFilters(prev => ({
      ...prev,
      itemId: undefined,
      supplierId: undefined,
      severity: undefined,
      riskLevel: undefined,
    }));
  };

  const hasActiveFilters = Boolean(
    filters.itemId || 
    filters.supplierId || 
    filters.severity || 
    filters.riskLevel
  );

  return (
    <div className={`filter-panel filter-panel--${filters.displayMode}`}>
      {/* Header */}
      <div className="filter-panel__header">
        <h3 className="filter-panel__title">
          <span className="filter-panel__icon">⚙️</span>
          Advanced Filters
        </h3>
        <button
          className="filter-panel__toggle"
          onClick={() => setFilters(prev => ({
            ...prev,
            displayMode: prev.displayMode === 'compact' ? 'expanded' : 'compact'
          }))}
          aria-label={filters.displayMode === 'compact' ? 'Expand filters' : 'Collapse filters'}
        >
          {filters.displayMode === 'compact' ? '▼' : '▲'}
        </button>
      </div>

      {/* Date Range Section */}
      <div className="filter-panel__section filter-panel__section--dates">
        <label className="filter-panel__label">Date Range</label>
        
        <div className="filter-panel__date-inputs">
          <div className="filter-panel__date-field">
            <label className="filter-panel__sublabel">From</label>
            <DatePicker
              selected={filters.startDate}
              onChange={(date: Date | null) => handleDateChange('startDate', date)}
              maxDate={filters.endDate}
              dateFormat="MMM dd, yyyy"
              className="filter-panel__date-picker"
            />
          </div>
          
          <div className="filter-panel__separator">→</div>
          
          <div className="filter-panel__date-field">
            <label className="filter-panel__sublabel">To</label>
            <DatePicker
              selected={filters.endDate}
              onChange={(date: Date | null) => handleDateChange('endDate', date)}
              minDate={filters.startDate}
              maxDate={new Date()}
              dateFormat="MMM dd, yyyy"
              className="filter-panel__date-picker"
            />
          </div>
        </div>

        {/* Date Presets */}
        <div className="filter-panel__presets">
          {PRESETS.map(preset => (
            <button
              key={preset.days}
              className="filter-panel__preset-btn"
              onClick={() => handlePresetClick(preset.days)}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Expandable Sections */}
      {filters.displayMode === 'expanded' && (
        <>
          {/* Item Filter */}
          {items.length > 0 && (
            <div className="filter-panel__section">
              <label className="filter-panel__label">
                <input
                  type="checkbox"
                  className="filter-panel__checkbox"
                  checked={Boolean(filters.itemId)}
                  onChange={(e) => handleFilterChange('itemId', e.target.checked ? items[0] : '')}
                />
                Item / Commodity
              </label>
              {filters.itemId && (
                <select
                  className="filter-panel__select"
                  value={filters.itemId}
                  onChange={(e) => handleFilterChange('itemId', e.target.value)}
                >
                  <option value="">-- Select Item --</option>
                  {items.map(item => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Supplier Filter */}
          {suppliers.length > 0 && (
            <div className="filter-panel__section">
              <label className="filter-panel__label">
                <input
                  type="checkbox"
                  className="filter-panel__checkbox"
                  checked={Boolean(filters.supplierId)}
                  onChange={(e) => handleFilterChange('supplierId', e.target.checked ? suppliers[0] : '')}
                />
                Supplier
              </label>
              {filters.supplierId && (
                <select
                  className="filter-panel__select"
                  value={filters.supplierId}
                  onChange={(e) => handleFilterChange('supplierId', e.target.value)}
                >
                  <option value="">-- Select Supplier --</option>
                  {suppliers.map(supplier => (
                    <option key={supplier} value={supplier}>{supplier}</option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Severity Filter */}
          <div className="filter-panel__section">
            <label className="filter-panel__label">Alert Severity</label>
            <div className="filter-panel__checkboxes">
              {SEVERITY_LEVELS.map(level => (
                <label key={level} className="filter-panel__checkbox-label">
                  <input
                    type="checkbox"
                    className="filter-panel__checkbox"
                    checked={filters.severity === level}
                    onChange={(e) => handleFilterChange('severity', e.target.checked ? level : '')}
                  />
                  <span className={`filter-panel__severity-badge severity-${level.toLowerCase()}`}>
                    {level}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Risk Level Filter */}
          <div className="filter-panel__section">
            <label className="filter-panel__label">Risk Level</label>
            <div className="filter-panel__checkboxes">
              {RISK_LEVELS.map(level => (
                <label key={level} className="filter-panel__checkbox-label">
                  <input
                    type="checkbox"
                    className="filter-panel__checkbox"
                    checked={filters.riskLevel === level}
                    onChange={(e) => handleFilterChange('riskLevel', e.target.checked ? level : '')}
                  />
                  <span className={`filter-panel__risk-badge risk-${level.toLowerCase()}`}>
                    {level}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Active Filters Display */}
          {hasActiveFilters && (
            <div className="filter-panel__active-filters">
              <p className="filter-panel__active-label">Active Filters:</p>
              {filters.itemId && (
                <span className="filter-panel__filter-tag">
                  Item: {filters.itemId}
                  <button onClick={() => handleFilterChange('itemId', '')}>×</button>
                </span>
              )}
              {filters.supplierId && (
                <span className="filter-panel__filter-tag">
                  Supplier: {filters.supplierId}
                  <button onClick={() => handleFilterChange('supplierId', '')}>×</button>
                </span>
              )}
              {filters.severity && (
                <span className="filter-panel__filter-tag">
                  Severity: {filters.severity}
                  <button onClick={() => handleFilterChange('severity', '')}>×</button>
                </span>
              )}
              {filters.riskLevel && (
                <span className="filter-panel__filter-tag">
                  Risk: {filters.riskLevel}
                  <button onClick={() => handleFilterChange('riskLevel', '')}>×</button>
                </span>
              )}
            </div>
          )}

          {/* Saved Presets */}
          <div className="filter-panel__section filter-panel__section--presets">
            <label className="filter-panel__label">Saved Presets</label>
            
            {savedPresets.length > 0 && (
              <div className="filter-panel__saved-presets">
                {savedPresets.map((preset, idx) => (
                  <div key={idx} className="filter-panel__saved-preset">
                    <button
                      className="filter-panel__preset-load-btn"
                      onClick={() => handleLoadPreset(preset)}
                    >
                      Load
                    </button>
                    <span className="filter-panel__preset-info">
                      {new Date(preset.startDate).toLocaleDateString()} - {new Date(preset.endDate).toLocaleDateString()}
                    </span>
                    <button
                      className="filter-panel__preset-delete-btn"
                      onClick={() => handleDeletePreset(idx)}
                      aria-label="Delete preset"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            )}

            {!showPresetInput && (
              <button
                className="filter-panel__save-preset-btn"
                onClick={() => setShowPresetInput(true)}
              >
                + Save Current Filters
              </button>
            )}

            {showPresetInput && (
              <div className="filter-panel__preset-input-group">
                <input
                  type="text"
                  className="filter-panel__preset-input"
                  placeholder="Preset name..."
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSavePreset()}
                />
                <button
                  className="filter-panel__preset-confirm-btn"
                  onClick={handleSavePreset}
                >
                  Save
                </button>
                <button
                  className="filter-panel__preset-cancel-btn"
                  onClick={() => {
                    setShowPresetInput(false);
                    setPresetName('');
                  }}
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {/* Action Buttons */}
      <div className="filter-panel__actions">
        {hasActiveFilters && (
          <button
            className="filter-panel__action-btn filter-panel__action-btn--reset"
            onClick={handleReset}
          >
            Reset Filters
          </button>
        )}
        <button
          className="filter-panel__action-btn filter-panel__action-btn--clear"
          onClick={handleClearFilters}
        >
          Clear All
        </button>
      </div>

      {/* Status Bar */}
      <div className="filter-panel__status">
        <span className="filter-panel__status-text">
          📊 Showing: {filters.startDate.toLocaleDateString()} to {filters.endDate.toLocaleDateString()}
          {hasActiveFilters && ' | Filters active'}
        </span>
      </div>
    </div>
  );
};

export default FilterPanel;
