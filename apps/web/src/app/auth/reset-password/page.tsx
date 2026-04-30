import { AuthShell } from "../_components/auth-shell";
import { ResetPasswordForm } from "../_components/reset-password-form";

type ResetPasswordPageProps = {
  searchParams?: {
    token?: string;
  };
};

export default function ResetPasswordPage({ searchParams }: ResetPasswordPageProps) {
  return (
    <AuthShell
      title="새 비밀번호 설정"
      description="재설정 토큰을 확인하고 새 비밀번호를 저장합니다."
      submitLabel="비밀번호 변경"
      form={<ResetPasswordForm initialToken={searchParams?.token ?? ""} />}
      footer={
        <p>
          변경 후 <a href="/auth/signin">로그인</a>으로 이동해 주세요.
        </p>
      }
    />
  );
}
