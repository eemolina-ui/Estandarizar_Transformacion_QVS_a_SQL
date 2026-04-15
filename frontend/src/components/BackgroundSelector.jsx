import React, { useState } from "react";

export const BackgroundSelector = () => {
  const [selectedClass, setSelectedClass] = useState(""); // Estado para la clase seleccionada

  const handleClassChange = (e) => {
    const body = document.querySelector("body");
    // Remover todas las posibles clases de fondo
    body.classList.remove("greenScreen", "pinkScreen");

    const selectedClass = e.target.value; // Obtener el valor del select
    if (selectedClass) {
      body.classList.add(selectedClass); // Agregar la clase seleccionada
    }
    setSelectedClass(selectedClass); // Actualizar el estado
  };

  return (
    <div className="pointer-events-auto bg-[#BBB9DA] hover:bg-[#7874B4] text-white p-4 rounded-md">
      
      <select
        id="backgroundSelect"
        value={selectedClass}
        onChange={handleClassChange}
        className="ml-2 p-2 border bg-[#BBB9DA] rounded-md pointer-events-auto"
      >
        <option value="">Minsait</option>
        <option value="pinkScreen">Pink</option>
        <option value="greenScreen">Green</option>
      </select>
    </div>
  );
};

// export default BackgroundSelector;
