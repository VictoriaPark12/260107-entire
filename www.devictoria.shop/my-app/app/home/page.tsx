"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // OAuth 콜백 처리
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");
    const refreshToken = urlParams.get("refreshToken");
    const success = urlParams.get("success");
    const error = urlParams.get("error");

    if (success === "true" && token) {
      // 로그인 성공
      console.log("로그인 성공! 토큰 저장");
      localStorage.setItem("accessToken", token);
      if (refreshToken) {
        localStorage.setItem("refreshToken", refreshToken);
      }

      // URL 정리 (토큰 제거)
      window.history.replaceState({}, document.title, "/home");
      setIsLoggedIn(true);
    } else if (error) {
      // 로그인 실패
      console.error("로그인 실패:", error);
      alert("로그인 실패: " + decodeURIComponent(error));
      window.history.replaceState({}, document.title, "/");
      router.push("/");
    } else {
      // 일반 접근 - 토큰 확인
      const accessToken = localStorage.getItem("accessToken");
      if (!accessToken) {
        router.push("/");
      } else {
        setIsLoggedIn(true);
      }
    }
  }, [searchParams, router]);

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    router.push("/");
  };

  if (!isLoggedIn) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-gray-900 flex flex-col items-center justify-start pt-20 px-4">
      {/* Google 스타일 로고 */}
      <div className="mb-12">
        <h1 className="text-6xl font-normal text-purple-200 tracking-wide">
          Google
        </h1>
      </div>

      {/* 검색 바 */}
      <div className="w-full max-w-2xl mb-12">
        <div className="bg-white rounded-full shadow-2xl px-6 py-4 flex items-center justify-between hover:shadow-3xl transition-shadow">
          {/* 왼쪽: 검색 아이콘 + 입력 필드 */}
          <div className="flex items-center gap-4 flex-1">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="text-gray-500"
            >
              <path
                d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <input
              type="text"
              placeholder="Google 검색 또는 URL 입력"
              className="flex-1 outline-none text-gray-700 text-base bg-transparent"
            />
          </div>

          {/* 오른쪽: 마이크, 카메라, AI 모드 아이콘 */}
          <div className="flex items-center gap-4">
            <button className="text-gray-500 hover:text-gray-700 transition-colors">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M12 2C10.8954 2 10 2.89543 10 4V12C10 13.1046 10.8954 14 12 14C13.1046 14 14 13.1046 14 12V4C14 2.89543 13.1046 2 12 2Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  fill="none"
                />
                <path
                  d="M19 12V13C19 16.866 15.866 20 12 20C8.13401 20 5 16.866 5 13V12"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
                <path
                  d="M12 20V22M8 22H16"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </button>
            <button className="text-gray-500 hover:text-gray-700 transition-colors">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M23 19C23 19.5304 22.7893 20.0391 22.4142 20.4142C22.0391 20.7893 21.5304 21 21 21H3C2.46957 21 1.96086 20.7893 1.58579 20.4142C1.21071 20.0391 1 19.5304 1 19V8C1 7.46957 1.21071 6.96086 1.58579 6.58579C1.96086 6.21071 2.46957 6 3 6H7L9 4H15L17 6H21C21.5304 6 22.0391 6.21071 22.4142 6.58579C22.7893 6.96086 23 7.46957 23 8V19Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx="12" cy="13" r="4" stroke="currentColor" strokeWidth="2" />
              </svg>
            </button>
            <button className="text-gray-500 hover:text-gray-700 transition-colors flex items-center gap-1 px-3 py-1 rounded-full hover:bg-gray-100">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span className="text-sm font-medium">AI 모드</span>
            </button>
          </div>
        </div>
      </div>

      {/* 바로가기 아이콘들 */}
      <div className="w-full max-w-4xl grid grid-cols-4 md:grid-cols-9 gap-6 mb-8">
        {/* 바로가기 1 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl font-bold">G</span>
          </div>
          <span className="text-purple-200 text-xs text-center">GitHub</span>
        </div>

        {/* 바로가기 2 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl">C</span>
          </div>
          <span className="text-purple-200 text-xs text-center">ChatGPT</span>
        </div>

        {/* 바로가기 3 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl font-bold">X</span>
          </div>
          <span className="text-purple-200 text-xs text-center">Home / X</span>
        </div>

        {/* 바로가기 4 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl">S</span>
          </div>
          <span className="text-purple-200 text-xs text-center">Slack</span>
        </div>

        {/* 바로가기 5 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl">N</span>
          </div>
          <span className="text-purple-200 text-xs text-center">Next.js</span>
        </div>

        {/* 바로가기 6 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl font-bold">X</span>
          </div>
          <span className="text-purple-200 text-xs text-center">X 로그인</span>
        </div>

        {/* 바로가기 7 - 타이타닉 */}
        <div 
          className="flex flex-col items-center cursor-pointer group"
          onClick={() => router.push("/passengers")}
        >
          <div className="w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl font-bold">T</span>
          </div>
          <span className="text-purple-200 text-xs text-center">타이타닉</span>
        </div>

        {/* 바로가기 8 - 웹 스토어 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center mb-2 group-hover:bg-gray-600 transition-colors">
            <span className="text-white text-xl">W</span>
          </div>
          <span className="text-purple-200 text-xs text-center">웹 스토어</span>
        </div>

        {/* 바로가기 추가 버튼 */}
        <div className="flex flex-col items-center cursor-pointer group">
          <div className="w-14 h-14 rounded-full bg-purple-600 flex items-center justify-center mb-2 group-hover:bg-purple-500 transition-colors">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="text-white"
            >
              <path
                d="M12 5V19M5 12H19"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <span className="text-purple-200 text-xs text-center">바로가기 추가</span>
        </div>
      </div>

      {/* 하단 메뉴 */}
      <div className="mt-auto pb-8 flex gap-4">
        <button
          onClick={() => router.push("/passengers")}
          className="px-4 py-2 bg-gray-800 text-purple-200 rounded-lg hover:bg-gray-700 transition-colors text-sm"
        >
          승객명단
        </button>
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-gray-800 text-purple-200 rounded-lg hover:bg-gray-700 transition-colors text-sm"
        >
          로그아웃
        </button>
      </div>
    </div>
  );
}
