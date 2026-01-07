"use client";

import { useState, useRef, useEffect } from "react";

interface HeatmapData {
  districts: string[];
  crimeTypes: string[];
  data: {
    [district: string]: {
      [crimeType: string]: number;
    };
  };
}

interface HeatmapJson {
  crimeRate: HeatmapData;
  arrestRate: HeatmapData;
}

interface InteractiveHeatmapProps {
  imageSrc: string;
  dataType: "crimeRate" | "arrestRate";
  title: string;
}

export default function InteractiveHeatmap({
  imageSrc,
  dataType,
  title,
}: InteractiveHeatmapProps) {
  const [heatmapData, setHeatmapData] = useState<HeatmapJson | null>(null);
  const [tooltip, setTooltip] = useState<{
    district: string;
    crimeType: string;
    value: number;
    x: number;
    y: number;
  } | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  // 히트맵 데이터 로드
  useEffect(() => {
    fetch("/heatmap_data.json")
      .then((res) => res.json())
      .then((data: HeatmapJson) => {
        setHeatmapData(data);
      })
      .catch((err) => {
        console.error("히트맵 데이터 로드 실패:", err);
      });
  }, [dataType]);

  // 이미지 로드 시 크기 저장
  const handleImageLoad = () => {
    if (imageRef.current) {
      const rect = imageRef.current.getBoundingClientRect();
      setImageSize({ width: rect.width, height: rect.height });
    }
  };

  // 셀 오버레이 렌더링 - 각 셀을 실제 클릭 가능한 영역으로 만들기
  const renderCellOverlay = () => {
    if (!imageRef.current || !heatmapData || !imageSize) return null;

    // 셀 영역 계산
    const cellAreaLeft = imageSize.width * 0.10;
    const cellAreaRight = imageSize.width * 0.90;
    const cellAreaTop = imageSize.height * 0.06;
    const cellAreaBottom = imageSize.height * 0.94;
    const cellWidth = (cellAreaRight - cellAreaLeft) / heatmapData[dataType].crimeTypes.length;
    const cellHeight = (cellAreaBottom - cellAreaTop) / heatmapData[dataType].districts.length;

    return (
      <div className="absolute inset-0 pointer-events-none">
        {heatmapData[dataType].districts.map((district, di) =>
          heatmapData[dataType].crimeTypes.map((crimeType, ci) => {
            const value = heatmapData[dataType].data[district]?.[crimeType] ?? 0;
            
            return (
              <div
                key={`${di}-${ci}`}
                className="absolute cursor-pointer hover:bg-blue-500/20 transition-colors"
                style={{
                  left: `${cellAreaLeft + ci * cellWidth}px`,
                  top: `${cellAreaTop + di * cellHeight}px`,
                  width: `${cellWidth}px`,
                  height: `${cellHeight}px`,
                  pointerEvents: 'auto',
                }}
                onMouseEnter={(e) => {
                  setTooltip({
                    district,
                    crimeType,
                    value,
                    x: e.clientX,
                    y: e.clientY,
                  });
                }}
                onMouseMove={(e) => {
                  if (!tooltip) return;
                  
                  setTooltip({
                    ...tooltip,
                    x: e.clientX,
                    y: e.clientY,
                  });
                }}
                onMouseLeave={() => {
                  setTooltip(null);
                }}
              />
            );
          })
        )}
      </div>
    );
  };

  if (!heatmapData) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-500">데이터 로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="relative w-full flex items-center justify-center bg-white">
      <div
        ref={containerRef}
        className="relative inline-block"
      >
        <img
          ref={imageRef}
          src={imageSrc}
          alt={title}
          className="block max-w-full h-auto"
          draggable={false}
          onLoad={handleImageLoad}
        />
        {renderCellOverlay()}
        {tooltip && (
          <div
            className="fixed z-50 bg-gray-900 text-white px-4 py-3 rounded-lg shadow-2xl text-sm border-2 border-blue-500 min-w-[180px] pointer-events-none"
            style={{
              left: `${tooltip.x + 20}px`,
              top: `${tooltip.y - 10}px`,
            }}
          >
            <div className="font-bold mb-2 text-blue-300 text-lg border-b border-gray-700 pb-1">
              {tooltip.district}
            </div>
            <div className="text-sm text-gray-300 mb-2 font-semibold">
              {tooltip.crimeType}
            </div>
            <div className="text-base font-mono text-green-300 font-bold bg-gray-800 px-2 py-1 rounded">
              {tooltip.value.toFixed(6)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
