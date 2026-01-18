/**
 * Data Export Utilities
 * 
 * Provides functions to export analytics data in multiple formats:
 * - CSV (comma-separated values)
 * - Excel (.xlsx)
 * - JSON (JavaScript Object Notation)
 */

import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

export interface ExportData {
  title: string;
  generatedAt: string;
  filters?: Record<string, any>;
  data: any[];
  columns: { key: string; label: string }[];
}

export interface ExportOptions {
  filename?: string;
  sheetName?: string;
  includeMetadata?: boolean;
}

/**
 * Export data as CSV
 */
export const exportAsCSV = (exportData: ExportData, options: ExportOptions = {}) => {
  const {
    filename = `${exportData.title}_${new Date().getTime()}`,
    includeMetadata = true,
  } = options;

  let csv = '';

  // Add metadata rows
  if (includeMetadata) {
    csv += `${exportData.title}\n`;
    csv += `Generated: ${exportData.generatedAt}\n`;
    if (exportData.filters) {
      csv += `Filters: ${JSON.stringify(exportData.filters).replace(/"/g, "'")}\n`;
    }
    csv += '\n';
  }

  // Add headers
  const headers = exportData.columns.map(col => `"${col.label}"`).join(',');
  csv += headers + '\n';

  // Add data rows
  exportData.data.forEach(row => {
    const values = exportData.columns
      .map(col => {
        let value = row[col.key];
        // Handle values that contain commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          value = `"${value.replace(/"/g, '""')}"`;
        }
        return value ?? '';
      })
      .join(',');
    csv += values + '\n';
  });

  // Create blob and download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  saveAs(blob, `${filename}.csv`);

  return {
    success: true,
    format: 'CSV',
    rowCount: exportData.data.length,
    filename: `${filename}.csv`,
  };
};

/**
 * Export data as Excel (.xlsx)
 */
export const exportAsExcel = (exportData: ExportData, options: ExportOptions = {}) => {
  const {
    filename = `${exportData.title}_${new Date().getTime()}`,
    sheetName = 'Data',
    includeMetadata = true,
  } = options;

  // Create workbook and worksheet
  const wb = XLSX.utils.book_new();

  // Prepare data
  let wsData: any[] = [];

  // Add metadata
  if (includeMetadata) {
    wsData.push([exportData.title]);
    wsData.push([`Generated: ${exportData.generatedAt}`]);
    if (exportData.filters) {
      wsData.push([`Filters: ${JSON.stringify(exportData.filters).replace(/"/g, "'")}`]);
    }
    wsData.push([]); // Empty row for spacing
  }

  // Add headers
  const headers = exportData.columns.map(col => col.label);
  wsData.push(headers);

  // Add data
  exportData.data.forEach(row => {
    const values = exportData.columns.map(col => row[col.key] ?? '');
    wsData.push(values);
  });

  // Create worksheet
  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // Style headers (if metadata included, headers start at row 4)
  const headerRowIndex = includeMetadata ? 4 : 1;
  const headerCellStyle = {
    font: { bold: true, color: { rgb: 'FFFFFF' } },
    fill: { fgColor: { rgb: '667EEA' } },
    alignment: { horizontal: 'center', vertical: 'center' },
  };

  headers.forEach((_, colIndex) => {
    const cellRef = XLSX.utils.encode_col(colIndex) + (headerRowIndex);
    if (ws[cellRef]) {
      ws[cellRef].s = headerCellStyle;
    }
  });

  // Set column widths
  const colWidths = exportData.columns.map(col => ({
    wch: Math.max(12, col.label.length + 2),
  }));
  ws['!cols'] = colWidths;

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(wb, ws, sheetName);

  // Write file
  XLSX.writeFile(wb, `${filename}.xlsx`);

  return {
    success: true,
    format: 'Excel',
    rowCount: exportData.data.length,
    filename: `${filename}.xlsx`,
  };
};

/**
 * Export data as JSON
 */
export const exportAsJSON = (exportData: ExportData, options: ExportOptions = {}) => {
  const {
    filename = `${exportData.title}_${new Date().getTime()}`,
    includeMetadata = true,
  } = options;

  let jsonData: any;

  if (includeMetadata) {
    jsonData = {
      metadata: {
        title: exportData.title,
        generatedAt: exportData.generatedAt,
        recordCount: exportData.data.length,
        filters: exportData.filters || null,
      },
      columns: exportData.columns,
      data: exportData.data,
    };
  } else {
    jsonData = exportData.data;
  }

  const json = JSON.stringify(jsonData, null, 2);
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
  saveAs(blob, `${filename}.json`);

  return {
    success: true,
    format: 'JSON',
    rowCount: exportData.data.length,
    filename: `${filename}.json`,
  };
};

/**
 * Generate sample chart data for export
 */
export const generateChartExportData = (
  chartType: 'price' | 'alert' | 'anomaly' | 'signal' | 'trend',
  filters?: Record<string, any>
): ExportData => {
  const now = new Date();
  const chartData: Record<string, any> = {};

  switch (chartType) {
    case 'price':
      chartData.title = 'Price Trends Report';
      chartData.columns = [
        { key: 'date', label: 'Date' },
        { key: 'price', label: 'Price ($)' },
        { key: 'trend', label: 'Trend' },
        { key: 'change', label: 'Change (%)' },
      ];
      chartData.data = Array.from({ length: 30 }, (_, i) => ({
        date: new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toLocaleDateString(),
        price: (200 + Math.random() * 50).toFixed(2),
        trend: Math.random() > 0.5 ? 'Up' : 'Down',
        change: (Math.random() * 10 - 5).toFixed(2),
      }));
      break;

    case 'alert':
      chartData.title = 'Alert Summary Report';
      chartData.columns = [
        { key: 'date', label: 'Date' },
        { key: 'severity', label: 'Severity' },
        { key: 'count', label: 'Count' },
        { key: 'status', label: 'Status' },
      ];
      chartData.data = [
        { date: now.toLocaleDateString(), severity: 'Critical', count: 2, status: 'Active' },
        { date: now.toLocaleDateString(), severity: 'High', count: 5, status: 'Active' },
        { date: now.toLocaleDateString(), severity: 'Medium', count: 12, status: 'Resolved' },
        { date: now.toLocaleDateString(), severity: 'Low', count: 23, status: 'Resolved' },
      ];
      break;

    case 'anomaly':
      chartData.title = 'Anomaly Detection Report';
      chartData.columns = [
        { key: 'date', label: 'Date' },
        { key: 'value', label: 'Value' },
        { key: 'zscore', label: 'Z-Score' },
        { key: 'status', label: 'Status' },
      ];
      chartData.data = Array.from({ length: 20 }, (_, i) => ({
        date: new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toLocaleDateString(),
        value: (100 + Math.random() * 200).toFixed(2),
        zscore: (Math.random() * 4 - 2).toFixed(2),
        status: Math.random() > 0.8 ? 'Anomaly' : 'Normal',
      }));
      break;

    case 'signal':
      chartData.title = 'Supplier Performance Signals';
      chartData.columns = [
        { key: 'supplier', label: 'Supplier' },
        { key: 'signal', label: 'Signal Value' },
        { key: 'rating', label: 'Rating' },
        { key: 'trend', label: 'Trend' },
      ];
      chartData.data = [
        { supplier: 'Supplier A', signal: '0.85', rating: 'Good', trend: 'Improving' },
        { supplier: 'Supplier B', signal: '0.72', rating: 'Fair', trend: 'Declining' },
        { supplier: 'Supplier C', signal: '0.95', rating: 'Excellent', trend: 'Stable' },
        { supplier: 'Supplier D', signal: '0.58', rating: 'Poor', trend: 'Critical' },
        { supplier: 'Supplier E', signal: '0.82', rating: 'Good', trend: 'Improving' },
      ];
      break;

    case 'trend':
      chartData.title = 'Trend Forecast Report';
      chartData.columns = [
        { key: 'date', label: 'Date' },
        { key: 'actual', label: 'Actual' },
        { key: 'forecast', label: 'Forecast' },
        { key: 'confidence', label: 'Confidence (%)' },
      ];
      chartData.data = Array.from({ length: 30 }, (_, i) => ({
        date: new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toLocaleDateString(),
        actual: (500 + Math.random() * 200).toFixed(2),
        forecast: (500 + Math.random() * 200).toFixed(2),
        confidence: (75 + Math.random() * 20).toFixed(0),
      }));
      break;
  }

  return {
    title: chartData.title,
    generatedAt: now.toISOString(),
    filters,
    data: chartData.data,
    columns: chartData.columns,
  };
};

/**
 * Generate combined export data from multiple sources
 */
export const generateCombinedExportData = (
  charts: Array<'price' | 'alert' | 'anomaly' | 'signal' | 'trend'>,
  filters?: Record<string, any>
): ExportData[] => {
  return charts.map(chart => generateChartExportData(chart, filters));
};
