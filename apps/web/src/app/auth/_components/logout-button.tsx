"use client";

import { useState } from "react";

export function LogoutButton() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleLogout() {
    setIsSubmitting(true);
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      window.location.assign("/");
    }
  }

  return (
    <button className="auth-secondary-button" disabled={isSubmitting} onClick={handleLogout} type="button">
      {isSubmitting ? "로그아웃 중" : "로그아웃"}
    </button>
  );
}
