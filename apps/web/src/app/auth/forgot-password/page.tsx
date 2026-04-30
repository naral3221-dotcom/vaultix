import { AuthShell } from "../_components/auth-shell";
import { ForgotPasswordForm } from "../_components/reset-password-form";

export default function ForgotPasswordPage() {
  return (
    <AuthShell
      title="비밀번호 재설정"
      description="가입한 이메일로 비밀번호 재설정 안내를 보냅니다."
      submitLabel="재설정 메일 받기"
      form={<ForgotPasswordForm />}
      footer={
        <p>
          비밀번호가 기억났나요? <a href="/auth/signin">로그인</a>
        </p>
      }
    />
  );
}
