import sys
import pathlib

readme_path = pathlib.Path('README.md')
content = readme_path.read_text(encoding='utf-8', errors='replace')

target_1 = "> **Notice on Docker Policy**: We have discontinued Docker image distribution. In commercial and corporate environments, Docker Desktop licensing policies present compliance challenges for developers. Since Ripen is a Streamable HTTP/SSE server, **you only need a single Windows machine running Ripen within your team's network**. All other team members, regardless of their OS (macOS, Linux, etc.), can connect to this single instance purely via HTTP, making cross-platform local setups or Docker containers unnecessary for local client usage."
replace_1 = "> **Notice on Docker Policy**: We have discontinued Docker image distribution due to potential licensing issues in corporate environments. Since Ripen only requires a single Windows machine to be running in your network, all other AI agents can connect and interact with it simply via HTTP. Therefore, cross-platform compatibility is practically complete without needing complex containerization. We have consolidated our distribution into Windows `.exe` binaries and Python source execution."

target_2 = "    *Note: The Docker container is configured to listen on `0.0.0.0`, meaning it accepts connections from any IP address reaching the host machine.*"
replace_2 = "    *Note: By default, the Ripen Server is configured to listen on `0.0.0.0`, meaning it accepts connections from any IP address reaching the host machine.*"

target_3 = """> **Docker配布の取りやめとマルチOS対応について**
> 企業や商用環境での利用時に懸念されるDocker Desktop等のライセンス問題を考慮し、Dockerによるコンテナ配布方針は取りやめました。
> 本サーバーは常駐型のHTTP/SSEサーバーであるため、チーム内にWindows環境が1台稼働していれば、MacやLinuxなど他のOSを使うメンバーのAIエージェントはHTTP通信（SSE）で接続するだけで利用可能です。これにより実質的なマルチOS対応が容易に実現できるため、配布形態をライセンス問題のないWindows `.exe` およびPythonソース起動に一本化しています。"""

replace_3 = """> **Docker配布の取りやめとマルチOS対応について**
> 企業や商用環境での利用時に懸念されるDocker Desktop等のライセンス問題を考慮し、Dockerによるコンテナ配布方針は取りやめました。
> .exeオンリーにした理由については、このRipenはWindows環境が一台あったら、その他のAIエージェントはHTTP通信をするだけであるので、ほとんどすでにマルチOS対応は完了しているも同然であると判断して、ライセンスの問題があるdockerでの配布方針を取りやめました。
> チーム内にWindows環境が1台稼働していれば、MacやLinuxなど他のOSを使うメンバーのAIエージェントはHTTP通信（SSE）で接続するだけで利用可能です。これにより、配布形態をライセンス問題のないWindows `.exe` およびPythonソース起動に一本化しています。"""

if target_1 not in content:
    print("Warning: target_1 not found!")
if target_2 not in content:
    print("Warning: target_2 not found!")
if target_3 not in content:
    print("Warning: target_3 not found!")

content = content.replace(target_1, replace_1)
content = content.replace(target_2, replace_2)
content = content.replace(target_3, replace_3)

readme_path.write_text(content, encoding='utf-8')
print("Successfully updated README.md")
