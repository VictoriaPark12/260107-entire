"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function OAuthPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // 소셜 로그인 시작
  const handleSocialLogin = async (provider: "kakao" | "google" | "naver") => {
    try {
      setIsLoading(true);
      // Gateway를 통해 OAuth 시작 API 호출
      // OAuth 컨트롤러는 Gateway 내부에 있으므로 /kakao/start, /google/start, /naver/start로 직접 접근
      const response = await fetch(`http://localhost:8080/${provider}/start`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`서버 응답 오류: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.authUrl) {
        // 인증 URL로 리다이렉트
        window.location.href = data.authUrl;
      } else {
        alert(`${provider} 로그인 시작에 실패했습니다.`);
      }
    } catch (error) {
      console.error(`${provider} 로그인 오류:`, error);
      alert(`${provider} 로그인 중 오류가 발생했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 이메일/비밀번호 로그인 (현재는 미구현)
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    alert("이메일/비밀번호 로그인은 현재 지원되지 않습니다. 소셜 로그인을 이용해주세요.");
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* 타이틀 */}
        <h1 className="text-3xl font-semibold text-gray-900 text-center mb-2">
          로그인
        </h1>
        <p className="text-gray-600 text-center mb-8">
          이메일과 비밀번호를 입력하세요.
        </p>

        {/* 이메일/비밀번호 로그인 폼 */}
        <form onSubmit={handleEmailLogin} className="mb-6">
          <div className="space-y-4 mb-6">
            {/* 이메일 입력 */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                이메일
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="이메일을 입력하세요"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                disabled={isLoading}
              />
            </div>

            {/* 비밀번호 입력 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  비밀번호
                </label>
                <a
                  href="#"
                  className="text-sm text-gray-500 hover:text-gray-700"
                  onClick={(e) => {
                    e.preventDefault();
                    alert("비밀번호 찾기 기능은 준비 중입니다.");
                  }}
                >
                  비밀번호를 잊었나요?
                </a>
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="비밀번호를 입력하세요"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                disabled={isLoading}
              />
            </div>
          </div>

          {/* 로그인 버튼 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gray-900 text-white font-medium py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            로그인
          </button>
        </form>

        {/* 계정 생성 링크 */}
        <div className="text-center mb-8">
          <span className="text-gray-600">계정이 있으신가요? </span>
          <a
            href="#"
            className="text-gray-900 font-medium hover:underline"
            onClick={(e) => {
              e.preventDefault();
              alert("계정 생성 기능은 준비 중입니다.");
            }}
          >
            계정생성
          </a>
        </div>

        {/* 소셜 로그인 버튼들 */}
        <div className="flex justify-center gap-4">
          {/* Google */}
          <button
            onClick={() => handleSocialLogin("google")}
            disabled={isLoading}
            className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center text-white font-bold text-xl hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Google로 로그인"
          >
            G
          </button>

          {/* Facebook */}
          <button
            onClick={() => {
              alert("Facebook 로그인은 현재 지원되지 않습니다.");
            }}
            disabled={isLoading}
            className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Facebook으로 로그인"
          >
            f
          </button>

          {/* Kakao */}
          <button
            onClick={() => handleSocialLogin("kakao")}
            disabled={isLoading}
            className="w-12 h-12 bg-yellow-400 rounded-lg flex items-center justify-center hover:bg-yellow-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="카카오로 로그인"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 3C6.477 3 2 6.153 2 10c0 2.37 1.638 4.456 4.075 5.74l-.95 3.52c-.09.333.244.595.528.42l4.347-2.86c.31.05.63.08.95.08 5.523 0 10-3.153 10-7s-4.477-7-10-7z"
                fill="#000000"
              />
            </svg>
          </button>

          {/* Naver */}
          <button
            onClick={() => handleSocialLogin("naver")}
            disabled={isLoading}
            className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center text-white font-bold text-xl hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="네이버로 로그인"
          >
            N
          </button>
        </div>

        {/* 로딩 상태 표시 */}
        {isLoading && (
          <div className="mt-6 text-center text-gray-500 text-sm">
            로그인 처리 중...
          </div>
        )}
      </div>
    </div>
  );
}

