import AudioInput from "./AudioInput";
import { useRef, useState, useEffect} from "react";
import { useChat } from "../hooks/useChat";
import {BackgroundSelector} from "./BackgroundSelector";
import CameraComponent from "./CameraComponent";
import ImageViewerComponent from "./ImageViewerComponent";
import MapComponent from "./MapComponent";
import MultiDimensionalChart from "./ChartComponent";
import ChatHistory from "./chatHistory";
//Iconos svg
import Loader2Icon from "./icons/Loader2Icon";
import SendIcon from "./icons/SendIcon";

export const UI = ({ hidden, ...props }) => {
  const input = useRef();
  const cameraRef = useRef();
  const wrapperRef = useRef();
  const suggestionsRef = useRef();
  const fileInputRef = useRef(); // Referencia para el input de archivo
  const { chat, loading, cameraZoomed, setCameraZoomed, message, setCameraAside, cameraAside, clearConversation } = useChat();
  const [isCameraBackground, setIsCameraBackground] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null); // Estado para el archivo seleccionado

  const [locations, setLocations] = useState([]);
  const [sampleData, setSampleData] = useState([]);
  const [imagesData, setImagesData] = useState([]);
  const [tableData, setTableData] = useState({});
  const [tableColumns, setTableColumns] = useState([]);
  const [clearChat, setClearChat] = useState(false);
  const [historyKey, setHistoryKey] = useState(0);
  const timeoutRef = useRef(null);

  const fixedQuestions = [
    "¿Cómo está ayudando Indra a las empresas a usar inteligencia artificial en Chile?",
    "¿Qué hacemos como Indra en sectores críticos del país?",
    "¿En qué se diferencia Minsait dentro de Indra Group?",
    "¿Cuál es el propósito de Indra en Chile más allá de la tecnología?",
    "En una frase, ¿qué es lo que hacemos en Indra Chile?"
  ];

  const QVS = "qvs";
  const ArcExtQVS = `.${QVS}`;

  // Mostrar/ocultar sugerencias al hacer clic en el botón ?
  const toggleSuggestions = () => {
    console.log("Botón ? clickeado - Mostrando sugerencias");
    setShowSuggestions(!showSuggestions);
  };

  // Cerrar menú al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target) &&
          wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Manejar la selección de archivos
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      console.log("Archivo seleccionado:", file.name, "Tamaño:", file.size, "Tipo:", file.type);
      
      // Aquí puedes procesar el archivo según necesites
      // Por ejemplo, leerlo como texto, imagen, etc.
      
      // Opcional: Mostrar una notificación o procesar automáticamente
      // processFile(file);
    }
  };

  // Función para procesar el archivo (opcional)
  const processFile = async (file) => {
    // Ejemplo: Leer archivo de texto
    if (file.type === "text/plain") {
      const text = await file.text();
      console.log("Contenido del archivo:", text);
      // Aquí puedes enviar el contenido al chat o procesarlo
    }
    
    // Ejemplo: Leer imagen
    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        console.log("Imagen cargada:", e.target.result.substring(0, 100));
        // Aquí puedes usar la imagen
      };
      reader.readAsDataURL(file);
    }
  };

  // Limpiar archivo seleccionado (opcional)
  const clearSelectedFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  useEffect(() => {
    if (message && message.locations) {
      setLocations(message.locations);
    }
  }, [message]);

  useEffect(() => {
    if (message && !message.locations) {
      setLocations([]);
    }
  }, [message]);
  useEffect(() => {
    if (message && message.chartData) {
      setCameraAside(true);
      setSampleData(message.chartData);
    }
  }, [message]);
  useEffect(() => {
    if (message && !message.chartData) {
      setCameraAside(false);
      setSampleData([]);
    }
  }, [message]);
  useEffect(() => {
    if (message && message.images) {
      if (message.images.length > 0) {
      setCameraAside(true);
      setImagesData(message.images);
      }
    }
  }, [message]);
  useEffect(() => {
    if (message && !message.images) {
      setCameraAside(false);
      setImagesData([]);
    }
  }, [message]);
  useEffect(() => {
    if (message && message.data) {
      if (message.data.length > 0 ) {
      setCameraAside(true);
      setTableData(message.data);
      setTableColumns(Object.keys(message.data[0]));
      }
    }
  }, [message]);
  useEffect(() => {
    if (message && !message.data) {
      setCameraAside(false);
      setTableData([]);
      setTableColumns([]);
    }
  }, [message]);
  const captureAndSendMessage = (text) => {
    if (!loading && !message) {
      const imageDataUrl = cameraRef.current.captureImage();
      if (imageDataUrl) {
        console.log("Imagen capturada:", imageDataUrl.substring(0, 50) + "...");
      }
      chat(text, imageDataUrl);
      setShowSuggestions(false);
    }
  };

  const sendMessage = () => {
    const text = input.current.value;
    if (text && text.trim()) {
      captureAndSendMessage(text);
      input.current.value = "";
      resetTimer();
    }
  };

  const handleSpeakClick = (transcript) => {
    captureAndSendMessage(transcript);
  };

  const handleToggleBackground = () => {
    setIsCameraBackground(!isCameraBackground);
  };

  const resetTimer = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setClearChat(true);
      setHistoryKey(prev => prev + 1);
    }, 300000);
  };

  useEffect(() => {
    resetTimer();
    return () => clearTimeout(timeoutRef.current);
  }, []);

  useEffect(() => {
    if (message) resetTimer();
  }, [message]);

  useEffect(() => {
    if (clearChat) {
      setClearChat(false);
    }
  }, [clearChat]);

  if (hidden) {
    return null;
  }

  return (
    <>
      <div className={`fixed top-0 left-0 right-0 bottom-0 z-10 flex justify-between p-4 flex-col pointer-events-none ${isCameraBackground ? 'bg-opacity-50 backdrop-blur-sm' : ''}`}> 
        <div className="self-start backdrop-blur-md bg-white bg-opacity-50 p-4 rounded-lg max-w-lg border border-white/20 shadow-xl">
          <h1 className="font-black text-xl">Estandarizar Transformación QVS a SQL</h1>
          { !window.matchMedia("(max-width: 768px)").matches && (
              <p className="text-gray-700"> Mejorando tiempo de transformación de QVS a SQL.</p>
          )}
        </div>

        {/* Inicio :: INPUT DE TIPO FILE CON NOMBRE E ID ESPECÍFICOS */}
        {/*<div className="w-full max-w-lg mx-auto my-4 pointer-events-auto">*/}
        <div className="self-start backdrop-blur-md bg-white bg-opacity-50 p-4 rounded-lg max-w-lg border border-white/40 pointer-events-auto">
          {/* font-medium text-gray-900 dark:text-white */}
          <label 
            htmlFor="InputFile_QVS_01" 
            className="block text-sm font-bold text-gray-700 mb-2"
          >📎 Seleccione el archivo extencion {QVS.toUpperCase()}
          </label>          
          <input
            ref={fileInputRef}
            id="InputFile_QVS_01"
            name="InputFile_QVS_01"
            type="file"
            className="w-full p-3 border-2 border-dashed border-[#7874B4] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#7874B4] bg-white bg-opacity-90 backdrop-blur-sm text-gray-800 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#7874B4] file:text-white hover:file:bg-[#5e5a95] cursor-pointer"
            onChange={handleFileChange}
            accept={ArcExtQVS}
          />
          
          {selectedFile && (
            <div className="mt-2 flex items-center justify-between bg-gray-100 p-2 rounded">
              <span className="text-sm text-gray-700 truncate flex-1">
                📄 {selectedFile.name}
              </span>
              <button
                type="button"
                onClick={clearSelectedFile}
                className="ml-2 text-red-500 hover:text-red-700 text-xs"
              >
                ✖
              </button>
            </div>
          )}
          
          <p className="text-xs text-gray-600 mt-2">
            📌 Puedes cargar archivos {QVS.toUpperCase()} para consultar su contenido
          </p>
        </div>
        {/* Fin :: INPUT DE TIPO FILE CON NOMBRE E ID ESPECÍFICOS */}

        <CameraComponent 
          ref={cameraRef} 
          isBackground={isCameraBackground}
          onToggleBackground={handleToggleBackground}
        />

        <div className="flex justify-between items-center w-full">
          <div className="flex flex-col items-start">
            {locations.length > 0 && (
              <div className="map-container pointer-events-auto">
                <MapComponent locations={locations} />
              </div>
            )}
          </div>
          <div className="flex flex-col items-end">
            {sampleData.length > 0 && (
              <div className="chart-container pointer-events-auto">
                <MultiDimensionalChart data={sampleData} />
              </div>
            )}
          </div>
          {/* <div className="flex flex-col items-end">
            {imagesData.length>0 && (
              <div className="image-container pointer-events-auto">
                <ImageViewerComponent images={imagesData} titles={[]} tableData={tableData} tableColumns={tableColumns} />
              </div>
            )}
          </div>
          <div className="flex flex-col items-end">
            <button
              onClick={() => setCameraZoomed(!cameraZoomed)}
              className="pointer-events-auto bg-[#BBB9DA] hover:bg-[#7874B4] text-white p-4 rounded-md"
            >
              {cameraZoomed ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM13.5 10.5h-6"
                  />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6"
                  />
                </svg>
              )}
            </button>
          </div> */}

        </div>
        
        <div className="pointer-events-auto max-w-lg w-full mx-auto" ref={wrapperRef}>
            {/* Menú de preguntas frecuentes */}
            {showSuggestions && (
              <div 
                ref={suggestionsRef}
                className="mb-2 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden z-50"
              >
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-700">
                  📌 Preguntas frecuentes
                </div>
                <div className="p-2 flex flex-col gap-1 max-h-64 overflow-y-auto">
                  {fixedQuestions.map((question, idx) => (
                    <button
                      key={idx}
                      onClick={() => captureAndSendMessage(question)}
                      disabled={loading || message}
                      className="text-left px-3 py-2 rounded-lg text-sm hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center w-full rounded-2xl p-2 gap-2 bg-opacity-50 bg-white backdrop-blur-md shadow-lg">
                <input
                  className="flex-1 min-w-0 placeholder:text-gray-800 placeholder:italic py-2 px-3 rounded-lg bg-transparent border-none focus:outline-none"
                  placeholder="¿En qué te puedo ayudar?"
                  ref={input}
                  onKeyDown={(e) => {
                      if (e.key === "Enter") {
                          sendMessage();
                      }
                  }}
                />
                
                <button
                    disabled={loading || message}
                    onClick={sendMessage}
                    className={`flex-shrink-0 bg-[#7874B4] hover:bg-[#5e5a95] text-white p-2 rounded-xl transition-colors ${ 
                        loading || message ? "cursor-not-allowed opacity-50" : ""
                    }`}
                    aria-label="Enviar"
                >
                    {loading ? (
                        <Loader2Icon className="animate-spin w-5 h-5" /> 
                    ) : (
                        <SendIcon className="w-5 h-5" />
                    )}
                </button>
                
                <AudioInput onSpeechEnd={handleSpeakClick} />

                {/* Inicio ::  Botón de interrogación ? 
                <button
                    type="button"
                    onClick={toggleSuggestions}
                    disabled={loading || message}
                    className="flex-shrink-0 bg-gray-500 hover:bg-gray-600 text-white p-2 rounded-xl transition-colors"
                    aria-label="Preguntas frecuentes"
                    title="Ver preguntas frecuentes"
                >
                    <span className="text-white font-bold text-lg">?</span>
                </button>
                 Fin ::  Botón de interrogación ? */}
                {/* Inicio ::  Botón de interrogación - segunda opción */}
                <button
                    type="button"
                    onClick={toggleSuggestions}
                    disabled={loading || message}
                    className="text-white p-1 rounded-full flex-shrink-0 bg-[#BBB9DA] hover:bg-[#7874B4]"
                    aria-label="Preguntas frecuentes"
                    title="Ver preguntas frecuentes"
                >
                  <span className="text-black font-bold text-lg">&nbsp; ? &nbsp; </span>
                </button>
                {/* Fin ::  Botón de interrogación - segunda opción */}
            </div>
        </div>
      </div>
      
      {/* Añadimos el componente de historial de chat */}
      <ChatHistory key={historyKey} clear={clearChat} />
    </>
  );
};
