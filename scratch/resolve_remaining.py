import pathlib

readme_path = pathlib.Path('README.md')
content = readme_path.read_text(encoding='utf-8', errors='replace')

start_idx = content.find("<<<<<<< Updated upstream")
end_idx = content.find(">>>>>>> Stashed changes")

if start_idx != -1 and end_idx != -1:
    end_idx += len(">>>>>>> Stashed changes")
    
    resolved = """3. `URL` に `http://[親機のIP]:8377/mcp` を入力。

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
    
    new_content = content[:start_idx] + resolved + content[end_idx:]
    readme_path.write_text(new_content, encoding='utf-8')
    print("Resolved remaining conflict successfully.")
else:
    print("Error: Could not find conflict markers.")
