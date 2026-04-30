"use client";

import { FormEvent, useState } from "react";

type ResetState = {
  message: string | null;
  kind: "idle" | "success" | "error";
};

export function ForgotPasswordForm() {
  const [state, setState] = useState<ResetState>({ message: null, kind: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setState({ message: null, kind: "idle" });

    try {
      const response = await fetch("/api/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: String(form.get("email") ?? "") }),
      });
      const payload = await response.json();
      if (response.ok) {
        setState({ message: "비밀번호 재설정 안내를 확인해 주세요.", kind: "success" });
        return;
      }
      setState({ message: payload.detail ?? "재설정 요청을 처리하지 못했습니다.", kind: "error" });
    } catch {
      setState({ message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.", kind: "error" });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label htmlFor="forgot-email">이메일</label>
      <input id="forgot-email" name="email" type="email" autoComplete="email" required />
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "요청 중" : "재설정 메일 받기"}
      </button>
      {state.message ? (
        <p className={`auth-message ${state.kind}`} role="status">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}

export function ResetPasswordForm({ initialToken = "" }: { initialToken?: string }) {
  const [state, setState] = useState<ResetState>({ message: null, kind: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setState({ message: null, kind: "idle" });

    try {
      const response = await fetch("/api/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: String(form.get("token") ?? ""),
          password: String(form.get("password") ?? ""),
        }),
      });
      const payload = await response.json();
      if (response.ok) {
        setState({ message: "비밀번호가 변경되었습니다.", kind: "success" });
        return;
      }
      setState({ message: payload.detail ?? "비밀번호를 변경하지 못했습니다.", kind: "error" });
    } catch {
      setState({ message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.", kind: "error" });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label htmlFor="reset-token">재설정 토큰</label>
      <input id="reset-token" name="token" type="text" defaultValue={initialToken} required />
      <label htmlFor="reset-password">새 비밀번호</label>
      <input id="reset-password" name="password" type="password" autoComplete="new-password" required />
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "변경 중" : "비밀번호 변경"}
      </button>
      {state.message ? (
        <p className={`auth-message ${state.kind}`} role="status">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
