import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AboutPage from "./about/page";
import ContactPage from "./contact/page";
import ExplorePage from "./explore/page";
import LicensePage from "./license/page";
import LogPage from "./log/page";
import NewsletterPage from "./newsletter/page";
import PrivacyPage from "./privacy/page";
import ReportPage from "./report/page";
import TodayPage from "./today/page";

describe("Phase 1 public page shells", () => {
  it.each([
    ["탐색", ExplorePage],
    ["오늘의 큐레이션", TodayPage],
    ["운영 일지", LogPage],
    ["뉴스레터", NewsletterPage],
    ["라이선스", LicensePage],
    ["개인정보처리방침", PrivacyPage],
    ["About Vaultix", AboutPage],
    ["Contact", ContactPage],
    ["신고하기", ReportPage],
  ])("renders %s page", (heading, Page) => {
    render(<Page />);

    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
  });
});
