from pathlib import Path

EXPECTED_PACKS = [
    ("BLF_CustomArmor", "갑옷/방어구 등 착용 방어 장비 리소스 팩입니다."),
    (
        "BLF_CustomBlocks",
        "1.5칸 크기 이내의 모델링을 블럭 오브젝트로 넣을때 쓰는 리소스팩입니다.",
    ),
    ("BLF_CustomCore", "공용 렌더/머티리얼/사운드 등 핵심 리소스 팩입니다."),
    ("BLF_CustomCrops", "작물, 농사 관련 블록 및 엔티티 요소를 넣는 팩입니다."),
    ("BLF_CustomEntity", "캐릭터, 몬스터, 사물, 기타 엔티티 요소 등을 넣는 팩입니다."),
    ("BLF_CustomFurniture", "가구 및 인테리어 오브젝트 요소를 넣는 팩입니다."),
    ("BLF_CustomItems", "일반 아이템, 아이콘, 텍스처 요소를 넣는 팩입니다."),
    ("BLF_CustomPets", "펫/동물 엔티티 및 관련 리소스를 넣는 팩입니다."),
    ("BLF_CustomSystem", "UI 커스텀한거 넣는 곳입니다."),
    ("BLF_CustomTools", "도구류(곡괭이/도끼 등) 리소스를 넣는 팩입니다."),
    ("BLF_CustomWeapon", "무기류 리소스를 넣는 팩입니다."),
]

DEFAULT_ROOT_WINDOWS = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "Minecraft Bedrock"
    / "Users"
    / "Shared"
    / "games"
    / "com.mojang"
    / "development_resource_packs"
)