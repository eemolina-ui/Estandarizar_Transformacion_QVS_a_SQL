import React from 'react';

/**
 * Utility component to download table data as CSV
 */
const CSVDownloadHelper = ({ data, columns, filename = 'datos_exportados.csv' }) => {
  // Function to convert data to CSV format
  const convertToCSV = (dataArray, columnsArray) => {
    // Create header row
    let csvContent = columnsArray.join(',') + '\n';
    
    // Create data rows
    dataArray.forEach(item => {
      const row = columnsArray.map(column => {
        // Handle values that might contain commas by wrapping in quotes
        const value = item[column] !== undefined ? item[column] : '';
        const escaped = String(value).replace(/"/g, '""');
        return `"${escaped}"`;
      });
      csvContent += row.join(',') + '\n';
    });
    
    return csvContent;
  };
  
  // Generate CSV data
  const csvData = convertToCSV(data, columns);
  
  // Create download link
  const downloadCSV = () => {
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  return (
    <button 
      onClick={downloadCSV}
      className="px-1 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
    >
      <svg 
        className="w-4 h-4 mr-2" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth="2" 
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
        />
      </svg>
      Descargar CSV
    </button>
  );
};

export default CSVDownloadHelper;