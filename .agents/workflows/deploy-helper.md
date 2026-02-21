---
description: Deploy the Ironbird-DAS Streamlit app to Streamlit Community Cloud
---

# 1. 의존성 확인 (Check Dependencies)
의존성 파일(`requirements.txt`)에 필요한 라이브러리가 명시되어 있는지 확인합니다.

# 2. 로컬 테스트 (Local Test)
배포 전 로컬 웹 환경에서 앱이 정상적으로 실행되는지 점검합니다. 
```bash
streamlit run app.py
```

# 3. Git 및 GitHub 업로드 (Push to GitHub)
Streamlit Cloud 배포를 하려면 코드가 GitHub에 업로드되어 있어야 합니다.
// turbo-all
```bash
git add .
git commit -m "Ready for Streamlit Deployment"
git push origin main
```

# 4. Streamlit Cloud 연동 및 배포 (Deploy)
1. [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 로그인합니다.
2. **New app** 버튼을 클릭합니다.
3. 본 프로젝트가 있는 GitHub 저장소(Repository), 배포 브랜치(main), 그리고 메인 파일 경로(`app.py`)를 선택합니다.
4. 화면 하단의 **Deploy** 버튼을 클릭하면 수 분 내에 웹 서비스 배포가 완료됩니다!
