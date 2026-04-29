import type { ReactNode } from "react";

type AuthShellProps = {
  title: string;
  description: string;
  submitLabel: string;
  footer: ReactNode;
  form?: ReactNode;
};

export function AuthShell({ title, description, submitLabel, footer, form }: AuthShellProps) {
  return (
    <main className="auth-page">
      <a className="simple-back" href="/">
        Vaultix
      </a>
      <section className="auth-panel">
        <p className="eyebrow">Account</p>
        <h1>{title}</h1>
        <p>{description}</p>

        {form ?? (
          <form className="auth-form">
            <label htmlFor={`${submitLabel}-email`}>이메일</label>
            <input id={`${submitLabel}-email`} name="email" type="email" autoComplete="email" />

            <label htmlFor={`${submitLabel}-password`}>비밀번호</label>
            <input
              id={`${submitLabel}-password`}
              name="password"
              type="password"
              autoComplete={submitLabel === "가입하기" ? "new-password" : "current-password"}
            />

            {submitLabel === "가입하기" ? (
              <>
                <label htmlFor="signup-display-name">이름</label>
                <input id="signup-display-name" name="display_name" type="text" autoComplete="name" />
              </>
            ) : null}

            <button type="button">{submitLabel}</button>
          </form>
        )}

        <div className="auth-footer">{footer}</div>
      </section>
    </main>
  );
}
