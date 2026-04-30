"use client";

import { FormEvent, useState } from "react";

type SigninState = {
  message: string | null;
};

export function SigninForm() {
  const [state, setState] = useState<SigninState>({ message: null });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setState({ message: null });

    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: String(form.get("email") ?? ""),
          password: String(form.get("password") ?? ""),
        }),
      });
      const payload = await response.json();
      if (response.ok) {
        window.location.assign("/explore");
        return;
      }
      setState({ message: payload.detail ?? "로그인을 처리하지 못했습니다." });
    } catch {
      setState({ message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요." });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label htmlFor="signin-email">이메일</label>
      <input id="signin-email" name="email" type="email" autoComplete="email" required />

      <label htmlFor="signin-password">비밀번호</label>
      <input id="signin-password" name="password" type="password" autoComplete="current-password" required />

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "확인 중" : "로그인"}
      </button>

      {state.message ? (
        <p className="auth-message error" role="status">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
