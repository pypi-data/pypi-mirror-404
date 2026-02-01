import httpx
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import quote, urljoin, urlencode
from datetime import datetime
import json

class Maddahi:
    def __init__(self, search_term):
        self.search_term = search_term
        self.encoded_term = quote(search_term)
        self.base_url = "https://kashoob.com"
        self.results = []
        
    async def fetch_page(self, client, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            async with client.stream('GET', url, headers=headers, timeout=30.0) as response:
                response.raise_for_status()
                return await response.aread()
                
        except Exception as e:
            print(f"❌ خطا در دریافت {url}: {e}")
            return None

    def parse_results(self, html_content, max_results=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.find_all('div', class_='content-item')
        
        # اگر max_results مشخص شده باشد، آیتم‌ها را محدود می‌کنیم
        if max_results is not None:
            items = items[:max_results]
        
        parsed_count = 0
        for item in items:
            try:
                title_elem = item.find('h3')
                title = title_elem.text.strip() if title_elem else 'بدون عنوان'
                
                link_elem = item.find('a', href=True)
                link = urljoin(self.base_url, link_elem['href']) if link_elem else '#'
                
                meta_elem = item.find('div', class_='meta')
                meta = meta_elem.text.strip() if meta_elem else 'نامشخص'
                
                labels_elem = item.find('div', class_='labels')
                labels = labels_elem.text.strip() if labels_elem else ''
                
                img_elem = item.find('img')
                img_src = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ''
                
                # استخراج نوع محتوا از کلاس‌ها
                content_type = "صوت"
                if any(x in link for x in ['/video/', '/ویدئو']):
                    content_type = "ویدئو"
                
                self.results.append({
                    'title': title,
                    'artist': meta.split(' . ')[0] if ' . ' in meta else meta,
                    'category': meta.split(' . ')[1] if ' . ' in meta else 'عمومی',
                    'link': link,
                    'labels': labels,
                    'image': img_src,
                    'type': content_type,
                    'timestamp': datetime.now().isoformat()
                })
                parsed_count += 1
                
            except Exception as e:
                print(f"⚠️ خطا در پردازش آیتم: {e}")
                continue
                
        return parsed_count

    def generate_html_report(self):
        html_template = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>نتایج جستجوی "{self.search_term}" در کاشوب</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); padding: 30px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
                .header h1 {{ color: #333; font-size: 2.5rem; margin-bottom: 10px; text-align: center; }}
                .stats {{ display: flex; justify-content: center; gap: 20px; margin-top: 20px; flex-wrap: wrap; }}
                .stat-card {{ background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 15px 25px; border-radius: 12px; text-align: center; min-width: 150px; }}
                .results-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 25px; }}
                .result-card {{ background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 8px 25px rgba(0,0,0,0.08); transition: all 0.3s ease; position: relative; }}
                .result-card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); }}
                .card-image {{ height: 180px; background: linear-gradient(45deg, #667eea, #764ba2); position: relative; overflow: hidden; }}
                .card-image img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; }}
                .result-card:hover .card-image img {{ transform: scale(1.05); }}
                .card-content {{ padding: 20px; }}
                .card-title {{ font-size: 1.3rem; color: #333; margin-bottom: 10px; line-height: 1.4; }}
                .card-meta {{ color: #666; font-size: 0.9rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
                .card-meta i {{ color: #667eea; }}
                .card-badge {{ display: inline-block; background: linear-gradient(45deg, #FF416C, #FF4B2B); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin-top: 10px; }}
                .card-footer {{ padding: 15px 20px; background: #f8f9fa; border-top: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
                .btn {{ background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 8px 20px; border-radius: 8px; text-decoration: none; font-size: 0.9rem; transition: all 0.3s ease; }}
                .btn:hover {{ background: linear-gradient(45deg, #5a6fd8, #6b4190); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }}
                .type-badge {{ position: absolute; top: 15px; left: 15px; background: rgba(0,0,0,0.7); color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; z-index: 2; }}
                .footer {{ text-align: center; margin-top: 40px; color: white; opacity: 0.8; }}
                @media (max-width: 768px) {{ .results-grid {{ grid-template-columns: 1fr; }} .header h1 {{ font-size: 2rem; }} }}
            </style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><i class="fas fa-search"></i> نتایج جستجوی "{self.search_term}"</h1>
                    <p style="text-align: center; color: #666; margin-top: 10px;">سایت کاشوب - {datetime.now().strftime('%Y/%m/%d %H:%M')}</p>
                    <div class="stats">
                        <div class="stat-card">
                            <i class="fas fa-music"></i>
                            <h3>{len(self.results)}</h3>
                            <p>تعداد نتایج</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-microphone"></i>
                            <h3>{len(set(r['artist'] for r in self.results))}</h3>
                            <p>تعداد مداحان</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-film"></i>
                            <h3>{len([r for r in self.results if r['type'] == 'ویدئو'])}</h3>
                            <p>ویدئو</p>
                        </div>
                    </div>
                </div>
                
                <div class="results-grid">
        """
        
        # اضافه کردن کارت‌های نتایج
        for result in self.results:
            html_template += f"""
                    <div class="result-card">
                        <div class="type-badge">
                            <i class="fas fa-{'video' if result['type'] == 'ویدئو' else 'music'}"></i> {result['type']}
                        </div>
                        <div class="card-image">
                            {'<img src="' + result['image'] + '" alt="' + result['title'] + '" loading="lazy">' if result['image'] else ''}
                        </div>
                        <div class="card-content">
                            <h3 class="card-title">{result['title']}</h3>
                            <div class="card-meta">
                                <i class="fas fa-user"></i> <span>{result['artist']}</span>
                            </div>
                            <div class="card-meta">
                                <i class="fas fa-tag"></i> <span>{result['category']}</span>
                            </div>
                            {f'<div class="card-badge"><i class="fas fa-star"></i> {result["labels"]}</div>' if result['labels'] else ''}
                        </div>
                        <div class="card-footer">
                            <a href="{result['link']}" target="_blank" class="btn">
                                <i class="fas fa-external-link-alt"></i> مشاهده
                            </a>
                            <span style="color: #666; font-size: 0.85rem;">
                                <i class="far fa-clock"></i> {result['timestamp'][11:16]}
                            </span>
                        </div>
                    </div>
            """
        
        html_template += f"""
                </div>
                
                <div class="footer">
                    <p>تولید شده توسط Kashoob Crawler • {datetime.now().strftime('%Y/%m/%d')}</p>
                    <p style="margin-top: 10px; font-size: 0.9rem;">
                        <i class="fas fa-info-circle"></i> کلیه حقوق محفوظ است • این گزارش فقط برای استفاده شخصی می‌باشد
                    </p>
                </div>
            </div>
            
            <script>
                // انیمیشن اسکرول نرم
                document.addEventListener('DOMContentLoaded', function() {{
                    const cards = document.querySelectorAll('.result-card');
                    cards.forEach((card, index) => {{
                        card.style.opacity = '0';
                        card.style.transform = 'translateY(20px)';
                        
                        setTimeout(() => {{
                            card.style.transition = 'all 0.6s ease';
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }}, index * 100);
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        return html_template

    async def search(self, page=1, results_per_page=None):
        """
        اجرای اصلی کراولر با قابلیت صفحه‌بندی
        
        پارامترها:
        -----------
        page : int
            شماره صفحه مورد نظر برای جستجو (پیش‌فرض: 1)
        results_per_page : int | None
            تعداد نتایج در هر صفحه (پیش‌فرض: None یعنی همه نتایج)
        """
        print(f"🔍 شروع جستجوی '{self.search_term}' در کاشوب...")
        print(f"📄 صفحه: {page} | تعداد نتایج در هر صفحه: {results_per_page or 'همه'}\n")
        
        async with httpx.AsyncClient(follow_redirects=True, http2=True) as client:
            # ساخت URL با پارامتر صفحه
            query_params = {'q': self.search_term}
            if page > 1:
                query_params['page'] = page
            
            search_url = f"{self.base_url}/search?{urlencode(query_params)}"
            
            # دریافت صفحه نتایج
            html_content = await self.fetch_page(client, search_url)
            
            if not html_content:
                print("❌ دریافت نتایج ناموفق بود")
                return
            
            # پارس کردن نتایج با محدودیت تعداد
            count = self.parse_results(html_content, results_per_page)
            print(f"✅ {count} نتیجه یافت شد")
            
            # ذخیره در فایل JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            json_filename = f"kashoob_{self.search_term}_page{page}_{timestamp}.json"
            json_path = Path(json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'search_term': self.search_term,
                    'page': page,
                    'results_per_page': results_per_page,
                    'timestamp': datetime.now().isoformat(),
                    'total_results': len(self.results),
                    'results': self.results
                }, f, ensure_ascii=False, indent=2)
            print(f"📁 JSON ذخیره شد: {json_path}")
            
            # تولید گزارش HTML
            html_content = self.generate_html_report()
            html_filename = f"kashoob_report_{self.search_term}_page{page}_{timestamp}.html"
            html_path = Path(html_filename)
            html_path.write_text(html_content, encoding='utf-8')
            print(f"🎨 گزارش HTML ذخیره شد: {html_path}")
            
            # نمایش خلاصه در ترمینال
            print(f"\n{'='*60}")
            print("📊 خلاصه نتایج:")
            print(f"{'='*60}")
            
            # نمایش حداکثر 5 نتیجه در ترمینال
            display_count = min(5, len(self.results))
            for i, result in enumerate(self.results[:display_count], 1):
                print(f"{i}. {result['title']}")
                print(f"   👤 {result['artist']} • 🏷️ {result['category']}")
                print(f"   🔗 {result['link'][:80]}...")
                print()
            
            if len(self.results) > display_count:
                print(f"... و {len(self.results) - display_count} مورد دیگر")
            
            print(f"\n✨ گزارش کامل در فایل‌های زیر ذخیره شد:")
            print(f"   📄 {html_path}")
            print(f"   📊 {json_path}")
            
            return {
                'total_results': len(self.results),
                'page': page,
                'results_per_page': results_per_page,
                'html_path': str(html_path),
                'json_path': str(json_path)
            }



