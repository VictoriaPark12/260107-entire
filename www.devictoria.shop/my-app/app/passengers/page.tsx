"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Passenger {
  PassengerId: string;
  Survived: string;
  Pclass: string;
  Name: string;
  Sex: string;
  Age: string;
  Fare: string;
  Embarked: string;
}

export default function PassengersPage() {
  const router = useRouter();
  const [passengers, setPassengers] = useState<Passenger[]>([]);
  const [loading, setLoading] = useState(false);
  const [showPassengers, setShowPassengers] = useState(false);

  // 로그인 확인
  useEffect(() => {
    const accessToken = localStorage.getItem("accessToken");
    if (!accessToken) {
      // 로그인되지 않은 경우 홈으로 리다이렉트
      router.push("/");
    }
  }, [router]);

  const fetchTitanicPassengers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8080/api/titanic/passengers/top10", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("서버 응답 오류");
      }

      const data = await response.json();
      if (data.passengers) {
        setPassengers(data.passengers);
        setShowPassengers(true);
      }
    } catch (error) {
      console.error("타이타닉 승객 정보 조회 오류:", error);
      alert("타이타닉 승객 정보를 가져오는 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleBackToDashboard = () => {
    router.push("/home");
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        {!showPassengers ? (
          <>
            {/* 질문 텍스트 */}
            <div className="text-center mb-8">
              <h1 className="text-white text-2xl font-medium">
                무슨 작업을 하고 계세요?
              </h1>
            </div>

            {/* 입력 필드 */}
            <div className="relative mb-8">
              <div className="bg-gray-800 rounded-2xl px-6 py-4 flex items-center justify-between shadow-lg border border-gray-700">
                {/* 왼쪽: 플러스 아이콘 + 텍스트 */}
                <div className="flex items-center gap-3 flex-1">
                  <button className="text-white hover:text-gray-300 transition-colors">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 20 20"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M10 4V16M4 10H16"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                      />
                    </svg>
                  </button>
                  <span className="text-gray-400 text-sm">무엇이든 물어보세요</span>
                </div>

                {/* 오른쪽: 마이크 + 사운드 아이콘 */}
                <div className="flex items-center gap-4">
                  <button className="text-white hover:text-gray-300 transition-colors">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 20 20"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M10 2C8.89543 2 8 2.89543 8 4V10C8 11.1046 8.89543 12 10 12C11.1046 12 12 11.1046 12 10V4C12 2.89543 11.1046 2 10 2Z"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        fill="none"
                      />
                      <path
                        d="M5 10V11C5 13.7614 7.23858 16 10 16C12.7614 16 15 13.7614 15 11V10"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                      />
                      <path
                        d="M10 16V18M7 18H13"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                      />
                    </svg>
                  </button>
                  <button className="text-white hover:text-gray-300 transition-colors">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 20 20"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <rect
                        x="3"
                        y="8"
                        width="2"
                        height="4"
                        rx="1"
                        fill="currentColor"
                      />
                      <rect
                        x="7"
                        y="6"
                        width="2"
                        height="8"
                        rx="1"
                        fill="currentColor"
                      />
                      <rect
                        x="11"
                        y="4"
                        width="2"
                        height="12"
                        rx="1"
                        fill="currentColor"
                      />
                      <rect
                        x="15"
                        y="7"
                        width="2"
                        height="6"
                        rx="1"
                        fill="currentColor"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* 승객명단 확인 버튼 */}
            <div className="text-center">
              <button
                onClick={fetchTitanicPassengers}
                disabled={loading}
                className="bg-blue-600 text-white px-8 py-4 rounded-md font-medium text-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? "로딩 중..." : "승객명단 확인하기"}
              </button>
            </div>

            {/* 추가 메뉴 버튼들 */}
            <div className="mt-8 flex justify-center gap-4">
              <button
                onClick={handleBackToDashboard}
                className="px-6 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm border border-gray-700"
              >
                대시보드로 돌아가기
              </button>
            </div>
          </>
        ) : (
          <div className="bg-gray-800 rounded-lg shadow-xl p-8 border border-gray-700">
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-2xl font-semibold text-white">
                타이타닉 상위 10명 승객 정보
              </h2>
              <button
                onClick={() => {
                  setShowPassengers(false);
                  setPassengers([]);
                }}
                className="px-4 py-2 bg-gray-700 text-white rounded-md font-medium hover:bg-gray-600 transition-colors"
              >
                다시 확인하기
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      이름
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      생존
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      등급
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      성별
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      나이
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      요금
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      탑승지
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {passengers.map((passenger: Passenger, index: number) => (
                    <tr key={index} className="hover:bg-gray-750">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                        {passenger.PassengerId}
                      </td>
                      <td className="px-4 py-3 text-sm text-white">
                        {passenger.Name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            passenger.Survived === "1"
                              ? "bg-green-800 text-green-200"
                              : "bg-red-800 text-red-200"
                          }`}
                        >
                          {passenger.Survived === "1" ? "생존" : "사망"}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                        {passenger.Pclass}등급
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                        {passenger.Sex === "male" ? "남성" : "여성"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                        {passenger.Age || "N/A"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                        {passenger.Fare || "N/A"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                        {passenger.Embarked || "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

