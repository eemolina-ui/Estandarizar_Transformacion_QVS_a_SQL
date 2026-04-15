import React, { useState } from 'react';
import CSVDownloadHelper from '../composables/CSVDownloadHelper';
import transformColumnarToTabular from '../composables/DataTransformer';

const DataImageViewerComponent = ({ images, titles, tableData, tableColumns, isColumnarFormat = false }) => {
  // State to track the currently displayed image
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  // State to track the active view tab (images or data)
  const [activeTab, setActiveTab] = useState('images');
  // State for table search/filter
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredData, setFilteredData] = useState([]);

  // Handler for navigating to the next image
  const handleNextImage = () => {
    setCurrentImageIndex((prevIndex) => (prevIndex + 1) % images.length);
  };

  // Handler for navigating to the previous image
  const handlePrevImage = () => {
    setCurrentImageIndex((prevIndex) => (prevIndex - 1 + images.length) % images.length);
  };

  // Handler for selecting a specific image
  const handleSelectImage = (index) => {
    setCurrentImageIndex(index);
  };

  // Handler for changing tabs
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'data') {
      // When switching to data tab, apply any existing filters
      handleSearch(searchTerm);
    }
  };
  
  // Handler for search/filter functionality
  const handleSearch = (term) => {
    setSearchTerm(term);
    if (!term.trim()) {
      setFilteredData(tableData);
      return;
    }
    
    const lowerTerm = term.toLowerCase();
    const filtered = tableData.filter(row => {
      return tableColumns.some(column => {
        const value = row[column];
        return value !== undefined && 
               String(value).toLowerCase().includes(lowerTerm);
      });
    });
    
    setFilteredData(filtered);
  };

  // Transformar datos si es necesario y mantener los datos transformados
  const [transformedData, setTransformedData] = useState([]);
  
  // Initialize filteredData and transform data when component mounts or tableData changes
  React.useEffect(() => {
    // Si los datos están en formato columnar, transformarlos
    const processedData = isColumnarFormat
      ? transformColumnarToTabular(tableData)
      : tableData;
    
    setTransformedData(processedData);
    setFilteredData(processedData);
  }, [tableData, isColumnarFormat]);
  
  return (
    <div className="p-8 font-sans min-w-[calc(100vh-1rem)]">
      <div className="relative h-[calc(100vh-16rem)] p-2 rounded-2xl bg-black/60 backdrop-blur flex flex-col shadow-lg">
        {/* Tab navigation */}
        <div className="flex mb-1 border-b border-gray-600">
          <button
            onClick={() => handleTabChange('images')}
            className={`px-4 py-2 mr-2 ${
              activeTab === 'images'
                ? 'bg-white text-black rounded-t-lg'
                : 'text-white hover:bg-gray-700'
            }`}
          >
            Imágenes
          </button>
          <button
            onClick={() => handleTabChange('data')}
            className={`px-4 py-2 ${
              activeTab === 'data'
                ? 'bg-white text-black rounded-t-lg'
                : 'text-white hover:bg-gray-700'
            }`}
          >
            Datos
          </button>
        </div>

        {activeTab === 'images' ? (
          // Images View
          <>
            <h2 className="text-center text-white mb-1">
              {titles && titles[currentImageIndex] ? titles[currentImageIndex] : `Imagen ${currentImageIndex + 1}`}
            </h2>
            
            {/* Image selection controls */}
            <div className="flex flex-wrap justify-center mb-2">
              {images.map((_, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectImage(index)}
                  className={`mx-2 px-3 py-1 rounded-full ${
                    currentImageIndex === index
                      ? 'bg-white text-black'
                      : 'bg-gray-700 text-white'
                  }`}
                >
                  {titles && titles[index] ? titles[index] : `Imagen ${index + 1}`}
                </button>
              ))}
            </div>

            {/* Image container */}
            <div className="relative flex-grow flex items-center justify-center overflow-hidden">
                {images.length > 0 ? (
                <img
                  src={images[currentImageIndex]}
                  alt={titles ? titles[currentImageIndex] : `Imagen ${currentImageIndex + 1}`}
                  className="w-full h-full max-w-full max-h-full object-contain "
                />
                ) : (
                <div className="text-white">No hay imágenes disponibles</div>
                )}
              
              {/* Navigation arrows */}
              {images.length > 1 && (
                <>
                  <button
                    onClick={handlePrevImage}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70"
                  >
                    &lt;
                  </button>
                  <button
                    onClick={handleNextImage}
                    className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70"
                  >
                    &gt;
                  </button>
                </>
              )}
            </div>
            
            {/* Page indicator */}
            <div className="text-center text-white mt-2">
              {currentImageIndex + 1} / {images.length}
            </div>
          </>
        ) : (
          // Data Table View
          <div className="flex-grow overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-center text-white">Datos Tabulares</h2>
              {transformedData && transformedData.length > 0 && (
                <CSVDownloadHelper 
                  data={transformedData} 
                  columns={tableColumns && tableColumns.length > 0 
                    ? tableColumns 
                    : transformedData.length > 0 ? Object.keys(transformedData[0]) : []} 
                  filename="datos_analisis.csv" 
                />
              )}
            </div>
            
            {/* Search/filter input */}
            {tableData && tableData.length > 0 && (
              <div className="mb-4">
                <input
                  type="text"
                  placeholder="Buscar en los datos..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:outline-none focus:border-blue-500"
                />
              </div>
            )}
            
            {transformedData && transformedData.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full bg-black/30 text-white">
                  <thead>
                    <tr className="bg-gray-700">
                      {(tableColumns && tableColumns.length > 0 
                      ? tableColumns 
                      : transformedData.length > 0 ? Object.keys(transformedData[0]) : []).map((column, index) => (
                        <th 
                          key={index} 
                          className="px-4 py-2 text-left border-b border-gray-600"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(searchTerm ? filteredData : transformedData).map((row, rowIndex) => (
                      <tr 
                        key={rowIndex} 
                        className={rowIndex % 2 === 0 ? 'bg-black/40' : 'bg-black/20'}
                      >
                        {tableColumns.map((column, colIndex) => (
                          <td 
                            key={colIndex} 
                            className="px-4 py-2 border-b border-gray-700"
                          >
                            {row[column]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-white text-center">No hay datos disponibles</div>
            )}
            
            {/* Additional stats or summary could go here */}
          </div>
        )}
      </div>
    </div>
  );
};

DataImageViewerComponent.defaultProps = {
  images: [],
  titles: null,
  tableData: [],
  tableColumns: []
};

export default DataImageViewerComponent;