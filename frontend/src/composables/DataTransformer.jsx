/**
 * Transforma datos de formato columnar indexado a formato tabular de filas
 * 
 * Entrada:
 * {
 *   columna1: {0: 'valor1', 1: 'valor2', ...},
 *   columna2: {0: 'valor3', 1: 'valor4', ...},
 * }
 * 
 * Salida:
 * [
 *   {columna1: 'valor1', columna2: 'valor3'},
 *   {columna1: 'valor2', columna2: 'valor4'},
 *   ...
 * ]
 */
const transformColumnarToTabular = (columnarData) => {
    if (!columnarData || typeof columnarData !== 'object') {
      return [];
    }
    
    // Determinar el número máximo de filas examinando las claves numéricas
    const columnNames = Object.keys(columnarData);
    if (columnNames.length === 0) return [];
    
    let maxRows = 0;
    
    for (const columnName of columnNames) {
      const columnData = columnarData[columnName];
      if (columnData && typeof columnData === 'object') {
        const rowIndices = Object.keys(columnData).map(key => parseInt(key));
        if (rowIndices.length > 0) {
          const maxIndex = Math.max(...rowIndices);
          maxRows = Math.max(maxRows, maxIndex + 1);
        }
      }
    }
    
    // Crear array de objetos de filas
    const rows = [];
    
    for (let i = 0; i < maxRows; i++) {
      const row = {};
      
      for (const columnName of columnNames) {
        const columnData = columnarData[columnName];
        if (columnData && typeof columnData === 'object') {
          row[columnName] = columnData[i] !== undefined ? columnData[i] : null;
        } else {
          row[columnName] = null;
        }
      }
      
      rows.push(row);
    }
    
    return rows;
  };
  
  export default transformColumnarToTabular;