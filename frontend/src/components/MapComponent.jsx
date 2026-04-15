// src/components/MapComponent.jsx
import React, { useState } from "react";
import { GoogleMap, LoadScript, Marker, } from "@react-google-maps/api";
// import { ApiProvider, Map, AdvancedMarker, MapCameraChangedEvent, Pin} from "@vis.gl/react-google-maps";
import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";


const MapComponent = ({ locations }) => {
  if (!locations) {
    return null;
  }
  else {
  const [currentLocation, setCurrentLocation] = useState(0);
  // Configuración para el slider
  const sliderSettings = {
    dots: true,
    infinite: true,
    speed: 500,
    slidesToShow: 1,
    slidesToScroll: 1,
    afterChange: (index) => setCurrentLocation(index),
  };

  return (
    <>
    <div style={styles.container}>
      <LoadScript googleMapsApiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
        <GoogleMap
          mapContainerStyle={styles.mapStyles}
          zoom={16}
          center={{
            lat: locations[currentLocation].lat,
            lng: locations[currentLocation].lng,
          }}
        >
          <Marker
            key={locations[currentLocation].name}
            position={{
              lat: locations[currentLocation].lat,
              lng: locations[currentLocation].lng,
            }}
          />

        </GoogleMap>
      </LoadScript>

      {/* Slider debajo del mapa */}
      <Slider {...sliderSettings}>
        {locations.map((location, index) => (
          <div key={index} center>
            <h3>{location.name}</h3>
          </div>
        ))}
      </Slider>
    </div>
    </>
  );
  }
};

const styles = {
  container: {
    width: "30vh",
    height: "40vh",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
  },
  mapStyles: {
    height: "30vh", 
    width: "20vh",
    justifyContent: "center",
  },
};

export default MapComponent;
