"use client";

import { useState, useRef } from "react";

interface GenerateResponse {
  id: string;
  image_url: string;
  meta_url: string;
  meta: {
    id: string;
    created_at: string;
    prompt: string;
    negative_prompt?: string;
    width: number;
    height: number;
    steps: number;
    guidance_scale: number;
    strength?: number;
    seed?: number;
    device: string;
  };
}

export default function DiffusionPage() {
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [steps, setSteps] = useState(20);
  const [guidanceScale, setGuidanceScale] = useState(7.5);
  const [strength, setStrength] = useState(0.75);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [initImage, setInitImage] = useState<File | null>(null);
  const [initImagePreview, setInitImagePreview] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [meta, setMeta] = useState<GenerateResponse["meta"] | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError("프롬프트를 입력해주세요.");
      return;
    }

    setIsGenerating(true);
    setError(null);
    setGeneratedImage(null);
    setMeta(null);

    try {
      // FormData 사용 (이미지 파일이 있을 수 있으므로)
      const formData = new FormData();
      formData.append("prompt", prompt.trim());
      if (negativePrompt.trim()) {
        formData.append("negative_prompt", negativePrompt.trim());
      }
      if (!initImage) {
        // txt2img 모드일 때만 width, height 사용
        formData.append("width", width.toString());
        formData.append("height", height.toString());
      }
      formData.append("steps", steps.toString());
      formData.append("guidance_scale", guidanceScale.toString());
      if (initImage) {
        // img2img 모드일 때 strength 사용
        formData.append("strength", strength.toString());
        formData.append("init_image", initImage);
      }
      if (seed !== undefined) {
        formData.append("seed", seed.toString());
      }

      console.log("FormData 전송 시작:", {
        prompt,
        hasImage: !!initImage,
        steps,
        guidanceScale,
        strength: initImage ? strength : undefined,
      });

      const response = await fetch("http://localhost:8000/api/v1/generate", {
        method: "POST",
        body: formData,
      });

      console.log("서버 응답 상태:", response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("서버 에러 응답:", errorText);
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `서버 오류: ${response.status}` };
        }
        throw new Error(errorData.detail || `서버 오류: ${response.status}`);
      }

      const data: GenerateResponse = await response.json();
      console.log("생성 성공:", data);
      
      // 이미지 URL 생성 (로컬 서버 주소와 결합)
      const imageUrl = `http://localhost:8000${data.image_url}`;
      
      setGeneratedImage(imageUrl);
      setMeta(data.meta);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "이미지 생성 중 오류가 발생했습니다.";
      setError(errorMessage);
      console.error("Generation error:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleImageSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("이미지 파일만 업로드할 수 있습니다.");
      return;
    }
    setInitImage(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setInitImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    setError(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleImageSelect(file);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageSelect(file);
    }
  };

  const handleRemoveImage = () => {
    setInitImage(null);
    setInitImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRandomSeed = () => {
    setSeed(Math.floor(Math.random() * 2147483647));
  };

  const handleReset = () => {
    setPrompt("");
    setNegativePrompt("");
    setWidth(512);
    setHeight(512);
    setSteps(20);
    setGuidanceScale(7.5);
    setStrength(0.75);
    setSeed(undefined);
    setInitImage(null);
    setInitImagePreview(null);
    setGeneratedImage(null);
    setMeta(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="min-h-screen bg-[#1b1b1f] text-white">
      <div className="container mx-auto px-4 py-6">
        {/* 헤더 */}
        <div className="mb-4">
          <h1 className="text-2xl font-semibold text-white">Stable Diffusion</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(400px,500px)_1fr] gap-4">
          {/* 왼쪽: 설정 패널 */}
          <div className="bg-[#262629] rounded-lg p-4 space-y-4">
            {/* Positive Prompt */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter prompt here..."
                className="w-full px-3 py-2 bg-[#1b1b1f] border border-[#3a3a3d] rounded text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500"
                rows={4}
                disabled={isGenerating}
              />
            </div>

            {/* Negative Prompt */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Negative prompt
              </label>
              <textarea
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                placeholder="Negative prompt (optional)"
                className="w-full px-3 py-2 bg-[#1b1b1f] border border-[#3a3a3d] rounded text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500"
                rows={3}
                disabled={isGenerating}
              />
            </div>

            {/* Image Upload (Image-to-Image) */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                초기 이미지 (선택사항 - Image-to-Image)
              </label>
              {initImagePreview ? (
                <div className="relative">
                  <img
                    src={initImagePreview}
                    alt="Preview"
                    className="w-full h-48 object-contain bg-[#1b1b1f] rounded border border-[#3a3a3d]"
                  />
                  <button
                    onClick={handleRemoveImage}
                    disabled={isGenerating}
                    className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold"
                    title="이미지 제거"
                  >
                    ×
                  </button>
                  <p className="text-xs text-gray-400 mt-1">{initImage?.name}</p>
                </div>
              ) : (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`w-full h-32 border-2 border-dashed rounded flex items-center justify-center cursor-pointer transition-colors ${
                    isDragging
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-[#3a3a3d] hover:border-[#4a4a4d] bg-[#1b1b1f]"
                  } ${isGenerating ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <div className="text-center text-gray-400">
                    <p className="text-sm">이미지를 드래그하거나 클릭하여 업로드</p>
                    <p className="text-xs mt-1">Image-to-Image 모드 활성화</p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileInputChange}
                    className="hidden"
                    disabled={isGenerating}
                  />
                </div>
              )}
            </div>

            {/* Generate Button */}
            <div>
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
                className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded transition-colors"
              >
                {isGenerating ? "Generating..." : "Generate"}
              </button>
            </div>

            {/* Settings */}
            <div className="space-y-3 pt-2 border-t border-[#3a3a3d]">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Sampling steps: {steps}
                </label>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={steps}
                  onChange={(e) => setSteps(parseInt(e.target.value))}
                  className="w-full"
                  disabled={isGenerating}
                />
              </div>

              {!initImage && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Width: {width}
                    </label>
                    <input
                      type="number"
                      value={width}
                      onChange={(e) => setWidth(parseInt(e.target.value) || 512)}
                      min={64}
                      max={512}
                      step={8}
                      className="w-full px-3 py-2 bg-[#1b1b1f] border border-[#3a3a3d] rounded text-white focus:outline-none focus:border-blue-500"
                      disabled={isGenerating}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Height: {height}
                    </label>
                    <input
                      type="number"
                      value={height}
                      onChange={(e) => setHeight(parseInt(e.target.value) || 512)}
                      min={64}
                      max={512}
                      step={8}
                      className="w-full px-3 py-2 bg-[#1b1b1f] border border-[#3a3a3d] rounded text-white focus:outline-none focus:border-blue-500"
                      disabled={isGenerating}
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Guidance Scale: {guidanceScale}
                </label>
                <input
                  type="range"
                  min="0"
                  max="20"
                  step="0.5"
                  value={guidanceScale}
                  onChange={(e) => setGuidanceScale(parseFloat(e.target.value))}
                  className="w-full"
                  disabled={isGenerating}
                />
              </div>

              {initImage && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Strength: {strength} (높을수록 원본 유지)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={strength}
                    onChange={(e) => setStrength(parseFloat(e.target.value))}
                    className="w-full"
                    disabled={isGenerating}
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Seed
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={seed || -1}
                    onChange={(e) => setSeed(e.target.value === "-1" ? undefined : parseInt(e.target.value) || undefined)}
                    className="flex-1 px-3 py-2 bg-[#1b1b1f] border border-[#3a3a3d] rounded text-white focus:outline-none focus:border-blue-500"
                    disabled={isGenerating}
                  />
                  <button
                    onClick={handleRandomSeed}
                    disabled={isGenerating}
                    className="px-3 py-2 bg-[#3a3a3d] hover:bg-[#4a4a4d] rounded text-white transition-colors"
                    title="Random seed"
                  >
                    🎲
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-1">-1 for random</p>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-900/50 border border-red-700 rounded p-3 text-red-200 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* 오른쪽: 이미지 미리보기 */}
          <div className="bg-[#262629] rounded-lg p-4">
            <div className="sticky top-4">
              <h2 className="text-lg font-semibold mb-4">Generated Image</h2>
              
              {generatedImage ? (
                <div className="space-y-4">
                  {/* 이미지 */}
                  <div className="bg-[#1b1b1f] rounded-lg overflow-hidden border border-[#3a3a3d] aspect-square flex items-center justify-center">
                    <img
                      src={generatedImage}
                      alt="Generated"
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='512' height='512'%3E%3Crect fill='%231b1b1f' width='512' height='512'/%3E%3Ctext fill='%23fff' font-family='sans-serif' font-size='20' x='50%25' y='50%25' text-anchor='middle' dominant-baseline='middle'%3E이미지를 불러올 수 없습니다%3C/text%3E%3C/svg%3E";
                      }}
                    />
                  </div>

                  {/* 이미지 액션 버튼들 */}
                  {meta && (
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = generatedImage!;
                          link.download = `generated-${meta.id}.png`;
                          link.click();
                        }}
                        className="px-4 py-2 bg-[#3a3a3d] hover:bg-[#4a4a4d] rounded text-white text-sm transition-colors"
                      >
                        💾 Save
                      </button>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(generatedImage!);
                          alert('이미지 URL이 클립보드에 복사되었습니다.');
                        }}
                        className="px-4 py-2 bg-[#3a3a3d] hover:bg-[#4a4a4d] rounded text-white text-sm transition-colors"
                      >
                        📋 Copy URL
                      </button>
                    </div>
                  )}

                  {/* 메타데이터 */}
                  {meta && (
                    <div className="bg-[#1b1b1f] rounded-lg p-4 border border-[#3a3a3d] text-sm space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-gray-400">Size:</span>
                          <p className="text-white font-medium">{meta.width} × {meta.height}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Steps:</span>
                          <p className="text-white font-medium">{meta.steps}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">CFG Scale:</span>
                          <p className="text-white font-medium">{meta.guidance_scale}</p>
                        </div>
                        {meta.strength !== undefined && (
                          <div>
                            <span className="text-gray-400">Strength:</span>
                            <p className="text-white font-medium">{meta.strength}</p>
                          </div>
                        )}
                        {meta.seed !== undefined && (
                          <div>
                            <span className="text-gray-400">Seed:</span>
                            <p className="text-white font-medium">{meta.seed}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-[#1b1b1f] rounded-lg border border-[#3a3a3d] aspect-square flex items-center justify-center text-gray-500">
                  {isGenerating ? (
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                      <p>Generating image...</p>
                    </div>
                  ) : (
                    <p>Generated image will appear here</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
