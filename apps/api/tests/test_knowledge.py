from bodyos_api.crypto import FieldCipher
from bodyos_api.knowledge import KnowledgeAccessDenied, KnowledgeService
from bodyos_api.models import KnowledgeChunk, User
from sqlalchemy import select
from sqlalchemy.orm import Session

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"


def seed_users(session: Session) -> None:
    session.add_all([User(fitcrew_user_id=OWNER), User(fitcrew_user_id=OTHER)])
    session.commit()


def test_private_book_chunks_are_encrypted_and_page_cited(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_users(session)
    service = KnowledgeService(session, field_cipher)
    source = service.import_pages(
        fitcrew_user_id=OWNER,
        title="控糖革命",
        author="Jessie Inchauspé",
        content_hash="a" * 64,
        rights_status="user_provided_private_use_unverified",
        pages={12: "进餐顺序可能影响餐后葡萄糖曲线。先吃蔬菜，再吃蛋白质。"},
    )

    stored = session.scalar(select(KnowledgeChunk).where(KnowledgeChunk.source_id == source.id))
    assert stored is not None
    assert "葡萄糖".encode() not in stored.content_ciphertext

    hits = service.search_private(OWNER, "餐后葡萄糖", limit=3)

    assert hits[0].title == "控糖革命"
    assert hits[0].page_number == 12
    assert "葡萄糖" in hits[0].excerpt


def test_other_user_cannot_search_owner_private_book(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_users(session)
    service = KnowledgeService(session, field_cipher)
    service.import_pages(
        fitcrew_user_id=OWNER,
        title="睡眠优化完全指南",
        author=None,
        content_hash="b" * 64,
        rights_status="user_provided_private_use_unverified",
        pages={1: "稳定的起床时间有助于保持昼夜节律。"},
    )

    assert service.search_private(OTHER, "昼夜节律") == []
    try:
        service.get_private_source(OTHER, title="睡眠优化完全指南")
    except KnowledgeAccessDenied:
        pass
    else:
        raise AssertionError("another user accessed an owner-only source")


def test_public_search_reads_only_published_versions(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_users(session)
    service = KnowledgeService(session, field_cipher)
    draft = service.import_pages(
        fitcrew_user_id=None,
        title="公共候选",
        author=None,
        content_hash="c" * 64,
        rights_status="licensed_summary",
        pages={1: "步行是低门槛活动。"},
        visibility="public",
    )

    assert service.search_public("步行") == []

    service.review_source(
        draft.id,
        reviewer_role="editor",
        decision="approved",
        rationale="来源和适用边界已核验",
        applicability="一般成人的低强度活动建议",
    )

    assert service.search_public("步行")[0].title == "公共候选"


def test_withdrawn_source_is_removed_from_retrieval(
    session: Session, field_cipher: FieldCipher
) -> None:
    seed_users(session)
    service = KnowledgeService(session, field_cipher)
    source = service.import_pages(
        fitcrew_user_id=OWNER,
        title="百岁人生行动手册",
        author=None,
        content_hash="d" * 64,
        rights_status="user_provided_private_use_unverified",
        pages={8: "长期健康需要可持续的日常行动。"},
    )
    assert service.search_private(OWNER, "可持续")[0].title == "百岁人生行动手册"

    service.withdraw_source(OWNER, source.id)

    assert service.search_private(OWNER, "可持续") == []
