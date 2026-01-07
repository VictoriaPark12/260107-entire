"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * /dashboard는 더 이상 사용하지 않습니다.
 * /home으로 자동 리다이렉트합니다.
 */
export default function Dashboard() {
  const router = useRouter();

  useEffect(() => {
    // /dashboard 접근 시 /home으로 리다이렉트
    router.replace("/home");
  }, [router]);

  return null;
}

