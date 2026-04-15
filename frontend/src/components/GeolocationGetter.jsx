import { useState, useEffect } from 'react';

// Hook personalizado para obtener coordenadas geográficas
const useGeolocation = () => {
  // Definir estados para la latitud y longitud, con valores predeterminados
  const [latitude, setLatitude] = useState('19.4396757');
  const [longitude, setLongitude] = useState('-99.2027084');
  const [error, setError] = useState(null);  // Para almacenar errores, si ocurren

  useEffect(() => {
    // Verificar si la geolocalización está soportada
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          // Actualizar las coordenadas con los valores del navegador
          setLatitude(position.coords.latitude.toString());
          setLongitude(position.coords.longitude.toString());
        },
        (err) => {
          // Si ocurre un error, lo almacenamos
          setError('Error getting location, using default coordinates');
          console.error('Error getting location, using default coordinates:', err);
          setLatitude(import.meta.env.VITE_DEFAULT_LATITUDE);
          setLongitude(import.meta.env.VITE_DEFAULT_LONGITUDE);
        },
        { timeout: 5000 }
      );
    } else {
      // Si la geolocalización no está soportada
      setError('Geolocation is not supported by this browser.');
      console.warn('Geolocation is not supported, using default coordinates.');
    }
  }, []);  // Este hook se ejecutará solo una vez al montar el componente

  // Retornar las coordenadas (y el error si existe)
  return { latitude, longitude, error };
};

export default useGeolocation;
