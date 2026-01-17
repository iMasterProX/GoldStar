from pathlib import Path

EXPECTED_PACKS = [
    {
        "name": "BLF_CustomArmor",
        "desc": {
            "ko": "갑옷/방어구 등 착용 방어 장비 리소스 팩입니다.",
            "en": "Resources for armor and wearable defensive gear.",
        },
    },
    {
        "name": "BLF_CustomBlocks",
        "desc": {
            "ko": "1.5칸 크기 이내의 모델링을 블럭 오브젝트로 넣을때 쓰는 리소스팩입니다.",
            "en": "Pack for block objects with models up to 1.5 blocks in size.",
        },
    },
    {
        "name": "BLF_CustomCore",
        "desc": {
            "ko": "공용 렌더/머티리얼/사운드 등 핵심 리소스 팩입니다.",
            "en": "Core shared resources (render/material/sounds).",
        },
    },
    {
        "name": "BLF_CustomCrops",
        "desc": {
            "ko": "작물, 농사 관련 블록 및 엔티티 요소를 넣는 팩입니다.",
            "en": "Crops and farming related blocks/entities.",
        },
    },
    {
        "name": "BLF_CustomEntity",
        "desc": {
            "ko": "캐릭터, 몬스터, 사물, 기타 엔티티 요소 등을 넣는 팩입니다.",
            "en": "Characters, monsters, props, and other entities.",
        },
    },
    {
        "name": "BLF_CustomFurniture",
        "desc": {
            "ko": "가구 및 인테리어 오브젝트 요소를 넣는 팩입니다.",
            "en": "Furniture and interior object resources.",
        },
    },
    {
        "name": "BLF_CustomItems",
        "desc": {
            "ko": "일반 아이템, 아이콘, 텍스처 요소를 넣는 팩입니다.",
            "en": "General items, icons, and textures.",
        },
    },
    {
        "name": "BLF_CustomPets",
        "desc": {
            "ko": "펫/동물 엔티티 및 관련 리소스를 넣는 팩입니다.",
            "en": "Pets/animals entities and related resources.",
        },
    },
    {
        "name": "BLF_CustomSystem",
        "desc": {
            "ko": "UI 커스텀한거 넣는 곳입니다.",
            "en": "UI customization resources.",
        },
    },
    {
        "name": "BLF_CustomTools",
        "desc": {
            "ko": "도구류(곡괭이/도끼 등) 리소스를 넣는 팩입니다.",
            "en": "Tool resources (pickaxe/axe/etc).",
        },
    },
    {
        "name": "BLF_CustomWeapon",
        "desc": {
            "ko": "무기류 리소스를 넣는 팩입니다.",
            "en": "Weapon resources.",
        },
    },
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
