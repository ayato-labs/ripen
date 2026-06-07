import pathlib

readme_path = pathlib.Path('README.md')
content = readme_path.read_text(encoding='utf-8', errors='replace')

# 1. 冒頭のコンフリクト箇所の置換
conflict_1 = """<<<<<<< Updated upstream
> **Official Distribution**: We strongly recommend running the Ripen Hub via **Docker**. For Windows users who prefer it, standalone `.exe` binaries are also available in the [Official GitHub Releases](https://github.com/ayato-labs/ripen/releases).

> [!NOTE]
> **Distribution Policy**: To provide the best developer experience and maximize multi-platform compatibility, our primary distribution method is **Docker Container Images via GHCR**. PyPI distribution has been discontinued.
=======
> **Official Distribution**: We distribute Ripen primarily as a standalone Windows native binary (`Ripen.exe`). 
> 
> **Notice on Docker Policy**: We have discontinued Docker image distribution due to potential licensing issues in corporate environments. Since Ripen only requires a single Windows machine to be running in your network, all other AI agents can connect and interact with it simply via HTTP. Therefore, cross-platform compatibility is practically complete without needing complex containerization. We have consolidated our distribution into Windows `.exe` binaries and Python source execution.
>>>>>>> Stashed changes"""

resolved_1 = """> **Official Distribution**: We distribute Ripen primarily as a standalone Windows native binary (`Ripen.exe`). 
> 
> **Notice on Docker Policy**: We have discontinued Docker image distribution due to potential licensing issues in corporate environments. Since Ripen only requires a single Windows machine to be running in your network, all other AI agents can connect and interact with it simply via HTTP. Therefore, cross-platform compatibility is practically complete without needing complex containerization. We have consolidated our distribution into Windows `.exe` binaries and Python source execution."""

# 2. 日本語セクションのコンフリクト箇所の置換
conflict_2 = """<<<<<<< Updated upstream
=======
3. `URL` に `http://[サーバーのIP]:8377/mcp` を入力。

#### 3. 動作確認
エージェントに「このプロジェクトの規約を教えて」と聞いてみてください。サーバーに蓄積された知識を答えられれば成功です！

---

一般的なMCPメモリサーバーは `stdio` モードで動作し、**1つのIDEと1つのサーバー**が1:1で接続されます。知識はそのIDEのプロセス内に閉じており、他のツールや他のユーザーからは参照できません。

**Ripenは `Streamable HTTP Server` として動作します。** HTTPサーバーとして常駐し、複数のIDE・複数のメンバーが同時に読み書きできます。

> **Docker配布の取りやめとマルチOS対応について**
> 企業や商用環境での利用時に懸念されるDocker Desktop等のライセンス問題を考慮し、Dockerによるコンテナ配布方針は取りやめました。
> .exeオンリーにした理由については、このRipenはWindows環境が一台あったら、その他のAIエージェントはHTTP通信をするだけであるので、ほとんどすでにマルチOS対応は完了しているも同然であると判断して、ライセンスの問題があるdockerでの配布方針を取りやめました。
> チーム内にWindows環境が1台稼働していれば、MacやLinuxなど他のOSを使うメンバーのAIエージェントはHTTP通信（SSE）で接続するだけで利用可能です。これにより、配布形態をライセンス問題のないWindows `.exe` およびPythonソース起動に一本化しています。

> **最大のポイント**: Claude Code・Cursor・Antigravity・Gemini CLI の間で知識を共有できます。しかも、**違うアカウントを使った別の人のPCで稼働するAIエージェントとの間でも。**

これは「便利な追加機能」ではなく、エージェントフレームワークが構造的に実現不可能な**唯一の機能**です。

詳細は [概念的要件定義書](docs/概念的要件定義書.md) · [アーキテクチャ](docs/アーキテクチャ.md) をご覧ください。
2. `Type` を **SSE** に指定。
>>>>>>> Stashed changes"""

resolved_2 = """3. `URL` に `http://[親機のIP]:8377/mcp` を入力。

#### 3. 動作確認
エージェントに「このプロジェクトの規約を教えて」と聞いてみてください。親機に蓄積された知識を答えられれば成功です！

---

一般的なMCPメモリサーバーは `stdio` モードで動作し、**1つのIDEと1つのサーバー**が1:1で接続されます。知識はそのIDEのプロセス内に閉じており、他のツールや他のユーザーからは参照できません。

**Ripenは `Streamable HTTP Hub` として動作します。** HTTPサーバーとして常駐し、複数のIDE・複数のメンバーが同時に読み書きできます。

> **Docker配布の取りやめとマルチOS対応について**
> 企業や商用環境での利用時に懸念されるDocker Desktop等のライセンス問題を考慮し、Dockerによるコンテナ配布方針は取りやめました。
> .exeオンリーにした理由については、このRipenはWindows環境が一台あったら、その他のAIエージェントはHTTP通信をするだけであるので、ほとんどすでにマルチOS対応は完了しているも同然であると判断して、ライセンスの問題があるdockerでの配布方針を取りやめました。
> チーム内にWindows環境が1台稼働していれば、MacやLinuxなど他のOSを使うメンバーのAIエージェントはHTTP通信（SSE）で接続するだけで利用可能です。これにより、配布形態をライセンス問題のないWindows `.exe` およびPythonソース起動に一本化しています。

> **最大のポイント**: Claude Code・Cursor・Antigravity・Gemini CLI の間で知識を共有できます。しかも、**違うアカウントを使った別の人のPCで稼働するAIエージェントとの間でも。**

これは「便利な追加機能」ではなく、エージェントフレームワークが構造的に実現不可能な**唯一の機能**です。

詳細は [概念的要件定義書](docs/概念的要件定義書.md) · [アーキテクチャ](docs/アーキテクチャ.md) をご覧ください。"""

if conflict_1 not in content:
    print("Error: conflict_1 not found!")
if conflict_2 not in content:
    print("Error: conflict_2 not found!")

content = content.replace(conflict_1, resolved_1)
content = content.replace(conflict_2, resolved_2)

readme_path.write_text(content, encoding='utf-8')
print("Successfully resolved README.md conflicts")
