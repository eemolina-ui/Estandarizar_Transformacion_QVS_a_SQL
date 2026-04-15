import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const MultiDimensionalChart = ({ data, colors }) => {
  // Get all metrics dynamically from 'variables'
  const metrics = Array.from(
    new Set(data.flatMap((entry) => Object.keys(entry.variables)))
  );

  // Initialize with all metrics selected
  const [selectedMetrics, setSelectedMetrics] = useState(metrics);

  const handleMetricToggle = (metric) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric)
        ? prev.filter((m) => m !== metric)
        : [...prev, metric]
    );
  };

  const transformedData = data.map((entry) => ({
    date: entry.date,
    ...entry.variables,
  }));

  return (
    <div className="p-8 font-sans min-w-[calc(100vh-1rem)]">
      <div className="relative h-[calc(100vh-16rem)] p-8 rounded-2xl bg-black/60 backdrop-blur">
        <h2 className="text-center text-white mb-4">Comparación de Métricas</h2>
        
        <div className="flex flex-wrap justify-center mb-4">
          {metrics.map((metric) => (
            <label key={metric} className="mx-2 cursor-pointer text-white">
              <input
                type="checkbox"
                checked={selectedMetrics.includes(metric)}
                onChange={() => handleMetricToggle(metric)}
                className="mr-2"
              />
              {metric}
            </label>
          ))}
        </div>

        <ResponsiveContainer width="100%" height="80%">
          <LineChart data={transformedData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cccccc" />
            <XAxis dataKey="date" tick={{ fill: '#cccccc' }} />
            <YAxis tick={{ fill: '#cccccc' }} />
            <Tooltip contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', color: '#000' }} />
            <Legend wrapperStyle={{ color: '#cccccc' }} />
            {selectedMetrics.map((metric, index) => (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                stroke={colors[index % colors.length]}
                activeDot={{ r: 8 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

MultiDimensionalChart.defaultProps = {
  colors: ['#ecd2f2', '#69e0ff', '#faaca8', '#ddd6f3', '#fff', '#000']
};

export default MultiDimensionalChart;