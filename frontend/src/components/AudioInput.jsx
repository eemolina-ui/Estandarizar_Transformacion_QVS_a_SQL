import React, { useState, useEffect } from 'react';
import { useChat } from '../hooks/useChat';

import StopIcon from "./icons/StopIcon";
import MicIcon from "./icons/MicIcon";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const AudioInput = ({ onSpeechEnd }) => {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const { chat } = useChat();

  useEffect(() => {
   if (SpeechRecognition) {
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.lang = 'es-MX';
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;

      recognitionInstance.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');

        if (event.results[0].isFinal) {
          onSpeechEnd(transcript);
          recognitionInstance.stop();
          setIsListening(false);
        }
      };

      setRecognition(recognitionInstance);
      setIsSupported(true);
    } else {
      console.log('El reconocimiento de voz no está soportado en este navegador.');
      setIsSupported(false); // El soporte NO está disponible
    }

    return () => {
      if (recognition) {
        recognition.stop();
      }
    };
  }, [chat, onSpeechEnd]);

  const toggleListening = () => {
    if (!recognition) {
      if (!isSupported) {
          alert('¡Ups! Tu navegador no soporta la entrada de voz. Intenta con Chrome.');
      }
      return;
    }
    
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
    setIsListening(!isListening);
  };

  return (
    <button
      onClick={toggleListening}
      className={` text-white p-2 rounded-full flex-shrink-0 ${
        isListening ? 'bg-red-500 hover:bg-red-600 animate-pulse' : 'bg-[#BBB9DA] hover:bg-[#7874B4]'}
      `}
      aria-label={isListening ? 'Detener' : 'Hablar'} 
    >
     {isListening ? (
      <StopIcon className="w-5 h-5" /> 
    ) : (
      <MicIcon className="w-5 h-5" /> 
    )}
    </button>
  );
};

export default AudioInput;