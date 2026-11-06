medium rev crypto can
English
Analyze the ECU-D firmware based on RAMN, bypass the UDS authentication, and read the protected DID. The distributed files include the firmware (ECUD.hex), an expired certificate and private key, and a client environment for connecting to the remote server.

Run sudo ./connect.sh 20.210.80.68 13337 to start a Docker environment and communicate with the remote server via vcan0.

Note: This challenge requires a Linux environment with SocketCAN support. Please run the connection script on a Linux system where the vcan0 interface can be created.
Sessions are terminated after 5 minutes, and the connection script tries to reconnect automatically.

日本語
RAMNのECU-Dを元にしたファームウェアを解析し、UDSの認証を突破して、保護されたDIDを読み出してください。 配布物にはファームウェア (ECUD.hex)、期限切れの証明書と秘密鍵、リモート接続用クライアント環境が含まれます。

sudo ./connect.sh 20.210.80.68 13337でDocker環境を立ち上げると、vcan0経由でリモートサーバと通信することができます。

注意: この問題では SocketCAN が利用可能な Linux 環境が必要です。vcan0 インターフェースを作成できる Linux 環境で接続スクリプトを実行してください。
セッションは5分で強制終了されますが、接続スクリプトは自動的に再接続を試みます。
