"use client";

import { useState } from "react";

interface FileItem {
  file: File;
  preview: string;
  id: string;
}

export default function PortfolioPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [segmentResult, setSegmentResult] = useState<{original: string, segment: string} | null>(null);
  const [isSegmenting, setIsSegmenting] = useState(false);
  const [poseResult, setPoseResult] = useState<string | null>(null);
  const [isPosing, setIsPosing] = useState(false);

  const handlePortfolioSubmit = async () => {
    if (files.length === 0) {
      alert('업로드할 파일이 없습니다.');
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      
      // 모든 파일을 FormData에 추가 (FastAPI는 'files' 키로 여러 파일을 받음)
      files.forEach((fileItem) => {
        formData.append('files', fileItem.file);
      });

      // 파이썬 서버로 파일 전송
      // TODO: 실제 API 엔드포인트로 변경 필요
      const response = await fetch('http://localhost:8000/api/portfolio/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`서버 오류: ${response.status}`);
      }

      const result = await response.json();
      console.log('업로드 성공:', result);
      
      // 서버 응답 메시지 표시
      if (result.message) {
        alert(result.message);
      } else {
        alert('포트폴리오가 성공적으로 추가되었습니다!');
      }
      
      // 교체된 파일 정보가 있으면 추가 정보 표시
      if (result.replaced_files && result.replaced_files.length > 0) {
        const replacedCount = result.replaced_files.length;
        const replacedNames = result.replaced_files.map((f: any) => f.filename).join(', ');
        console.log(`${replacedCount}개의 중복 이미지가 기존 파일과 교체되었습니다:`, replacedNames);
      }
      
      // 업로드 성공 후 파일 리스트 초기화
      files.forEach(fileItem => {
        URL.revokeObjectURL(fileItem.preview);
      });
      setFiles([]);
    } catch (error) {
      console.error('업로드 실패:', error);
      alert(`포트폴리오 업로드 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer) {
      // files나 items가 있으면 드래그 상태 활성화
      const hasFiles = (e.dataTransfer.files && e.dataTransfer.files.length > 0) ||
                       (e.dataTransfer.items && e.dataTransfer.items.length > 0);
      if (hasFiles) {
        setIsDragging(true);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'copy';
      // files나 items가 있으면 드래그 상태 활성화
      const hasFiles = (e.dataTransfer.files && e.dataTransfer.files.length > 0) ||
                       (e.dataTransfer.items && e.dataTransfer.items.length > 0);
      if (hasFiles) {
        setIsDragging(true);
      }
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (!e.dataTransfer) {
      console.error('dataTransfer가 없습니다');
      return;
    }

    console.log('Drop 이벤트 발생');
    console.log('dataTransfer.files.length:', e.dataTransfer.files?.length);
    console.log('dataTransfer.items.length:', e.dataTransfer.items?.length);
    console.log('dataTransfer.types:', Array.from(e.dataTransfer.types || []));

    let droppedFiles: File[] = [];

    // 방법 1: dataTransfer.files 직접 확인
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      droppedFiles = Array.from(e.dataTransfer.files);
      console.log('방법 1: files에서 가져옴, 개수:', droppedFiles.length);
    }
    // 방법 2: dataTransfer.items에서 파일 가져오기
    else if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      console.log('items 상세 정보:');
      for (let i = 0; i < e.dataTransfer.items.length; i++) {
        const item = e.dataTransfer.items[i];
        console.log(`Item ${i}:`, {
          kind: item.kind,
          type: item.type
        });
        
        if (item.kind === 'file') {
          const file = item.getAsFile();
          if (file) {
            console.log(`  -> 파일 발견: ${file.name}, 타입: ${file.type}`);
            droppedFiles.push(file);
          } else {
            console.log(`  -> getAsFile()이 null 반환`);
          }
        }
      }
      console.log('방법 2: items에서 가져옴, 개수:', droppedFiles.length);
    }

    if (droppedFiles.length > 0) {
      const newFiles: FileItem[] = droppedFiles
        .filter(file => {
          const isImage = file.type.startsWith('image/');
          if (!isImage) {
            console.log(`이미지가 아닌 파일 제외: ${file.name}, 타입: ${file.type}`);
          }
          return isImage;
        })
        .map(file => {
          const preview = URL.createObjectURL(file);
          console.log(`이미지 파일 처리: ${file.name}`);
          return {
            file,
            preview,
            id: `${file.name}-${file.lastModified}-${Date.now()}`
          };
        });
      
      console.log('최종 이미지 파일 개수:', newFiles.length);
      if (newFiles.length > 0) {
        setFiles(prev => [...prev, ...newFiles]);
      } else {
        console.warn('이미지 파일이 없습니다. 모든 파일 타입:', droppedFiles.map(f => f.type));
      }
    } else {
      console.error('파일이 감지되지 않음');
      console.log('files:', e.dataTransfer.files);
      console.log('items:', e.dataTransfer.items);
      alert('파일이 감지되지 않았습니다.\n\n파일 탐색기(Windows 탐색기)에서 직접 이미지 파일을 드래그해주세요.\n\nVS Code나 다른 에디터에서 드래그하면 작동하지 않을 수 있습니다.');
    }
  };

  return (
    <div 
      className="flex flex-col items-center min-h-screen bg-black py-8"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className={`border-2 border-dashed rounded-lg p-16 transition-all mb-8 ${
        isDragging 
          ? 'border-white bg-white/10 scale-105' 
          : 'border-gray-600 hover:border-gray-400'
      }`}>
        <p className={`text-xl font-semibold transition-colors ${
          isDragging ? 'text-white' : 'text-gray-400'
        }`}>
          파일을 여기로 드래그하세요
        </p>
      </div>

      {/* YOLO 포즈 검출 결과 표시 */}
      <div className="w-full max-w-6xl px-4 mb-8">
        <h2 className="text-2xl font-bold text-white mb-4 text-center">YOLO 포즈 검출 결과</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 text-center">포즈 검출 결과</h3>
            {poseResult ? (
              <img 
                src={poseResult} 
                alt="YOLO 포즈 검출 결과"
                className="w-full h-auto rounded border border-gray-600"
              />
            ) : (
              <img 
                src="/family_pose.jpg" 
                alt="YOLO 포즈 검출 결과"
                className="w-full h-auto rounded border border-gray-600"
              />
            )}
          </div>
        </div>
        
        {/* YOLO 포즈 검출 버튼 */}
        <div className="flex justify-center mt-6">
          <button
            onClick={async () => {
              try {
                setIsPosing(true);
                // 먼저 서버가 실행 중인지 확인
                try {
                  const healthCheck = await fetch('http://localhost:8000/', {
                    method: 'GET',
                  });
                  if (!healthCheck.ok) {
                    throw new Error('Python 서버가 실행되지 않았습니다.');
                  }
                } catch (healthError) {
                  alert('Python 서버에 연결할 수 없습니다.\n\n서버를 실행해주세요:\ncd cv.devictoria.shop/app/yolo\npython main.py');
                  return;
                }
                
                // family.jpg 파일을 서버로 업로드
                console.log('이미지 파일 로드 시작...');
                const response = await fetch('/family.jpg');
                if (!response.ok) {
                  throw new Error('family.jpg 파일을 불러올 수 없습니다.');
                }
                const blob = await response.blob();
                console.log('이미지 파일 로드 완료, 크기:', blob.size, 'bytes');
                
                const file = new File([blob], 'family.jpg', { type: 'image/jpeg' });
                console.log('File 객체 생성 완료:', file.name, file.size, 'bytes', file.type);
                
                const formData = new FormData();
                formData.append('file', file);
                console.log('FormData 생성 완료, Python 서버로 업로드 시작...');
                
                // Python 서버로 YOLO 포즈 검출 요청
                console.log('YOLO 포즈 검출 요청 시작: http://localhost:8000/api/yolo/pose');
                const poseResponse = await fetch('http://localhost:8000/api/yolo/pose', {
                  method: 'POST',
                  body: formData,
                });
                console.log('서버 응답 받음, 상태:', poseResponse.status, poseResponse.statusText);
                
                if (!poseResponse.ok) {
                  const errorText = await poseResponse.text();
                  console.error('서버 응답 오류:', errorText);
                  throw new Error(`서버 오류: ${poseResponse.status} - ${errorText}`);
                }
                
                const result = await poseResponse.json();
                
                if (result.status === 'success' && result.images) {
                  const poseImageBase64 = `data:image/jpeg;base64,${result.images.pose.base64}`;
                  setPoseResult(poseImageBase64);
                  
                  // 포즈 검출 결과 이미지 다운로드
                  const images = [
                    { base64: result.images.pose.base64, name: 'family_pose.jpg' }
                  ];
                  
                  images.forEach((img, index) => {
                    setTimeout(() => {
                      // base64를 blob으로 변환
                      const byteCharacters = atob(img.base64);
                      const byteNumbers = new Array(byteCharacters.length);
                      for (let i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                      }
                      const byteArray = new Uint8Array(byteNumbers);
                      const blob = new Blob([byteArray], { type: 'image/jpeg' });
                      
                      // 다운로드
                      const url = URL.createObjectURL(blob);
                      const link = document.createElement('a');
                      link.href = url;
                      link.download = img.name;
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                      URL.revokeObjectURL(url);
                    }, index * 300); // 각 이미지 다운로드 간격
                  });
                  
                  alert('YOLO 포즈 검출 완료! 이미지 다운로드가 시작되었습니다.');
                } else {
                  alert('포즈 검출 처리에 실패했습니다.');
                }
              } catch (error) {
                console.error('포즈 검출 실패:', error);
                alert(`포즈 검출 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
              } finally {
                setIsPosing(false);
              }
            }}
            disabled={isPosing}
            className={`px-8 py-3 rounded-lg font-semibold transition-colors ${
              isPosing
                ? 'bg-gray-500 text-gray-300 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            {isPosing ? '포즈 검출 중...' : 'YOLO 포즈 검출'}
          </button>
        </div>
      </div>

      {/* YOLO 세그먼테이션 결과 표시 */}
      <div className="w-full max-w-6xl px-4 mb-8">
        <h2 className="text-2xl font-bold text-white mb-4 text-center">YOLO 세그먼테이션 결과</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 text-center">세그먼트 결과</h3>
            {segmentResult ? (
              <img 
                src={segmentResult.segment} 
                alt="YOLO 세그먼테이션 결과"
                className="w-full h-auto rounded border border-gray-600"
              />
            ) : (
              <img 
                src="/family_segment.jpg" 
                alt="YOLO 세그먼테이션 결과"
                className="w-full h-auto rounded border border-gray-600"
              />
            )}
          </div>
        </div>
        
        {/* YOLO 세그먼테이션 버튼 */}
        <div className="flex justify-center mt-6">
          <button
            onClick={async () => {
              try {
                setIsSegmenting(true);
                // 먼저 서버가 실행 중인지 확인
                try {
                  const healthCheck = await fetch('http://localhost:8000/', {
                    method: 'GET',
                  });
                  if (!healthCheck.ok) {
                    throw new Error('Python 서버가 실행되지 않았습니다.');
                  }
                } catch (healthError) {
                  alert('Python 서버에 연결할 수 없습니다.\n\n서버를 실행해주세요:\ncd cv.devictoria.shop/app/yolo\npython main.py');
                  return;
                }
                
                // family.jpg 파일을 서버로 업로드
                const response = await fetch('/family.jpg');
                if (!response.ok) {
                  throw new Error('family.jpg 파일을 불러올 수 없습니다.');
                }
                const blob = await response.blob();
                const file = new File([blob], 'family.jpg', { type: 'image/jpeg' });
                
                const formData = new FormData();
                formData.append('file', file);
                
                // Python 서버로 YOLO 세그먼테이션 요청
                console.log('YOLO 세그먼테이션 요청 시작...');
                const segmentResponse = await fetch('http://localhost:8000/api/yolo/segment', {
                  method: 'POST',
                  body: formData,
                });
                
                if (!segmentResponse.ok) {
                  const errorText = await segmentResponse.text();
                  console.error('서버 응답 오류:', errorText);
                  throw new Error(`서버 오류: ${segmentResponse.status} - ${errorText}`);
                }
                
                const result = await segmentResponse.json();
                
                if (result.status === 'success' && result.images) {
                  setSegmentResult({
                    original: `data:image/jpeg;base64,${result.images.original.base64}`,
                    segment: `data:image/jpeg;base64,${result.images.segment.base64}`
                  });
                  
                  // 세그먼테이션 결과 이미지 다운로드 (세그먼트 결과만)
                  const images = [
                    { base64: result.images.segment.base64, name: 'family_segment.jpg' }
                  ];
                  
                  images.forEach((img, index) => {
                    setTimeout(() => {
                      // base64를 blob으로 변환
                      const byteCharacters = atob(img.base64);
                      const byteNumbers = new Array(byteCharacters.length);
                      for (let i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                      }
                      const byteArray = new Uint8Array(byteNumbers);
                      const blob = new Blob([byteArray], { type: 'image/jpeg' });
                      
                      // 다운로드
                      const url = URL.createObjectURL(blob);
                      const link = document.createElement('a');
                      link.href = url;
                      link.download = img.name;
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                      URL.revokeObjectURL(url);
                    }, index * 300); // 각 이미지 다운로드 간격
                  });
                  
                  alert('YOLO 세그먼테이션 완료! 이미지 다운로드가 시작되었습니다.');
                } else {
                  alert('세그먼테이션 처리에 실패했습니다.');
                }
              } catch (error) {
                console.error('세그먼테이션 실패:', error);
                alert(`세그먼테이션 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
              } finally {
                setIsSegmenting(false);
              }
            }}
            disabled={isSegmenting}
            className={`px-8 py-3 rounded-lg font-semibold transition-colors ${
              isSegmenting
                ? 'bg-gray-500 text-gray-300 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {isSegmenting ? '세그먼테이션 중...' : 'YOLO 세그먼테이션'}
          </button>
        </div>
      </div>

      {/* yolo-s3 폴더의 이미지 표시 */}
      <div className="w-full max-w-6xl px-4 mb-8">
        <h2 className="text-2xl font-bold text-white mb-4 text-center">YOLO 디텍션 결과</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 text-center">원본 이미지</h3>
            <img 
              src="/family.jpg" 
              alt="원본 이미지"
              className="w-full h-auto rounded border border-gray-600"
            />
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 text-center">얼굴 검출</h3>
            <img 
              src="/family_detect.jpg" 
              alt="얼굴 검출 이미지"
              className="w-full h-auto rounded border border-gray-600"
            />
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 text-center">그레이스케일 얼굴</h3>
            <img 
              src="/family_gray_face.jpg" 
              alt="그레이스케일 얼굴 이미지"
              className="w-full h-auto rounded border border-gray-600"
            />
          </div>
        </div>
        
        {/* 다운로드 버튼 */}
        <div className="flex justify-center gap-4 mt-6">
          <button
            onClick={async () => {
              try {
                // 먼저 서버가 실행 중인지 확인
                try {
                  const healthCheck = await fetch('http://localhost:8000/', {
                    method: 'GET',
                  });
                  if (!healthCheck.ok) {
                    throw new Error('Python 서버가 실행되지 않았습니다.');
                  }
                } catch (healthError) {
                  alert('Python 서버에 연결할 수 없습니다.\n\n서버를 실행해주세요:\ncd cv.devictoria.shop\npython main.py');
                  return;
                }
                
                // family.jpg 파일을 서버로 업로드
                const response = await fetch('/family.jpg');
                if (!response.ok) {
                  throw new Error('family.jpg 파일을 불러올 수 없습니다.');
                }
                const blob = await response.blob();
                const file = new File([blob], 'family.jpg', { type: 'image/jpeg' });
                
                const formData = new FormData();
                formData.append('file', file);
                
                // Python 서버로 YOLO 디텍션 요청
                console.log('YOLO 디텍션 요청 시작...');
                const detectResponse = await fetch('http://localhost:8000/api/yolo/detect', {
                  method: 'POST',
                  body: formData,
                });
                
                console.log('서버 응답 상태:', detectResponse.status, detectResponse.statusText);
                console.log('서버 응답 URL:', detectResponse.url);
                
                if (!detectResponse.ok) {
                  const errorText = await detectResponse.text();
                  console.error('서버 응답 오류:', errorText);
                  
                  // 404 에러인 경우 더 자세한 정보 제공
                  if (detectResponse.status === 404) {
                    throw new Error(
                      `엔드포인트를 찾을 수 없습니다 (404).\n\n` +
                      `가능한 원인:\n` +
                      `1. 서버가 실행되지 않았습니다\n` +
                      `2. 엔드포인트 경로가 잘못되었습니다\n` +
                      `3. 서버가 재시작되지 않았습니다\n\n` +
                      `해결 방법:\n` +
                      `1. 서버를 실행하세요: cd cv.devictoria.shop && python main.py\n` +
                      `2. 서버가 실행 중이면 재시작하세요\n` +
                      `3. 브라우저에서 http://localhost:8000/docs 를 열어 엔드포인트를 확인하세요\n\n` +
                      `서버 응답: ${errorText}`
                    );
                  }
                  
                  throw new Error(`서버 오류: ${detectResponse.status} - ${errorText}`);
                }
                
                const result = await detectResponse.json();
                
                if (result.status === 'success' && result.images) {
                  // base64 이미지를 다운로드
                  const images = [
                    { base64: result.images.original.base64, name: 'family_original.jpg' },
                    { base64: result.images.detect.base64, name: 'family_detect.jpg' },
                    { base64: result.images.gray_face.base64, name: 'family_gray_face.jpg' }
                  ];
                  
                  images.forEach((img, index) => {
                    setTimeout(() => {
                      // base64를 blob으로 변환
                      const byteCharacters = atob(img.base64);
                      const byteNumbers = new Array(byteCharacters.length);
                      for (let i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                      }
                      const byteArray = new Uint8Array(byteNumbers);
                      const blob = new Blob([byteArray], { type: 'image/jpeg' });
                      
                      // 다운로드
                      const url = URL.createObjectURL(blob);
                      const link = document.createElement('a');
                      link.href = url;
                      link.download = img.name;
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                      URL.revokeObjectURL(url);
                    }, index * 300); // 각 이미지 다운로드 간격
                  });
                  
                  alert('이미지 다운로드가 시작되었습니다!');
                } else {
                  alert('이미지 처리에 실패했습니다.');
                }
              } catch (error) {
                console.error('다운로드 실패:', error);
                alert(`이미지 다운로드 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
              }
            }}
            className="px-8 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            이미지 다운로드
          </button>
        </div>
      </div>


      {files.length > 0 && (
        <div className="w-full max-w-4xl px-4">
          <div className="space-y-4 mb-6">
            {files.map((fileItem) => (
              <div 
                key={fileItem.id}
                className="bg-gray-900 border border-gray-700 rounded-lg p-4 flex gap-4"
              >
                <div className="flex-shrink-0">
                  <img 
                    src={fileItem.preview} 
                    alt={fileItem.file.name}
                    className="w-32 h-32 object-cover rounded border border-gray-600"
                  />
                </div>
                <div className="flex-1 text-white">
                  <h3 className="font-semibold text-lg mb-2">{fileItem.file.name}</h3>
                  <div className="space-y-1 text-sm text-gray-300">
                    <p>파일 크기: {(fileItem.file.size / 1024).toFixed(2)} KB ({fileItem.file.size} bytes)</p>
                    <p>파일 타입: {fileItem.file.type || '알 수 없음'}</p>
                    <p>마지막 수정: {new Date(fileItem.file.lastModified).toLocaleString('ko-KR')}</p>
              </div>
                </div>
              </div>
            ))}
            </div>
          <div className="flex justify-center">
          <button
              onClick={handlePortfolioSubmit}
              disabled={isUploading}
              className={`px-8 py-3 rounded-lg font-semibold transition-colors ${
                isUploading 
                  ? 'bg-gray-500 text-gray-300 cursor-not-allowed' 
                  : 'bg-white text-black hover:bg-gray-200'
              }`}
            >
              {isUploading ? '업로드 중...' : '포트폴리오 추가하기'}
          </button>
          </div>
        </div>
      )}
    </div>
  );
}

