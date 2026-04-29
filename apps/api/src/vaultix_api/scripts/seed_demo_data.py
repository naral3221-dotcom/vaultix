from sqlalchemy.orm import Session

from vaultix_api.db.session import get_sessionmaker
from vaultix_api.models.core import Asset, AssetTag, Category, Tag


def upsert_demo_data(session: Session) -> None:
    categories = [
        Category(id=101, slug="business", name_ko="비즈니스", sort_order=1),
        Category(id=102, slug="marketing", name_ko="마케팅", sort_order=2),
        Category(id=103, slug="report", name_ko="보고서", sort_order=3),
        Category(id=104, slug="sns", name_ko="SNS", sort_order=4),
    ]
    tags = [
        Tag(id=101, slug="meeting", name_ko="미팅", use_count=12),
        Tag(id=102, slug="presentation", name_ko="발표자료", use_count=10),
        Tag(id=103, slug="report", name_ko="보고서", use_count=8),
        Tag(id=104, slug="marketing", name_ko="마케팅", use_count=6),
    ]
    assets = [
        Asset(
            id=101,
            slug="business-meeting-illustration",
            asset_type="image",
            category_id=101,
            status="published",
            title_ko="비즈니스 미팅 일러스트",
            description_ko="보고서와 발표자료에 쓰기 좋은 회의 장면 이미지입니다.",
            alt_text_ko="회의실에서 사람들이 발표 자료를 보는 장면",
            thumbnail_path="/cdn/thumb/business-meeting.webp",
            preview_path="/cdn/preview/business-meeting.webp",
            file_path="/cdn/original/business-meeting.png",
            mime_type="image/png",
            checksum="demo-business-meeting",
            download_count=42,
        ),
        Asset(
            id=102,
            slug="quarterly-report-chart",
            asset_type="image",
            category_id=103,
            status="published",
            title_ko="분기 성과 그래프 이미지",
            description_ko="성과 보고서 첫 장에 쓰기 좋은 추상 그래프 이미지입니다.",
            alt_text_ko="상승 곡선과 막대 그래프가 조합된 업무용 이미지",
            thumbnail_path="/cdn/thumb/quarterly-report.webp",
            preview_path="/cdn/preview/quarterly-report.webp",
            file_path="/cdn/original/quarterly-report.png",
            mime_type="image/png",
            checksum="demo-quarterly-report",
            download_count=31,
        ),
        Asset(
            id=103,
            slug="sns-card-background",
            asset_type="image",
            category_id=104,
            status="published",
            title_ko="SNS 카드뉴스 배경",
            description_ko="텍스트를 얹기 좋은 여백 중심의 카드뉴스 배경입니다.",
            alt_text_ko="밝은 배경에 추상적인 도형이 배치된 카드뉴스 이미지",
            thumbnail_path="/cdn/thumb/sns-card.webp",
            preview_path="/cdn/preview/sns-card.webp",
            file_path="/cdn/original/sns-card.png",
            mime_type="image/png",
            checksum="demo-sns-card",
            download_count=24,
        ),
    ]

    for item in categories:
        session.merge(item)
    session.flush()
    for item in tags:
        session.merge(item)
    session.flush()
    for item in assets:
        session.merge(item)
    session.flush()
    for asset_id, tag_id in [(101, 101), (101, 102), (102, 103), (103, 104)]:
        session.merge(AssetTag(asset_id=asset_id, tag_id=tag_id))
    session.commit()


def main() -> None:
    maker = get_sessionmaker()
    with maker() as session:
        upsert_demo_data(session)
    print("Seeded Vaultix demo catalog data.")


if __name__ == "__main__":
    main()
