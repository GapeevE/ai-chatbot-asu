from bs4 import BeautifulSoup
import requests
import numpy as np
import random
import time
import PyPDF2
from io import BytesIO
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Parented
import re
import os
from urllib.parse import urlparse

FILE_TO_PARSE = "data/links.txt"
DIR_TO_STORE = "docs"
DIR_TO_CACHE = "cache"
REPARSING_DATA = False

def transform_link(link):
    if link is None:
        return None
    link = link.strip()
    link = link.replace("http://", "https://")
    while link.endswith('/'):
        new_link = link[:-1]
        link = new_link.rstrip()
    if re.match(r"^(\/?[0-9]+)+$", link) or re.match(r"^([0-9]+\/?)+$", link):
        return None
    if (link.startswith("http") and "abiturient.asu.ru" not in link) or \
    link.startswith("#") or link.endswith("#") or \
    "@" in link or ".jpg" in link or "tel:" in link or ".." in link or \
    "JavaScript" in link or "?page=" in link:
        return None
    elif link.startswith("/"):
        return "https://abiturient.asu.ru" + link
    elif "http" not in link and "abiturient.asu" not in link:
        return "https://abiturient.asu.ru/" + link
    elif "http" not in link and "abiturient.asu.ru" in link:
        return "https://" + link
    elif "abiturient.asu.ru" in link:
        return link
    else:
        return None

def extract_urls_from_txt_files(directory):
    urls = []
    try:
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                filepath = os.path.join(directory, filename)
                with open(filepath, "r", encoding="utf-8") as infile:
                    first_line = infile.readline().strip()
                    if first_line.startswith("URL: "):
                        url = first_line[5:].strip()
                        urls.append(url)
    except FileNotFoundError:
        print(f"Директория не найдена: {directory}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    return urls

def load_links_from_file(filename):
    links = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                link = line.strip()
                if link:
                    links.append(link)
        print(f"Ссылки успешно загружены из файла: {filename}")
    except FileNotFoundError:
        print(f"Файл не найден: {filename}")
    except Exception as e:
        print(f"Ошибка при чтении из файла: {e}")
    return links

def get_filename_from_url(url):
    path = urlparse(url).path
    filename = os.path.basename(path) 
    return filename

def extract_filename_from_url(url, domain="abiturient.asu.ru"):
    if domain not in url:
        print(f"Домен '{domain}' не найден в URL '{url}'.")
        return None
    parsed_url = urlparse(url)
    path = parsed_url.path
    query = parsed_url.query
    relevant_string = path.strip("/")
    if query:
        relevant_string += "_" + query
    filename = re.sub(r"[/\.\-=\?%]", "_", relevant_string)
    filename = re.sub(r"_+", "_", filename)
    filename = "asu_" + filename
    return filename

def process_docx(docx_filepath, output_filepath, link):
    try:
        doc = docx.Document(docx_filepath)
        output_lines = []
        element_index = 0
        for element in doc.element.body:
            if isinstance(element, docx.oxml.text.paragraph.CT_P):
                paragraph = docx.text.paragraph.Paragraph(element, doc)
                paragraph_text = paragraph.text
                if not paragraph_text:
                    continue
                font_sizes = []
                alignments = []
                font_weights = []
                for run in paragraph.runs:
                    font_size = run.font.size.pt if run.font.size else 0
                    font_sizes.append(font_size)
                    alignment_types = {
                        WD_ALIGN_PARAGRAPH.LEFT: 'left',
                        WD_ALIGN_PARAGRAPH.CENTER: 'center',
                        WD_ALIGN_PARAGRAPH.JUSTIFY: 'justify',
                        WD_ALIGN_PARAGRAPH.RIGHT: 'right',
                        None: 'NoneStyle'
                    }
                    alignment = alignment_types.get(paragraph.alignment, 'NoneStyle')
                    alignments.append(alignment)
                    if run.font.bold:
                        font_weights.append("bold")
                    if run.font.italic:
                        font_weights.append("italic")
                    if run.font.underline:
                        font_weights.append("underline")
                    if not font_weights:
                        font_weights.append("normal")
                alignment_row = 'mix' if len(set(alignments)) != 1 else alignments[0] 
                output_lines.append([element_index, paragraph_text, min(font_sizes), alignment_row, font_weights])
                element_index += 1
            elif isinstance(element, docx.oxml.table.CT_Tbl):
                if element_index != 0:
                    table_header = output_lines[element_index - 1][3]
                else:
                    table_header = "mix"
                for table in doc.tables:
                    num_rows = len(table.rows)
                    num_cols = len(table.columns)
                    if num_rows > 1 and num_cols > 0:
                        headers = [cell.text for cell in table.rows[0].cells]
                        if table_header == "center":
                            for i in range(1, num_rows):
                                cells = table.rows[i].cells
                                output_lines.append([element_index, f"    * {i}", 1, 'mix', 'normal'])
                                element_index += 1
                                for j in range(num_cols):
                                    output_lines.append([element_index, f"        * {headers[j]}", 1, 'mix', 'normal'])
                                    element_index += 1
                                    try:
                                        table_cell = cells[j].text
                                        table_cell = re.sub(r'\s+', ' ', table_cell)
                                        output_lines.append([element_index, f"            * {table_cell}", 1, 'mix', 'normal'])
                                    except IndexError:
                                        output_lines.append([element_index, f"            * N/A", 1, 'mix', 'normal'])
                                    element_index += 1
                        else:
                            output_lines.append([element_index, headers[0], 1, 'mix', 'normal'])
                            element_index += 1
                            for i in range(1, num_rows):
                                cells = table.rows[i].cells
                                try:
                                    table_cell_id = cells[0].text
                                    output_lines.append([element_index, f"    * {table_cell_id}", 1, 'mix', 'normal'])
                                except IndexError:
                                    output_lines.append([element_index, "    * N/A", 1, 'mix', 'normal'])
                                    element_index += 1
                                for j in range(1, num_cols):
                                    output_lines.append([element_index, f"        * {headers[j]}", 1, 'mix', 'normal'])
                                    element_index += 1
                                    try:
                                        table_cell = cells[j].text
                                        table_cell = re.sub(r'\s+', ' ', table_cell)
                                        output_lines.append([element_index, f"            * {table_cell}", 1, 'mix', 'normal'])
                                    except IndexError:
                                        output_lines.append([element_index, "            * N/A", 1, 'mix', 'normal'])
                                    element_index += 1
        h1_config = []
        if "italic" not in output_lines[0][4] and "bold" in output_lines[0][4] and "center" in output_lines[0][3]:
            output_lines[0][1] = "# " + output_lines[0][1]
            h1_config = [output_lines[0][2], output_lines[0][3], output_lines[0][4]]
            excepts_headers = []
            for i in range(1, len(output_lines)):
                if output_lines[i][2] == h1_config[0] and output_lines[i][3] == h1_config[1] and output_lines[i][4] == h1_config[2]:
                    output_lines[0][1] += f" {output_lines[i][1]}" 
                    excepts_headers.append(i)
                else:
                    break
            for item in excepts_headers:
                output_lines.pop(item)
            h2_config = []
            for i in range(1, len(output_lines)):
                if not output_lines[i][1].lstrip().startswith("*"):
                    if int(output_lines[i][2]) == 9 and output_lines[i][3] == 'center' and 'bold' in output_lines[i][4] and (len(h2_config) == 0 or (int(h2_config[0]) == 9 and h2_config[1] == "center" and "bold" in h2_config[2])):
                        output_lines[i][1] = "## " + output_lines[i][1]
                    elif int(h1_config[0]) == 14:
                        if int(output_lines[i][2]) == 16 and output_lines[i][3] == 'center' and 'bold' in output_lines[i][4] and (len(h2_config) == 0 or (int(h2_config[0]) == 16 and h2_config[1] == "center" and "bold" in h2_config[2])):
                            output_lines[i][1] = "## " + output_lines[i][1]
                            if len(h2_config) == 0:
                                h2_config = [output_lines[i][2], output_lines[i][3], output_lines[i][4]]
                        elif int(output_lines[i][2]) == 13 and output_lines[i][3] == 'center' and 'bold' in output_lines[i][4] and (len(h2_config) == 0 or (int(h2_config[0]) == 13 and h2_config[1] == "center" and "bold" in h2_config[2])):
                            output_lines[i][1] = "## " + output_lines[i][1]
                            if len(h2_config) == 0:
                                h2_config = [output_lines[i][2], output_lines[i][3], output_lines[i][4]]
                        elif int(output_lines[i][2]) == 12 and output_lines[i][3] == 'center' and 'bold' in output_lines[i][4] and (len(h2_config) == 0 or (int(h2_config[0]) == 12 and h2_config[1] == "center" and "bold" in h2_config[2])):
                            output_lines[i][1] = "## " + output_lines[i][1]
                            if len(h2_config) == 0:
                                h2_config = [output_lines[i][2], output_lines[i][3], output_lines[i][4]]
                        elif int(h1_config[0]) == 16:
                            if int(output_lines[i][2]) == 14 and output_lines[i][3] == 'center' and 'bold' in output_lines[i][4] and (len(h2_config) == 0 or (int(h2_config[0]) == 14 and h2_config[1] == "center" and "bold" in h2_config[2])):
                                output_lines[i][1] = "## " + output_lines[i][1]
                                if len(h2_config) == 0:
                                    h2_config = [output_lines[i][2], output_lines[i][3], output_lines[i][4]]
            h3_config = []
            for i in range(1, len(output_lines)):
                if not output_lines[i][1].lstrip().startswith("*") and len(h1_config) != 0 and len(h2_config) != 0:
                    if int(output_lines[i][2]) == 12 and output_lines[i][3] == 'justify' and output_lines[i][4] == 'bold' and int(h1_config[0]) == 16 and int(h2_config[0]) == 14 and (len(h3_config) != 0 or (output_lines[i][2] == h3_config[0] and output_lines[i][3] == h3_config[1] and output_lines[i][4] == h3_config[2])):
                        output_lines[i][1] = "### " + output_lines[i][1]
                        if len(h3_config) == 0:
                            h3_config = [output_lines[i][2], output_lines[i][3], output_lines[i][4]]
                    elif int(output_lines[i][2]) == 12 and output_lines[i][3] == 'justify' and output_lines[i][4] == 'bold' and int(h1_config[0]) == 14 and int(h2_config[0]) == 12 and (len(h3_config) != 0 or (output_lines[i][2] == h3_config[0] and output_lines[i][3] == h3_config[1] and output_lines[i][4] == h3_config[2])):
                        output_lines[i][1] = "### " + output_lines[i][1]
                        if len(h3_config) == 0:
                            h3_config = [output_lines[i][2], output_lines[i][3], output_lines[i][4]]
                    elif int(output_lines[i][2]) == 13 and output_lines[i][3] == 'justify' and output_lines[i][4] == 'bold' and int(h1_config[0]) == 14 and int(h2_config[0]) == 13 and (len(h3_config) != 0 or (output_lines[i][2] == h3_config[0] and output_lines[i][3] == h3_config[1] and output_lines[i][4] == h3_config[2])):
                        output_lines[i][1] = "### " + output_lines[i][1]
                        if len(h3_config) == 0:
                            h3_config = [output_lines[i][2], output_lines[i][3], output_lines[i][4]]
        if output_filepath and len(output_lines) > 0:
            filepath = os.path.join(DIR_TO_STORE, f"{output_filepath}.txt")
            with open(filepath, "w", encoding="utf-8") as outfile:
                outfile.write(f"URL: {link}\n")
                for line in output_lines:
                    outfile.write(f"{line[1]}\n")
            print(f"Контент успешно сохранен в {filepath}")
    except FileNotFoundError:
        print(f"Файл не найден: {docx_filepath}")
    except docx.opc.exceptions.PackageNotFoundError:
        print("Не удалось открыть docx файл.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def parsing_docx(res, filename, link):
    try:
        if not filename:
            filename = 'document.docx'
        if not os.path.exists(DIR_TO_CACHE):
            os.makedirs(DIR_TO_CACHE)
        filepath = os.path.join(DIR_TO_CACHE, filename)
        with open(filepath, 'wb') as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
        output_filepath = extract_filename_from_url(link)
        if output_filepath:
            process_docx(filepath, output_filepath, link)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании файла: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def parsing_pdf(res, link):
    content = []
    try:
        pdf_file = BytesIO(res.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            content.append(page.extract_text())
        output_filepath = extract_filename_from_url(link)
        if output_filepath and len(content) > 0:
            filepath = os.path.join(DIR_TO_STORE, f"{output_filepath}.txt")
            with open(filepath, "w", encoding="utf-8") as outfile:
                outfile.write(f"URL: {link}\n")
                for line in content:
                    outfile.write(f"{line}\n")
            print(f"Контент успешно сохранен в {filepath}")
    except Exception as e:
        print(f"Ошибка при парсинге - PDF '{link}': {e}")

def parsing_html(res, link):
    content = []
    try:
        soup = BeautifulSoup(res.text, 'lxml')
        main_section = soup.find("main")
        if not main_section:
            return False
        header_burger_menu = main_section.find("div", {"class": "header-burger-menu"})
        if header_burger_menu:
            header_burger_menu.decompose()
        main_buttons_container = main_section.find("section", {"class": "main-buttons-container"})
        if main_buttons_container:
            main_buttons_container.decompose()
        modal = main_section.find("div", {"class": "modal", "id": "modal_container"})
        if modal:
            modal.decompose()
        breadcrumbs_ul = main_section.find("ul", {"class": "breadcrumbs-ul"})
        if breadcrumbs_ul:
            breadcrumbs_ul.decompose()

        def process_element(element):
            if element.name in ["li", "p", "dd"]:
                text = element.get_text()
                if text and element.name in ['p']:
                    if text.strip() not in ['Поступить', 'Зарегистрироваться'] and len(text.strip()) > 0:
                        spaced_text = re.sub(r'\s+', ' ', text)
                        content.append(spaced_text.strip())
                elif text and element.name in ['li']:
                    li_list = []
                    for child in element.children:
                        text = child.get_text()
                        if text:
                            if len(text.strip()) > 0:
                                spaced_text = re.sub(r'\s+', ' ', text)
                                li_list.append(spaced_text.strip())
                    if len(li_list) > 0:
                        content.append(f"    * {li_list[0]}")
                    for i in range(1, len(li_list)):
                        content.append(f"        * {li_list[i]}")
                elif text and element.name in ['dd']:
                    for child in element.children:
                        if child.name in ['ul', 'ol']:
                            for child_child in child.children:
                                text = child_child.get_text()
                                if text:
                                    content.append(f"    * {text.strip()}")
                        else:
                            content.append(f"    * {text.strip()}")
            elif element.name in ["table"]:
                thead = element.find('thead')
                tbody = element.find('tbody')
                if thead and tbody:
                    headers = [th.get_text(strip=True) for th in thead.find_all('th')]
                    rows = tbody.find_all('tr')
                    if headers:
                        title = headers[0]
                        table_content = []
                        for row in rows:
                            cells = row.find_all('td')
                            row_text = []
                            for j in range(len(headers)):
                                if j < len(cells):
                                    cell_text = cells[j].get_text(strip=True)
                                    if j == 0:
                                        row_text.append(f"    * {cell_text}")
                                    else:
                                        row_text.append(f"        * {headers[j]}")
                                        row_text.append(f"            * {cell_text}")
                            table_content.append(row_text)
                        if title:
                            content.append(title)
                        if table_content:
                            for item_row in table_content:
                                for item in item_row:
                                    content.append(item)
            else:
                child_list = []
                for child in element.children:
                    text = child.get_text()
                    if text:
                        if len(text.strip()) > 0:
                            child_list.append([child.name, text])
                if  (len(child_list) == 2 and ((child_list[0][0] == "span" and child_list[1][0] == "small") or (child_list[0][0] == "span" and child_list[1][0] == "span"))) or (len(child_list) == 3 and child_list[0][0] == "span" and child_list[1][0] == "span" and child_list[2][0] == "span"):
                    if child_list[0][0] == "span" and child_list[1][0] == "small":
                        content.append(f"{child_list[1][1].strip()}:")
                        content.append(f"    * {child_list[0][1].strip()}")
                    elif len(child_list) == 3 and child_list[0][0] == "span" and child_list[1][0] == "span" and child_list[2][0] == "span":
                        content.append(f"{child_list[2][1].strip()} {child_list[0][1].strip()}:")
                        content.append(f"    * {child_list[1][1].strip()}")
                    elif child_list[0][0] == "span" and child_list[1][0] == "span" and len(child_list) == 2:
                        content.append(f"{child_list[1][1].strip()}:")
                        content.append(f"    * {child_list[0][1].strip()}")
                else:
                    for child in element.children:
                        if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt', 'span', 'small']:
                            if child.name in ['span', 'small'] and element.name in ['div']:
                                text = child.get_text()
                                if text:
                                    content.append(text.strip())
                            elif child.name in ['h1']:
                                text = child.get_text()
                                if text: 
                                    text = f"# {text.strip()}"
                                    content.append(text)
                            elif child.name in ['h2']:
                                text = child.get_text()
                                if text: 
                                    text = f"## {text.strip()}"
                                    content.append(text)
                            elif child.name in ['h3']:
                                text = child.get_text()
                                if text: 
                                    text = f"### {text.strip()}"
                                    content.append(text)
                            elif child.name in ['h4']:
                                text = child.get_text()
                                if text: 
                                    text = f"#### {text.strip()}"
                                    content.append(text)
                            elif child.name in ['h5']:
                                text = child.get_text()
                                if text: 
                                    text = f"##### {text.strip()}"
                                    content.append(text)
                            elif child.name in ['h6']:
                                text = child.get_text()
                                if text: 
                                    text = f"###### {text.strip()}"
                                    content.append(text)
                            else:
                                text = child.get_text()
                                if text:
                                    text = text.strip() + ':'
                                    content.append(text)
                        elif hasattr(child, 'children'):
                            process_element(child)

        process_element(main_section)
        output_filepath = extract_filename_from_url(link)
        if output_filepath and len(content) > 0:
            filepath = os.path.join(DIR_TO_STORE, f"{output_filepath}.txt")
            with open(filepath, "w", encoding="utf-8") as outfile:
                outfile.write(f"URL: {link}\n")
                for line in content:
                    outfile.write(f"{line}\n")
            print(f"Контент успешно сохранен в {filepath}")
    except Exception as e:
        print(f"Ошибка при парсинге - HTML '{link}': {e}")
    return True

def get_all_links(res, link):
    content = []
    try:
        soup = BeautifulSoup(res.text, 'lxml')
        links = soup.find_all('a')
        for i in range(len(links)):
            item = links[i].get('href')
            new_link = transform_link(item)
            if new_link:
                content.append(new_link)
    except Exception as e:
        print(f"Ошибка при парсинге links from HTML '{link}': {e}")
    parsing_list = np.array(content)
    parsing_list = np.unique(parsing_list)
    return parsing_list

def parsing(link, time_start=6, time_finish=12):
    links = []
    try:
        delay = round(random.uniform(time_start, time_finish), 1)
        time.sleep(delay)
        r = requests.get(link, timeout=16)
        if link.endswith(".docx"):
            filename = get_filename_from_url(link)
            parsing_docx(r, filename, link)
        elif link.endswith(".pdf"):
            parsing_pdf(r, link)
        else:
            is_parse = parsing_html(r, link)
            if is_parse and REPARSING_DATA:
                links_list = get_all_links(r, link)
                if len(links_list) > 0:
                    for item in links_list:
                        if item not in links:
                            links.append(item)
    except requests.exceptions.Timeout:
        print(f"Время ожидания истекло для '{link}'")
    return links

def get_parsed_list():
    to_parse = load_links_from_file(FILE_TO_PARSE)
    exception_links = extract_urls_from_txt_files(DIR_TO_STORE)
    while to_parse:
        item = to_parse.pop(0)
        new_links_list = parsing(item)
        if len(new_links_list) > 0:
            for element in new_links_list:
                if element not in exception_links:
                    exception_links.append(element)
                    if REPARSING_DATA:
                        to_parse.append(element)

if __name__ == "__main__":
    get_parsed_list()

