# Backend-ai
Backend service dedicated to RAG chatbot functionalities using Langchain and OpenAI API
# backend-ai 코랩 연동 가이드

팀 프로젝트 협업을 위해, 코랩에서 [jinjja-fun-trip](https://github.com/jinjja-fun-trip) 조직의 **backend-ai** 리포지토리를 클론(clone)하고, 원하는 브랜치에 코드 커밋 및 푸쉬하는 방법에 대한 리드미입니다.

## 주의

- **클론한 리포지토리 내 파일(backend-ai 폴더 내 파일)**
    
    실제 코드 작성 및 수정은 클론한 **backend-ai** 리포지토리 내부의 파일에서 진행합니다. 각 팀원은 자신의 기능이나 버그 수정을 위해 해당 리포지토리 내에서 작업하게 됩니다.
    
- **연동용 코랩파일 (backend-ai 폴더 내 파일이 아닌 연동을 위한 별도의 파일)**
    
    아래 코드는 소개된 `깃허브레포지토리연동용.ipynb` 파일은 리포지토리와의 연동 및 환경 설정을 위한 별도의 파일입니다.  이 파일을 통해 리포지토리 클론, 커밋, 푸쉬 및 Pull 작업을 쉽게 수행할 수 있습니다.
    
    이 파일은 코드 작업을 위한 주요 파일이 아니므로, 수정 작업은 클론한 리포지토리에서 진행해 주세요.
    

## 1. 사전 준비사항

- **Google 계정 및 Google Drive**
    - 코랩 사용을 위해 Google Drive를 마운트할 수 있어야 합니다.
- **GitHub 계정**
    - 리포지토리 접근 및 코드 푸쉬/풀을 위해 GitHub 계정이 필요합니다.
- **GitHub Personal Access Token 발급**
    - 안전한 인증을 위해 개인 깃허브 토큰이 필요하며, 이를 환경변수로 관리합니다.

## 2. GitHub Personal Access Token (PAT) 발급 방법

1. GitHub에 로그인한 후, 우측 상단의 프로필 아이콘을 클릭하고 **Settings**로 이동합니다.
2. 좌측 메뉴에서 **Developer settings**를 선택한 후, **Personal access tokens** > **Tokens (classic)** 메뉴로 이동합니다.
3. **Generate new token** 버튼을 클릭하여 새 토큰을 생성합니다.
4. 토큰에 사용할 **Note**와 **Expiration**을 설정하고, 필요한 **scope** (예: `repo` – 리포지토리 접근 권한)를 선택합니다. (프로젝트 기간동안은 사용할 수 있도록 유효 기간을 설정합니다. )
5. **Generate token**을 클릭하면, 새로 발급된 토큰을 복사할 수 있습니다.

## 3. 환경변수 및 사용자 설정

본인의 GitHub 정보를 입력할 수 있도록 아래와 같이 환경 변수를 관리합니다.

 셀에 다음 코드를 추가하여 환경변수를 설정할 수 있습니다. 

```python
import os
os.environ["GIT_TOKEN"] = "발급받은_토큰값을_여기에_입력"
os.environ["GIT_USERNAME"] = "본인깃허브아이디"
os.environ["GIT_EMAIL"] = "본인이메일@example.com"

```

### 3.2. Git 사용자 설정

코랩 노트북 내에서 설정한 환경변수를 가져와 Git 설정에 사용합니다.  

```python
# 환경변수에서 가져오기
GIT_TOKEN = os.getenv("GIT_TOKEN")
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_EMAIL = os.getenv("GIT_EMAIL")

# Git 사용자 정보 설정 
!git config --global user.email "{GIT_EMAIL}"
!git config --global user.name "{GIT_USERNAME}"

```

## 4. 리포지토리 클론 및 작업 환경 설정

Google Drive를 마운트하고 지정한 경로에 리포지토리를 클론하는 전체 과정에 해당합니다.

```python
# Google Drive 마운트
from google.colab import drive

ROOT = "/gdrive"
drive.mount(ROOT)
```

→ Mounted at /gdrive

<img width="360" alt="image" src="https://github.com/user-attachments/assets/5820c75d-9d44-4d81-981b-7c4bab062432" />


```python

# Google Drive 내의 프로젝트 경로 설정
from os.path import join

MY_GOOGLE_DRIVE_PATH = 'My Drive/Colab Notebooks/'
PROJECT_PATH = join(ROOT, MY_GOOGLE_DRIVE_PATH)
print("PROJECT_PATH: ", PROJECT_PATH)
```

→ PROJECT_PATH:  /gdrive/My Drive/Colab Notebooks/

```python

# GitHub 리포지토리 정보 설정
GIT_ORGANIZATION = "jinjja-fun-trip"
GIT_REPOSITORY = "backend-ai"

# Git 클론용 URL 생성
GIT_PATH = "https://" + GIT_TOKEN + "@github.com/" + GIT_ORGANIZATION + "/" + GIT_REPOSITORY + ".git"
print("GIT_PATH: ", GIT_PATH)
```

```python
# 프로젝트 경로로 이동
%cd "{PROJECT_PATH}"
```

→ `/gdrive/My Drive/Colab Notebooks`

<img width="387" alt="image" src="https://github.com/user-attachments/assets/6bde2943-058b-41db-bc63-9e18e1d20524" />


---

```python
# 이동한 해당 경로에서 리포지토리 클론
!git clone "{GIT_PATH}"
```

<img width="661" alt="image" src="https://github.com/user-attachments/assets/a1c4f775-dbd7-47f7-ac14-13bb48000730" />

project path에 깃허브 리포지토리에 대응되는 폴더 [backend-ai]가 생성된 것을 확인할 수 있습니다.

```python
# 클론 받은 디렉토리로 이동
%cd backend-ai/
```

<img width="369" alt="image" src="https://github.com/user-attachments/assets/d55bcdb3-cff9-4ec2-91b9-879b07e98af3" />

```python
# 브랜치 확인 및 상태 체크
!git branch
!git status
```

<img width="454" alt="image" src="https://github.com/user-attachments/assets/c0cbf41a-c7d4-4d5d-8e1b-2504c4c597f4" />


```python
# 폴더 구조 확인용
!apt-get install tree
!tree
```

필수x : 폴더구조 확인을 위해 tree를 install해 사용할 수 있습니다.

<img width="679" alt="image" src="https://github.com/user-attachments/assets/3ce90d21-d0c1-49a7-a81d-c3e83560ec6f" />


## 5. 코드 커밋, 푸쉬 및 Pull 받기

### 5.1. 코드 커밋 및 푸쉬

코랩에 클론한 해당 리포지토리에서 작업을 합니다. (**backend-ai 폴더 내 파일에서 실제 작업을 수행합니다.** )

<img width="666" alt="image" src="https://github.com/user-attachments/assets/ce5c54c6-dc8c-4b3e-9f01-ffce406043b7" />

작업 후 변경사항을 GitHub에 반영하기 위해선  `깃허브레포지토리연동용.ipynb` 파일에서 GitHub 리포지토리의 커밋, 푸쉬 등의 작업을 쉽게 수행합니다.

```bash
# 변경된 파일 추가
!git add .

# 커밋 (커밋 메시지 수정 가능)
!git commit -m "[chore] 커밋 테스트"
```

<img width="466" alt="image" src="https://github.com/user-attachments/assets/1d47fa8f-d050-433f-aa50-ed3eab0a0ce0" />

```bash
# 변경사항 푸쉬
!git push
```

<img width="668" alt="image" src="https://github.com/user-attachments/assets/2600faf3-2172-45b4-a699-0d0dcb99c1ef" />

> cf : 브랜치를 변경하고 싶다면 !git checkout 브랜치명 명령어를 사용하세요.
> 

깃허브에 코랩에서 push한 커밋이 반영됨을 확인할 수 있습니다.

<img width="662" alt="image" src="https://github.com/user-attachments/assets/99354b65-7c57-49d8-9271-f5d929a27276" />

### 5.2. 최신 변경사항 Pull 받기

리포지토리에 반영된 최신 변경사항을 가져오려면 아래 명령어를 사용합니다.

(+ 코랩이 아닌, backend-ai 리포지토리에 비주얼 스튜티오 코드 등으로 작업해서 원격 저장소에 Push한 사항도 pull 받을 수 있습니다. )

<img width="641" alt="image" src="https://github.com/user-attachments/assets/652a99f0-66d5-4d5c-8458-6d64aaee9574" />


```python
# 현재 브랜치의 최신 변경사항 Pull 받기
!git pull

# 또는, 특정 브랜치에서 Pull 받으려면:
!git pull origin 브랜치명

```

<img width="653" alt="image" src="https://github.com/user-attachments/assets/407b9378-9f8f-4352-9bc8-a675be7f3fd7" />

깃허브레포지토리연동용.ipynb 파일에서 Pull 명렁을 실행한 후에 코랩 상의  backend-ai 리포지토리를 확인하면, 리포지토리에 반영된 최신 변경사항이 반영된 것을 확인할 수 있습니다.

<img width="648" alt="image" src="https://github.com/user-attachments/assets/839d9057-b17c-423e-8e18-cd0625350711" />
