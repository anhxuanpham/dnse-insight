/**
 * Market Heatmap Component
 * Displays market performance as a treemap
 */
import React from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

interface HeatmapData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
}

interface MarketHeatmapProps {
  data: HeatmapData[];
}

const COLORS = {
  strong_gain: '#00C851',
  gain: '#26a69a',
  neutral: '#78909c',
  loss: '#ff6b6b',
  strong_loss: '#cc0000',
};

const getColor = (changePercent: number): string => {
  if (changePercent >= 3) return COLORS.strong_gain;
  if (changePercent >= 0.5) return COLORS.gain;
  if (changePercent >= -0.5) return COLORS.neutral;
  if (changePercent >= -3) return COLORS.loss;
  return COLORS.strong_loss;
};

export const MarketHeatmap: React.FC<MarketHeatmapProps> = ({ data }) => {
  // Transform data for treemap
  const treemapData = data.map(item => ({
    name: item.symbol,
    size: item.volume,
    change: item.change_percent,
    price: item.price,
    fill: getColor(item.change_percent),
  }));

  const CustomContent = (props: any) => {
    const { x, y, width, height, name, change, price } = props;

    if (width < 50 || height < 30) return null;

    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          style={{
            fill: props.fill,
            stroke: '#1e1e1e',
            strokeWidth: 2,
          }}
        />
        <text
          x={x + width / 2}
          y={y + height / 2 - 10}
          textAnchor="middle"
          fill="#fff"
          fontSize={width > 80 ? 14 : 10}
          fontWeight="bold"
        >
          {name}
        </text>
        <text
          x={x + width / 2}
          y={y + height / 2 + 10}
          textAnchor="middle"
          fill="#fff"
          fontSize={width > 80 ? 12 : 8}
        >
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </text>
        {width > 100 && (
          <text
            x={x + width / 2}
            y={y + height / 2 + 25}
            textAnchor="middle"
            fill="#fff"
            fontSize={10}
          >
            {price.toFixed(2)}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className="market-heatmap bg-gray-900 rounded-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">Market Heatmap</h2>
      <ResponsiveContainer width="100%" height={400}>
        <Treemap
          data={treemapData}
          dataKey="size"
          aspectRatio={4 / 3}
          stroke="#1e1e1e"
          fill="#8884d8"
          content={<CustomContent />}
        >
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-gray-800 p-3 rounded shadow-lg border border-gray-700">
                    <p className="text-white font-bold">{data.name}</p>
                    <p className="text-sm text-gray-300">Price: {data.price.toFixed(2)}</p>
                    <p className={`text-sm ${data.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      Change: {data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}%
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};
