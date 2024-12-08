# TFTP Client

이 TFTP 클라이언트는 소켓 API와 파이썬을 이용하여 TFTP 서버(tftpd-hpa)와 통신하는 프로그램입니다. 기본적으로 파일을 다운로드(get)하거나 업로드(put)하는 기능을 제공하며, 'octet' 모드만 지원합니다.

## 요구 사항
- Python 3.x

## 사용법
```bash
$ tftp <ip_address> [-p port_number] <get|put> <filename>
