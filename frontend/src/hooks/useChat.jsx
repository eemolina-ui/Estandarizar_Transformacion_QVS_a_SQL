import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { v4 as uuidv4 } from 'uuid';
import useGeolocation from '../components/GeolocationGetter';

const backendUrl = "http://localhost:3000";
const uuid = uuidv4();
const ChatContext = createContext();


/**
 * Agrupa un array de objetos de fuente (source, page) en un array de strings concisos.
 * Ejemplo: [{"source": "doc.pdf", "page": 4}, {"source": "doc.pdf", "page": 5}] -> ["doc.pdf (Pág: 4, 5)"]
 */
const groupAndFormatSources = (sources) => {
  if (!Array.isArray(sources)) {
      return [];
  }
  const groupedSources = {};

  sources.forEach(sourceObj => {
      const source = sourceObj.source || "Desconocido";
      const page = String(sourceObj.page) || "N/A"; // Asegurar que sea string

      if (!groupedSources[source]) {
          // Usamos Set para asegurar unicidad de páginas
          groupedSources[source] = new Set(); 
      }
      // Solo añadimos la página si no es "N/A"
      if (page !== "N/A") {
          groupedSources[source].add(page);
      }
  });

  return Object.keys(groupedSources).map(source => {
      const pages = Array.from(groupedSources[source]);
      if (pages.length === 0) {
          // Si no hay páginas específicas (solo documentos sin página o "N/A")
          return `${source}`; 
      } else {
          // Ordenar las páginas (intenta ordenar numéricamente)
          const sortedPages = pages.map(p => {
              const num = parseInt(p, 10);
              return isNaN(num) ? p : num;
          }).sort((a, b) => {
              if (typeof a === 'number' && typeof b === 'number') {
                  return a - b;
              }
              return String(a).localeCompare(String(b));
          }).join(', ');
          return `${source} Pág: ${sortedPages}`;
      }
  });
};

const parseStreamMessage = (chunk) => {
  try {
    return chunk
      .split('\n')
      .filter(line => line.trim())
      .map(line => {
        try {
          const parsed = JSON.parse(line);
          // Validate required fields
          const required = ['text', 'facialExpression', 'animation'];
          const hasAllRequired = required.every(field => 
            parsed.hasOwnProperty(field) && parsed[field] !== undefined
          );
          
          if (!hasAllRequired) {
            console.warn('Message missing required fields:', parsed);
            return null;
          }
          
          return parsed;
        } catch (e) {
          console.error('Error parsing message:', e);
          return null;
        }
      })
      .filter(msg => msg !== null);
  } catch (e) {
    console.error('Error processing chunk:', e);
    return [];
  }
};

export const ChatProvider = ({ children }) => {
  const { latitude, longitude } = useGeolocation();
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const [cameraAside, setCameraAside] = useState(false);
  // Estado para mantener el historial completo de la conversación
  const [chatHistory, setChatHistory] = useState([]);

  const getDefaultMessage = async (type) => {
    try {
      const audioResponse = await fetch(`./src/assets/default_messages/${type}/audio.mp3`);
      const metadataResponse = await fetch(`./src/assets/default_messages/${type}/json_metadata.json`);
      
      if (!audioResponse.ok || !metadataResponse.ok) {
        throw new Error('Failed to fetch default messages');
      }
  
      const audioBlob = await audioResponse.blob();
      const metadata = await metadataResponse.json();
      
      const audioBase64 = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(audioBlob);
      });
  
      return {
        text: type === 'error' 
          ? 'Lo siento, hubo un error en la comunicación. ¿Podrías intentarlo de nuevo?'
          : 'El servicio no está disponible en este momento. Por favor, intenta más tarde.',
        audio: audioBase64,
        lipsync: metadata,
        facialExpression: metadata.facialExpression || 'sad',
        animation: metadata.animation || 'Talking_0',
        error: true
      };
    } catch (error) {
      console.error('Error loading default message:', error);
      return {
        text: 'Error de comunicación',
        error: true
      };
    }
  };

  const processStreamResponse = useCallback(async (response) => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process complete messages from buffer
        const newlineIndex = buffer.lastIndexOf('\n');
        if (newlineIndex !== -1) {
          const completeChunk = buffer.substring(0, newlineIndex);
          buffer = buffer.substring(newlineIndex + 1);
          
          const parsedMessages = parseStreamMessage(completeChunk);
          if (parsedMessages.length > 0) {
            setMessages(prev => [...prev, ...parsedMessages]);
          }
        }
      }

      // Process any remaining buffer content
      if (buffer.trim()) {
        const parsedMessages = parseStreamMessage(buffer);
        if (parsedMessages.length > 0) {
          setMessages(prev => [...prev, ...parsedMessages]);
        }
      }
    } catch (error) {
      console.error('Error processing stream:', error);
      throw error;
    }
  }, []);

  const chat = useCallback(async (message, image) => {
    setLoading(true);
    const requestBody = {
      message,
      image,
      userId: uuid,
      coordinates: `${latitude}, ${longitude}`
    };

    // Añadir el mensaje del usuario al historial
    const userMessage = {
      id: Date.now(),
      content: message,
      timestamp: new Date().toLocaleTimeString(),
      isUser: true
    };
    setChatHistory(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      await processStreamResponse(response);
    } catch (error) {
      console.error('Error in chat:', error);
      const defaultMessage = await getDefaultMessage(
        error.message === 'Failed to fetch' ? 'unavailable' : 'error'
      );
      setMessages(prev => [...prev, defaultMessage]);
    } finally {
      setLoading(false);
    }
  }, [latitude, longitude, processStreamResponse]);

  const onMessagePlayed = useCallback(() => {
    if (messages.length > 0) {
      const playedMessage = messages[0];
      
      // Añadir el mensaje del asistente al historial
      if (!playedMessage.error) {
        const finalSources = groupAndFormatSources(playedMessage.sources);
        const assistantMessage = {
          id: Date.now(),
          content: playedMessage.text,
          timestamp: new Date().toLocaleTimeString(),
          isUser: false,
          media: {
            images: playedMessage.images || [],
            chartData: playedMessage.chartData || [],
            data: playedMessage.data || [],
            locations: playedMessage.locations || []
          },
          sources: finalSources
        };
        setChatHistory(prev => [...prev, assistantMessage]);
      }
      
      setMessages(prevMessages => prevMessages.slice(1));
    }
  }, [messages]);

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  const clearConversation = () => {
    setChatHistory([]);
    setMessages([]);
    setMessage(null);
  };

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
        cameraAside,
        setCameraAside,
        chatHistory, // Exponemos el historial completo
        clearConversation
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};