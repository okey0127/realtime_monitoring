# realtime_monitoring
## RealTime-Monitoring System with Raspberry Pi
* Camera, Vibration(Impact) Sensor, IR Temperature Sensor

## Python
* OpenCV Library \
 ▷ 간단한 영상처리
* Pandas Library \
 ▷ 수집된 데이터 DataFrame으로 정리
 ▷ CSV 형식으로 저장 
* Flask Framework\
 ▷ 웹서버 개설 및 실시간 스트리밍 \
 ▷ 센서 데이터 웹서버로 전달 \
 ▷ 경고값 설정 (POST) \
 ▷ 지정한 날짜의 CSV 파일 데이터 확인 및 다운(GET) 
* Threading Library\
 ▷ 데이터 수집 루프문, 영상 수집 및 처리 루프문 병렬처리 → 속도 향상
* Schedule Library\
 ▷ 데이터 저장 설정 / 주기: 1초 \
 ▷ 오래된 파일 제거 코드 작성 / 주기: 사용자 설정 \
 ▷ 경고 여부에 따라 부저 작동 / 주기: 0.1초 \
 ▷ LCD 화면을 초과하는 글자가 넘어가며 표시되도록 함 / 주기: 1초 * 1초마다 한칸씩 이동 

## JavaScript
* Chart.js \
 ▷ 진동, 온도 그래프 작성
* jquery.js \
 ▷ 데이터 리스트 페이지에서 원하는 데이터 읽어오기

## 부팅 시 코드 자동실행(Raspbian)
in terminal
> sudo nano /etc/profile.d/bash_completion.sh
> 
> sudo python3 realtime_monitoring/Stream.py
