"use client";

import Script from "next/script";
import { FormEvent, useEffect, useId, useState } from "react";

type SubmitState = {
  message: string | null;
  kind: "idle" | "success" | "error";
};

export function SignupForm() {
  const [state, setState] = useState<SubmitState>({ message: null, kind: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState("dev-token");
  const turnstileInputId = useId();
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "";

  useEffect(() => {
    if (!siteKey) {
      setTurnstileToken("dev-token");
      return;
    }

    window.vaultixOnTurnstileVerified = (token: string) => setTurnstileToken(token);
    window.vaultixOnTurnstileExpired = () => setTurnstileToken("");

    return () => {
      delete window.vaultixOnTurnstileVerified;
      delete window.vaultixOnTurnstileExpired;
    };
  }, [siteKey]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setState({ message: null, kind: "idle" });

    try {
      const response = await fetch("/api/v1/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: String(form.get("email") ?? ""),
          password: String(form.get("password") ?? ""),
          display_name: String(form.get("display_name") ?? ""),
          locale: "ko",
          turnstile_token: String(form.get("turnstile_token") ?? turnstileToken),
        }),
      });
      const payload = await response.json();
      if (response.ok) {
        setState({ message: "인증 메일을 확인해 주세요.", kind: "success" });
        return;
      }
      setState({ message: payload.detail ?? "회원가입을 처리하지 못했습니다.", kind: "error" });
    } catch {
      setState({ message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.", kind: "error" });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label htmlFor="signup-email">이메일</label>
      <input id="signup-email" name="email" type="email" autoComplete="email" required />

      <label htmlFor="signup-password">비밀번호</label>
      <input id="signup-password" name="password" type="password" autoComplete="new-password" required />

      <label htmlFor="signup-display-name">이름</label>
      <input id="signup-display-name" name="display_name" type="text" autoComplete="name" />

      <label className="sr-only" htmlFor={turnstileInputId}>
        보안 확인 토큰
      </label>
      <input
        id={turnstileInputId}
        name="turnstile_token"
        type="hidden"
        value={turnstileToken}
        onChange={(event) => setTurnstileToken(event.currentTarget.value)}
      />
      {siteKey ? (
        <>
          <Script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer />
          <div
            className="turnstile-box cf-turnstile"
            data-sitekey={siteKey}
            data-callback="vaultixOnTurnstileVerified"
            data-expired-callback="vaultixOnTurnstileExpired"
          />
        </>
      ) : null}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "처리 중" : "가입하기"}
      </button>

      {state.message ? (
        <p className={`auth-message ${state.kind}`} role="status">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}

declare global {
  interface Window {
    vaultixOnTurnstileVerified?: (token: string) => void;
    vaultixOnTurnstileExpired?: () => void;
  }
}
