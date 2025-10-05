from utils.save_to_firebase import save_conditions
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

bucketname = 'enigmagenomics-internship.firebasestorage.app'

def condition_function():
    
    ses = requests.Session()
    ses.headers.update({"User-Agent": "Mozilla/5.0"})
    url_main = 'https://medlineplus.gov/genetics/condition'
    letters = list("abcdefghijklmnopqrstuvwxyz0")

    all_links = []
    seen = set()  
    
    for i in letters:
        url = url_main + '/' if i == 'a' else url_main + '-' + i + '/'
        page = ses.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        A = soup.find('ul', class_='withident breaklist')
        if A:
            L = A.find_all('li')
            for li in L:
                a = li.find('a')
                if a and a['href'] not in seen:
                    seen.add(a['href'])  
                    all_links.append(li) 
                    
    total = len(all_links)
    print(f"Total conditions found: {total}")
    
    saved_count = 0
    lock = Lock()

    def replace_links_with_text(cont):
        
        if not cont:
            return ""

        for a in cont.find_all('a'):
            text = a.text.strip()
            href = a['href']
            replacement = f"{text} ({href})" if href else text
            a.replace_with(replacement)

        return cont.text.strip()

    def process_condition(i):
        nonlocal saved_count
        try:
            lin = i.find('a')
            condition_name = lin.text.strip()
            link = lin['href']
            page2 = ses.get(link)
            soup1 = BeautifulSoup(page2.text, 'html.parser')
            
            divs = soup1.find_all('div' , class_ = 'mp-exp exp-full')
            
            description_div = None
            for z in divs:
                if z.get("data-bookmark") == "description":
                    description_div = z
                    break
            description = ""
            if description_div:
                content = description_div.find('div', class_="mp-content")
                if content:
                    description = replace_links_with_text(content)

            frequency_div = None
            for y in divs:
                if y.get("data-bookmark") == "frequency":
                    frequency_div = y
                    break
            frequency = ""
            if frequency_div:
                fre = frequency_div.find('div' , class_ = "mp-content")
                if fre:
                    frequency = replace_links_with_text(fre)


            causes_div = None
            for x in divs:
                if x.get("data-bookmark") == "causes":
                    causes_div = x
                    break
            causes = [] 
            cause_entry = {
                "details": "",
                "related_genes": [],
                "NCBI_gene": []
            }
            if causes_div:
                cau = causes_div.find('div' , class_ = 'mp-content')
                causes_details = replace_links_with_text(cau) if cau else ""
                cause_entry["details"] = causes_details
                
                block = causes_div.find('div' , class_ = "related-genes mp-exp exp-full")
                if block:
                    h = block.find('h3')
                    if h:
                        ul_related = h.find_next("ul" , class_="relatedmp")
                        if ul_related:
                            for m in ul_related.find_all('li'):
                                a = m.find("a")
                                if a:
                                    gene_name = a.text.strip()
                                    gene_url = a["href"]
                                    cause_entry["related_genes"].append({
                                        "name": gene_name,
                                        "url": gene_url
                                    }) 
                if block:            
                    ncbi_block = block.find("p", string=lambda s: s and "NCBI Gene" in s)
                    if ncbi_block:
                        ul_ncbi = ncbi_block.find_next("ul", class_="relatedmp")
                        if ul_ncbi:
                            for li in ul_ncbi.find_all("li"):
                                a = li.find("a")
                                if a:
                                    ncbi_name = a.text.strip()
                                    ncbi_url = a["href"]
                                    cause_entry["NCBI_gene"].append({
                                        "name": ncbi_name,
                                        "url": ncbi_url
                                    })
                causes.append(cause_entry)
                
            inheritance_div = None
            for n in divs:
                if n.get("data-bookmark") == "inheritance":
                    inheritance_div = n
                    break
            inheritance = ""
            if inheritance_div:
                inh = inheritance_div.find('div', class_="mp-content")
                if inh:
                    inheritance = replace_links_with_text(inh)
                    

            syn_div = None
            for s in divs:
                if s.get("data-bookmark") == "synonyms":
                    syn_div = s
                    break
            synonyms = []
            if syn_div:
                ul = syn_div.find("ul", class_="bulletlist")
                if ul:
                    other_n = ul.find_all("li")
                    synonyms = [x.text.strip() for x in other_n]
                    
                    
            resources_div = None
            for n in divs:
                    if n.get('data-bookmark') == 'resources':
                        resources_div = n
                        break
            resources = []           
            if resources_div:
                res =  resources_div.find_all('div', class_="mp-content")

                for q in res:
                    name_resource = q.find('h2')
                    name_res =  name_resource.text.strip() if name_resource else "No Title"

                    a_all_tag = q.find_all('a', href=True)

                    for a in a_all_tag:
                        resources.append({
                            "name": name_res,
                            "url": a['href'],
                            "details": a.text.strip()
                        })

                
            references_div = None
            for ln in divs:
                if ln.get("data-bookmark") == 'references':
                    references_div = ln
                    break
            references = []
            if references_div:
                li_items = references_div.find_all('li')
                
                for li in li_items:
                    a_tags = li.find_all("a", href=True)
                    
                    citations = []
                    urls = []
                    for a in a_tags:
                        citations.append(a.text.strip())
                        urls.append(a['href'])
                        
                        for p in a_tags:
                            p.extract()
                        name_text = li.text.strip().replace('\n','')
                    
                        references.append({
                            "name": name_text,
                            "citation": " or ".join(citations),
                            "url": " or ".join(urls)
                        })
                        
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
            
            fi_name = condition_name.replace("/", "_").replace(" ", "_")
            filename = f'genes/all_conditions_separate_files/{fi_name}.json' 
            d = json.dumps(data_condition, ensure_ascii=False, indent=2) 
            save_conditions(d, bucketname, filename) 
            
            with lock:
                saved_count += 1
                print(f"{saved_count}/{total} -> {fi_name} saved.")
                
            del soup1, page2, description_div, frequency_div, causes_div, inheritance_div, syn_div, resources_div, references_div, data_condition
                        
        except Exception as e:
            with lock:
                 print(f"Error processing {lin.text.strip()}: {e}")    
                                 
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_condition, i) for i in all_links]
        for future in as_completed(futures):
            try:
                future.result() 
            except Exception as e:
                print(f"Error in task: {e}")
            
    return total, "All Conditions info added successfully."              