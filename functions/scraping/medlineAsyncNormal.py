from utils.save_to_firebase import save_conditions
from utils.saveLogs import log_condition_run
import json
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import re

bucketname = 'enigmagenomics-internship.firebasestorage.app'

def async_cond_function():
    
    url_base = 'https://medlineplus.gov/genetics/condition'
    letters = list("abcdefghijklmnopqrstuvwxyz0")
    
    success_conditions = []
    failed_conditions = []
    
    async def fetch(session, url):
        try:
            async with session.get(url, timeout=15) as response:
                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
            
    async def get_all_links(session):
        all_links = []
        seen = set()
        for i in letters:
            url = url_base + '/' if i == 'a' else url_base + '-' + i + '/'
            html = await fetch(session, url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                A = soup.find('ul', class_='withident breaklist')
                if A:
                    L = A.find_all('li')
                    for li in L:
                        a = li.find('a')
                        if a and a['href'] not in seen:
                            seen.add(a['href'])  
                            all_links.append(li)
        return all_links
    
    def extract_text_and_links(cont):
        if not cont:
            return ""
        for a in cont.find_all('a', href=True):
            label = a.text.strip()
            url = a['href']
            replacement = f"{label} ({url})" if url else label
            a.replace_with(replacement)
        return cont.get_text(" ", strip=True)
       
    
    semaphore = asyncio.Semaphore(30)
    async def process_condition(session, link_tag):
        async with semaphore:
            try:
                lin = link_tag.find('a')
                condition_name = lin.text.strip()
                link = lin['href']
        
                page2_text = await fetch(session, link)
                if not page2_text:
                    return
        
                soup1 = BeautifulSoup(page2_text, 'html.parser')
                divs = soup1.find_all('div', class_='mp-exp exp-full')
        
                description_div = next((z for z in divs if z.get("data-bookmark")=="description"), None)
                description = ""
                if description_div:
                    content = description_div.find('div', class_="mp-content")
                    if content:
                        description = await asyncio.to_thread(extract_text_and_links,content)
        
                frequency_div = next((y for y in divs if y.get("data-bookmark")=="frequency"), None)
                frequency = ""
                if frequency_div:
                    fre = frequency_div.find('div', class_="mp-content")
                    if fre:
                        frequency = await asyncio.to_thread(extract_text_and_links,fre)
        
                causes_div = next((x for x in divs if x.get("data-bookmark")=="causes"), None)
                causes = []
                cause_entry = {"details": "", "related_genes": [], "NCBI_gene": []}
                if causes_div:
                    cau = causes_div.find('div', class_='mp-content')
                    if cau:
                        cause_entry["details"] = await asyncio.to_thread(extract_text_and_links,cau)
                    block = causes_div.find('div', class_="related-genes mp-exp exp-full")
                    if block:
                        h = block.find('h3')
                        if h:
                            ul_related = h.find_next("ul", class_="relatedmp")
                            if ul_related:
                                for m in ul_related.find_all('li'):
                                    a = m.find("a")
                                    if a:
                                        cause_entry["related_genes"].append({"name": a.text.strip(), "url": a['href']})
                        ncbi_block = block.find("p", string=lambda s: s and "NCBI Gene" in s)
                        if ncbi_block:
                            ul_ncbi = ncbi_block.find_next("ul", class_="relatedmp")
                            if ul_ncbi:
                                for li in ul_ncbi.find_all("li"):
                                    a = li.find("a")
                                    if a:
                                        cause_entry["NCBI_gene"].append({"name": a.text.strip(), "url": a['href']})
                    causes.append(cause_entry)
        
                inheritance_div = next((n for n in divs if n.get("data-bookmark")=="inheritance"), None)
                inheritance = ""
                if inheritance_div:
                    inh = inheritance_div.find('div', class_="mp-content")
                    if inh:
                        inheritance = await asyncio.to_thread(extract_text_and_links,inh)
        
                syn_div = next((s for s in divs if s.get("data-bookmark")=="synonyms"), None)
                synonyms = []
                if syn_div:
                    ul = syn_div.find("ul", class_="bulletlist")
                    if ul:
                        synonyms = [x.text.strip() for x in ul.find_all("li")]
        
                resources_div = next((n for n in divs if n.get("data-bookmark")=='resources'), None)
                resources = []
                if resources_div:
                    res = resources_div.find_all('div', class_="mp-content")
                    for q in res:
                        name_resource = q.find('h2')
                        name_res = name_resource.text.strip() if name_resource else "No Title"
                        for a in q.find_all('a', href=True):
                            resources.append({"name": name_res, "url": a['href'], "details": a.text.strip()})
        
                references_div = next((ln for ln in divs if ln.get("data-bookmark")=='references'), None)
                references = []
                if references_div:
                    for li in references_div.find_all('li'):
                        a_tags = li.find_all("a", href=True)
                        citations, urls = [], []
                        for a in a_tags:
                            citations.append(a.text.strip())
                            urls.append(a['href'])
                            a.extract()
                        references.append({"name": li.text.strip(), "citation": " or ".join(citations), "url": " or ".join(urls)})
        
                data_condition = {
                    "condition_name": condition_name,
                    "details": {
                        "description": description,
                        "frequency": frequency,
                        "causes": causes,
                        "inheritance": inheritance,
                        "synonyms": synonyms,
                        "resources": resources,
                        "references": references
                    }
                }
                fi_name = re.sub(r"[^a-zA-Z0-9]+", '_', condition_name.lower())
                fi_name = re.sub(r'_+', '_', fi_name).strip('_')
                filename = f'genes/conditions_updated/{fi_name}.json' 
                d = json.dumps(data_condition, ensure_ascii=False, indent=2) 
                await asyncio.to_thread(save_conditions, d, bucketname, filename)
                
                size = len(d.encode('utf-8')) / 1024  # here i did dividing by 1024 to convert bytes to KB
                success_conditions.append({"name": condition_name, "size_kb": size, "path": filename})
                del soup1, page2_text, description_div, frequency_div, causes_div, inheritance_div, syn_div, resources_div, references_div, data_condition
                return 1
            
            except Exception as e:
                failed_conditions.append({"name": condition_name, "error": str(e)})
                print(f"Error processing {lin.text.strip()}: {e}")
                return 0

    async def main():
        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            all_links = await get_all_links(session)
            tasks = [process_condition(session, link_tag) for link_tag in all_links]
            r = await asyncio.gather(*tasks)
            save_count = sum(r)
            
        log_path = await asyncio.to_thread(log_condition_run, success_conditions, failed_conditions, len(all_links))
        
        print(f"Total conditions saved: {save_count} out of total conditions: {len(all_links)}")
        print(f"Log saved at: {log_path}")
        return len(all_links)
      
    total = asyncio.run(main())
    return total, "All Conditions info added successfully."

        