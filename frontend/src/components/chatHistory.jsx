import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '../hooks/useChat';
import ImageViewerComponent from './ImageViewerComponent';
import MultiDimensionalChart from './ChartComponent';
import CSVDownloadHelper from '../composables/CSVDownloadHelper';

const ChatHistory = ({ clear }) => {
  const { chatHistory, clearConversation } = useChat();
  const [isMinimized, setIsMinimized] = useState(false);
  const [activeMessageId, setActiveMessageId] = useState(null);
  const [fullScreenMedia, setFullScreenMedia] = useState(null);
  const chatEndRef = useRef(null);
  
  // Scroll automático al último mensaje
  useEffect(() => {
    if (!isMinimized && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, isMinimized]);

  useEffect(() => {
    if (clear) {
      clearConversation();
    }
  }, [clear, clearConversation]);

  const toggleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  const toggleMessageMedia = (id) => {
    setActiveMessageId(activeMessageId === id ? null : id);
  };

  // Mostrar contenido en pantalla completa
  const showFullscreen = (content) => {
    setFullScreenMedia(content);
  };

  // Cerrar vista de pantalla completa
  const closeFullscreen = () => {
    setFullScreenMedia(null);
  };

  // Comprobar si un mensaje tiene contenido multimedia
  const hasMedia = (media) => {
    return (
      media && (
        (media.images && media.images.length > 0) ||
        (media.chartData && media.chartData.length > 0) ||
        (media.data && media.data.length > 0) ||
        (media.locations && media.locations.length > 0)
      )
    );
  };

  // Descargar una imagen
  const downloadImage = (imgSrc, index) => {
    const link = document.createElement('a');
    link.href = imgSrc;
    link.download = `imagen_${index + 1}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      {/* Panel principal del historial */}
      <div className={`fixed bottom-0 right-0 z-20 w-96 bg-white bg-opacity-90 backdrop-blur-md rounded-tl-lg shadow-lg transition-all duration-300 ${
        isMinimized ? 'h-12' : 'h-96'
      }`}>
        {/* Encabezado del historial de chat */}
        <div className="flex justify-between items-center px-4 py-2 bg-[#BBB9DA] text-white rounded-tl-lg cursor-pointer" onClick={toggleMinimize}>
          <h3 className="font-bold">Historial de Conversación</h3>
          <button>
            {isMinimized ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            )}
          </button>
        </div>
        
        {/* Contenido del historial de chat */}
        {!isMinimized && (
          <div className="h-[calc(100%-2.5rem)] overflow-y-auto p-4">
            {!chatHistory || chatHistory.length === 0 ? (
              <p className="text-center text-gray-500 italic">No hay mensajes aún</p>
            ) : (
              <>
                {chatHistory.map((msg) => (
                  <div key={msg.id} className="mb-4">
                    <div className="flex justify-between items-start">
                      <div className={`rounded-lg p-3 max-w-[85%] break-words ${msg.isUser ? 'bg-[#e9e9ff] ml-auto' : 'bg-[#f0f0ff]'}`}>
                        <div>
                            {msg.content}
                            {/* {!msg.isUser && msg.sources && msg.sources.length > 0 && (
                                <div className="mt-1">
                                    {msg.sources.map((sourceText, index) => (
                                        <p 
                                            key={index} 
                                            className="text-xs font-medium text-blue-700 leading-tight" 
                                        >
                                            ( Fuente: {sourceText} )
                                        </p>
                                    ))}
                                </div>
                            )} */}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{msg.timestamp}</p>
                      </div>
                      {!msg.isUser && hasMedia(msg.media) && (
                        <button 
                          onClick={() => toggleMessageMedia(msg.id)}
                          className="bg-[#BBB9DA] hover:bg-[#7874B4] text-white p-2 rounded-full ml-2"
                        >
                          {activeMessageId === msg.id ? (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                            </svg>
                          )}
                        </button>
                      )}
                    </div>
                    
                    {/* Contenido multimedia expandido */}
                    {activeMessageId === msg.id && !msg.isUser && (
                      <div className="mt-2 p-3 bg-black/10 rounded-lg">
                        {msg.media.images && msg.media.images.length > 0 && (
                          <div className="mb-2">
                            <div className="flex justify-between items-center mb-1">
                              <h4 className="font-medium text-sm">Imágenes:</h4>
                              <button 
                                onClick={() => showFullscreen({type: 'images', data: msg.media.images})}
                                className="text-xs bg-blue-600 text-white px-1 py-0 rounded hover:bg-blue-700"
                              >
                                Ver completo
                              </button>
                            </div>
                            <div className="flex overflow-x-auto gap-2 pb-2">
                              {msg.media.images.map((img, index) => (
                                <div key={index} className="relative group">
                                  <img 
                                    src={img} 
                                    alt={`Imagen ${index + 1}`} 
                                    className="h-16 w-auto rounded-md cursor-pointer" 
                                    onClick={() => showFullscreen({type: 'image', data: img})}
                                  />
                                  <button 
                                    onClick={() => downloadImage(img, index)}
                                    className="absolute bottom-1 right-1 bg-black/70 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                  >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {msg.media.chartData && msg.media.chartData.length > 0 && (
                          <div className="mb-2">
                            <h4 className="font-medium text-sm mb-1">Gráfico:</h4>
                            <div className="h-32">
                              <MultiDimensionalChart 
                                data={msg.media.chartData} 
                                colors={['#7874B4', '#BBB9DA', '#9E9BC7', '#5D5A9E']}
                              />
                            </div>
                            <button 
                              onClick={() => showFullscreen({type: 'chart', data: msg.media.chartData})}
                              className="text-xs bg-blue-600 text-white px-0 py-0 rounded hover:bg-blue-700 mt-1"
                            >
                              Ver completo
                            </button>
                          </div>
                        )}
                        
                        {msg.media.data && msg.media.data.length > 0 && (
                          <div className="mb-2">
                            <div className="flex justify-between items-center mb-1">
                              <h4 className="font-medium text-sm">Datos:</h4>
                              <div className="flex gap-2">
                                <button 
                                  onClick={() => showFullscreen({type: 'data', data: msg.media.data})}
                                  className="text-xs bg-blue-600 text-white px-1 -py-1 rounded hover:bg-blue-700"
                                >
                                  Ver completo
                                </button>
                                {msg.media.data.length > 0 && (
                                  <CSVDownloadHelper 
                                    data={msg.media.data} 
                                    columns={Object.keys(msg.media.data[0])} 
                                    filename={`datos_${msg.id}.csv`}
                                  />
                                )}
                              </div>
                            </div>
                            <div className="overflow-x-auto">
                              <table className="min-w-full text-sm">
                                <thead>
                                  <tr className="bg-gray-200">
                                    {Object.keys(msg.media.data[0]).map((key) => (
                                      <th key={key} className="py-2 px-3 text-left">{key}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {msg.media.data.slice(0, 3).map((row, index) => (
                                    <tr key={index} className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                                      {Object.values(row).map((value, idx) => (
                                        <td key={idx} className="py-2 px-3">{value}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                              {msg.media.data.length > 3 && (
                                <p className="text-xs text-gray-500 mt-1">
                                  Mostrando 3 de {msg.media.data.length} filas
                                </p>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {msg.media.locations && msg.media.locations.length > 0 && (
                          <div className="mb-2">
                            <h4 className="font-medium text-sm mb-1">Ubicaciones:</h4>
                            <ul className="text-sm">
                              {msg.media.locations.map((location, index) => (
                                <li key={index}>
                                  {location.name || location.address || `Ubicación ${index + 1}`}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        <button 
                          className="text-xs text-[#7874B4] hover:text-[#5D5A9E] mt-2 underline"
                          onClick={() => toggleMessageMedia(msg.id)}
                        >
                          Cerrar
                        </button>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </>
            )}
          </div>
        )}
      </div>

      {/* Vista de pantalla completa para contenido multimedia */}
      {fullScreenMedia && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <button 
            onClick={closeFullscreen}
            className="absolute top-4 right-4 bg-white text-black p-2 rounded-full"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {fullScreenMedia.type === 'image' && (
            <img 
              src={fullScreenMedia.data} 
              alt="Imagen ampliada" 
              className="max-h-[90vh] max-w-[90vw] object-contain"
            />
          )}

          {fullScreenMedia.type === 'images' && (
            <div className="w-full max-w-4xl bg-white rounded-lg overflow-hidden">
              <ImageViewerComponent 
                images={fullScreenMedia.data} 
                titles={[]}
              />
            </div>
          )}

          {fullScreenMedia.type === 'chart' && (
            <div className="w-full max-w-4xl h-[80vh] bg-white rounded-lg p-4">
              <MultiDimensionalChart 
                data={fullScreenMedia.data} 
                colors={['#7874B4', '#BBB9DA', '#9E9BC7', '#5D5A9E']}
              />
            </div>
          )}

          {fullScreenMedia.type === 'data' && (
            <div className="w-full max-w-4xl max-h-[90vh] bg-white rounded-lg p-4 overflow-auto">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Datos Completos</h2>
                <CSVDownloadHelper 
                  data={fullScreenMedia.data} 
                  columns={Object.keys(fullScreenMedia.data[0])} 
                  filename="datos_exportados.csv"
                />
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-200">
                      {Object.keys(fullScreenMedia.data[0]).map((key) => (
                        <th key={key} className="py-2 px-4 text-left border border-gray-300">{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {fullScreenMedia.data.map((row, index) => (
                      <tr key={index} className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                        {Object.values(row).map((value, idx) => (
                          <td key={idx} className="py-2 px-4 border border-gray-300">{value}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default ChatHistory;