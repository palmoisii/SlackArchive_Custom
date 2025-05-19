import json
import os
from pathlib import Path

def transform_channel(channel):
   """チャンネル情報を新しいフォーマットに変換する"""
   return {
       "id": channel["id"],
       "name": channel["name"],
       "is_channel": True,
       "is_group": False,
       "is_im": False,
       "is_mpim": False,
       "is_private": False,
       "created": channel["created"],
       "is_archived": channel.get("is_archived", False),
       "is_general": channel.get("is_general", False),
       "unlinked": 0,
       "name_normalized": channel["name"],
       "is_shared": False,
       "is_org_shared": False,
       "is_pending_ext_shared": False,
       "pending_shared": [],
       "context_team_id": "T07TZU03H0S",
       "updated": int(channel["created"] * 1000),
       "parent_conversation": None,
       "creator": channel["creator"],
       "is_ext_shared": False,
       "shared_team_ids": ["T07TZU03H0S"],
       "pending_connected_team_ids": [],
       "is_member": True,
       "topic": channel["topic"],
       "purpose": channel["purpose"],
       "properties": {
           "canvas": {
               "file_id": f"F{channel['id'][1:]}",
               "is_empty": True,
               "quip_thread_id": f"W{channel['id'][1:]}"
           },
           "tabs": [
               {
                   "type": "bookmarks",
                   "label": "",
                   "id": "bookmarks"
               },
               {
                   "type": "files",
                   "label": "",
                   "id": "files"
               },
               {
                   "id": f"Ct{channel['id'][1:]}",
                   "type": "folder",
                   "label": ""
               }
           ],
           "tabz": [
               {"type": "bookmarks"},
               {"type": "files"},
               {
                   "id": f"Ct{channel['id'][1:]}",
                   "type": "folder"
               }
           ],
           "use_case": "project"
       },
       "previous_names": [],
       "num_members": len(channel.get("members", []))
   }

def transform_users(users_list):
   """ユーザーリストを辞書形式に変換する"""
   users_dict = {}
   for user in users_list:
       user_id = user["id"]
       users_dict[user_id] = user
   return users_dict

def get_timestamp(message):
   """メッセージからタイムスタンプを安全に取得する"""
   if 'ts' in message:
       return float(message['ts'])
   return 0

def process_channel_messages(messages_list):
    """チャンネルのメッセージを処理し、スレッド返信を適切に統合する"""
    thread_messages = {}  # スレッドの返信を一時的に保存
    root_messages = []    # スレッドの親メッセージを保存

    for msg in messages_list:
        if 'thread_ts' in msg and msg['ts'] != msg['thread_ts']:
            # これはスレッドの返信
            thread_ts = msg['thread_ts']
            if thread_ts not in thread_messages:
                thread_messages[thread_ts] = []
            thread_messages[thread_ts].append(msg)
        else:
            # これはスレッドの親メッセージまたは通常のメッセージ
            root_messages.append(msg)

    # スレッドの返信を親メッセージに統合
    for msg in root_messages:
        if 'thread_ts' in msg and msg['ts'] == msg['thread_ts']:
            thread_ts = msg['thread_ts']
            if thread_ts in thread_messages:
                # スレッド内のメッセージも時系列順（新しい順）にソート
                sorted_replies = sorted(thread_messages[thread_ts], 
                                     key=lambda x: float(x['ts']), 
                                     reverse=False)
                msg['replies'] = sorted_replies

    return root_messages

def process_slack_export(export_dir, output_dir):
   # 基本情報の読み込み
   with open(os.path.join(export_dir, 'channels.json'), 'r', encoding='utf-8') as f:
       channels = json.load(f)
   
   # channels.jsonの変換
   transformed_channels = [transform_channel(channel) for channel in channels]
   
   # users.jsonの読み込みと変換
   with open(os.path.join(export_dir, 'users.json'), 'r', encoding='utf-8') as f:
       users_list = json.load(f)
   users = transform_users(users_list)

   # チャンネルごとのメッセージを集約
   channel_messages = {}
   
   # チャンネルフォルダを探索
   for channel in channels:
       channel_id = channel['id']
       channel_dir = Path(export_dir) / channel['name']
       
       if not channel_dir.exists():
           print(f"Warning: Directory not found for channel {channel['name']}")
           continue
           
       messages = []
       # 日付ごとのJSONファイルを読み込み
       for json_file in channel_dir.glob('*.json'):
           try:
               with open(json_file, 'r', encoding='utf-8') as f:
                   daily_messages = json.load(f)
                   messages.extend(daily_messages)
           except json.JSONDecodeError:
               print(f"Warning: Could not parse {json_file}")
               continue
           except Exception as e:
               print(f"Error processing {json_file}: {str(e)}")
               continue

       # メッセージを時系列でソート
       try:
           messages.sort(key=get_timestamp, reverse=True)
       except Exception as e:
           print(f"Error sorting messages for channel {channel_id}: {str(e)}")

       # スレッド返信を処理
       processed_messages = process_channel_messages(messages)
       channel_messages[channel_id] = processed_messages

   # 出力ディレクトリの作成
   os.makedirs(output_dir, exist_ok=True)

   # チャンネルごとのメッセージファイルを出力
   for channel_id, messages in channel_messages.items():
       output_file = os.path.join(output_dir, f'{channel_id}.json')
       try:
           with open(output_file, 'w', encoding='utf-8') as f:
               json.dump(messages, f, ensure_ascii=False, indent=2)
       except Exception as e:
           print(f"Error writing {output_file}: {str(e)}")

   # 変換したchannels.jsonを出力
   try:
       with open(os.path.join(output_dir, 'channels.json'), 'w', encoding='utf-8') as f:
           json.dump(transformed_channels, f, ensure_ascii=False, indent=2)
   except Exception as e:
       print(f"Error writing channels.json: {str(e)}")

   # slack-archive.jsonの生成
   archive_data = {
       "channels": {
           channel_id: {"messages": len(messages)} 
           for channel_id, messages in channel_messages.items()
       }
   }
   
   try:
       with open(os.path.join(output_dir, 'slack-archive.json'), 'w', encoding='utf-8') as f:
           json.dump(archive_data, f, ensure_ascii=False, indent=2)
   except Exception as e:
       print(f"Error writing slack-archive.json: {str(e)}")

   # 変換したusers.jsonを出力
   try:
       with open(os.path.join(output_dir, 'users.json'), 'w', encoding='utf-8') as f:
           json.dump(users, f, ensure_ascii=False, indent=2)
   except Exception as e:
       print(f"Error writing users.json: {str(e)}")

   # emojis.jsonがある場合はコピー
   emoji_path = os.path.join(export_dir, 'emojis.json')
   if os.path.exists(emoji_path):
       try:
           with open(emoji_path, 'r', encoding='utf-8') as f:
               emojis = json.load(f)
           with open(os.path.join(output_dir, 'emojis.json'), 'w', encoding='utf-8') as f:
               json.dump(emojis, f, ensure_ascii=False, indent=2)
       except Exception as e:
           print(f"Error processing emojis.json: {str(e)}")

def main():
    export_dir = "./jsons"  # Slackエクスポートの解凍先
    output_dir = "./slack-archive"  # 変換後のファイルの出力先
    
    process_slack_export(export_dir, output_dir)

if __name__ == "__main__":
    main()