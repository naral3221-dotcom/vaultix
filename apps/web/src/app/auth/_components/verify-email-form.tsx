"use client";

import { FormEvent, useState } from "react";

type VerifyEmailFormProps = {
  initialToken?: string;
};

type VerifyState = {
  message: string | null;
  kind: "idle" | "success" | "error";
};

export function VerifyEmailForm({ initialToken = "" }: VerifyEmailFormProps) {
  const [state, setState] = useState<VerifyState>({ message: null, kind: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setState({ message: null, kind: "idle" });

    try {
      const response = await fetch("/api/v1/auth/verify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: String(form.get("token") ?? "") }),
      });
      const payload = await response.json();
      if (response.ok) {
        setState({ message: "이메일 인증이 완료되었습니다.", kind: "success" });
        return;
      }
      setState({ message: payload.detail ?? "이메일 인증을 처리하지 못했습니다.", kind: "error" });
    } catch {
      setState({ message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.", kind: "error" });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label htmlFor="verify-token">인증 토큰</label>
      <input id="verify-token" name="token" type="text" defaultValue={initialToken} required />

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "확인 중" : "이메일 인증하기"}
      </button>

      {state.message ? (
        <p className={`auth-message ${state.kind}`} role="status">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
