# goldstar

마인크래프트 베드락 에디션용 리소스팩 종합 자동화 프로그램입니다.

## 실행 방법

1) 아래 경로에 BLF_ 리소스팩 11개가 준비되어 있어야 합니다.

- C:\Users\<사용자이름>\AppData\Roaming\Minecraft Bedrock\Users\Shared\games\com.mojang\development_resource_packs

2) 이 저장소 폴더로 이동해 실행합니다.

```powershell
cd "C:\Users\minsi\AppData\Roaming\Minecraft Bedrock\Users\Shared\games\com.mojang\development_resource_packs\goldstar"
python -m goldstar
```

## 사용 흐름

- 로딩 화면에서 로고가 표시됩니다.
- 팩 선택 화면에서 BLF_ 11개 팩을 검사합니다.
- 하나라도 누락되면 목록을 안내합니다.
- 전부 없으면 최소 리소스팩(메타데이터 기반)을 생성할지 묻습니다.
- CustomEntity를 더블클릭하면 새 엔티티 생성 화면으로 이동합니다.

## CustomEntity 입력 규칙

- 필수: 엔티티 이름, 모델링, 텍스처
- 선택: 애니메이션 컨트롤러, 애니메이션, 아이콘 텍스처
- 엔티티 이름: 영문 소문자/숫자/언더바만, 최대 20자
- prefix: 영문 소문자만 (비우면 기본값 blf)

## 참고

- 로고 화질 개선을 위해 Pillow를 설치하면 더 선명해집니다.

```powershell
pip install pillow
```