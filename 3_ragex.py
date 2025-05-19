from pathlib import Path
from bs4 import BeautifulSoup
import urllib.parse

def extract_extension(url):
    url_without_query = url.split('?')[0]
    return Path(url_without_query).suffix

def process_html(directory):
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"ディレクトリが見つかりません: {directory}")
            
        for html_file in directory_path.rglob('*.html'):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    # 'html.parser'の代わりに'html5lib'を使用してより正確な構造を維持
                    soup = BeautifulSoup(f.read(), 'html5lib')
                
                modified = False
                
                for files_div in soup.find_all('div', class_='files'):
                    for link in files_div.find_all('a'):
                        if 'href' in link.attrs and link['href'].startswith('https://files.slack.com/files-pri/'):
                            original_url = link['href']
                            
                            img = link.find('img')
                            if img and 'src' in img.attrs:
                                src_path = img['src']
                                src_without_ext = str(Path(src_path).with_suffix(''))
                                
                                extension = extract_extension(original_url)
                                new_url = f"{src_without_ext}{extension}"
                                
                                print(f"変更前: {original_url}")
                                print(f"変更後: {new_url}")
                                print("-" * 50)
                                
                                link['href'] = new_url
                                modified = True
                
                if modified:
                    # 整形されたHTMLを出力
                    with open(html_file, 'w', encoding='utf-8') as f:
                        # prettyプリントを無効化し、オリジナルの構造を維持
                        f.write(str(soup))
                    print(f"\nファイルを更新しました: {html_file}\n")
                else:
                    print(f"変更はありませんでした: {html_file}")
                    
            except Exception as e:
                print(f"ファイル処理中にエラーが発生しました {html_file}: {e}")
                
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# 使用例
directory_path = "./slack-archive/html"
process_html(directory_path)