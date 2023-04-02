from django.shortcuts import render
from django.http import HttpResponse,JsonResponse 
import requests
from bs4 import BeautifulSoup
import time
from django.views.decorators.csrf import csrf_exempt
from urllib import parse, request
import html
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os 
import base64
from datetime import datetime
import json
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import re 
import pandas as pd
# Create your views here.
# req => response 
# request handler




def say_hello(request):
    #pull db from db
    return render(request,'hello.html',{'name':'Naga'})

def is_valid_url(url):
    """
    Checks if a URL is valid
    """
    try:
        result = parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# def scrape_content(url, headers):
#     try:
#         response = requests.get(url, headers=headers)
#     except requests.exceptions.RequestException:
#         return None

#     soup = BeautifulSoup(response.content, 'html.parser')
#     content = soup.get_text()

#     return content
# def scrape_content(url, headers):
#     try:
#         response = requests.get(url, headers=headers)
#     except requests.exceptions.RequestException:
#         return None

#     soup = BeautifulSoup(response.content, 'html.parser')

#     # Skip img, svg, and icon tags
#     for tag in soup.find_all(['img', 'svg', 'icon']):
#         tag.decompose()

#     # Extract text from remaining tags and unescape HTML entities
#     content = ''.join(html.unescape(s).strip() for s in soup.stripped_strings)

#     return content

def scrape_content(url, headers):
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Skip img, svg, and icon tags
    for tag in soup.find_all(['img', 'svg', 'icon']):
        tag.decompose()

    # Extract text from remaining tags and unescape HTML entities
    text_blocks = []
    for tag in soup.find_all():
        if tag.name in ['script', 'style', 'button', 'a']:
            # Skip script, style, button and a tags
            continue
        text = tag.get_text(strip=True, separator=' ')
        if text:
            text_blocks.append(text)

    return text_blocks


# def scrape_website(url, headers, max_pages=400):
#     try:
#         response = requests.get(url, headers=headers)
#         soup = BeautifulSoup(response.content, 'html.parser')

#         links = []
#         for link in soup.find_all('a'):
#             href = link.get('href')
#             if href and href.startswith(url):
#                 links.append(href)

#         print(f"Found {len(links)} links")  # print out number of links found
#         print(links)  # print out the links

#         content = scrape_content(url, headers)
#         if not content:
#             return None

#         count = 1  # initialize counter variable
#         print(count)
#         for link in links:
#             if count >= max_pages:  # add a conditional statement to break out of loop
#                 break
#             time.sleep(1)  # add a delay between requests
#             link_content = scrape_content(link, headers)
#             if link_content:
#                 content += link_content
#             count += 1  # increment counter variable
#             print(count)

#         return content
#     except requests.exceptions.RequestException:
#         return None





def scrape_website_recursive(url, headers, max_pages=20, scraped_urls=set()):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Scrape content from current page
        content = scrape_content(url, headers)
        if not content:
            return None

        # Add current URL to set of scraped URLs
        scraped_urls.add(url)

        # Find all internal links on current page
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith(url):
                links.append(href)

        print(f"Found {len(links)} links on {url}")

        # Recursively scrape each internal link
        count = 1
        for link in links:
            if count >= max_pages:
                break
            if link in scraped_urls:
                continue  # Skip already scraped URLs to avoid infinite loop
            time.sleep(1)
            child_content = scrape_website_recursive(link, headers, max_pages=max_pages, scraped_urls=scraped_urls)
            if child_content:
                content += child_content
            count += 1

        return content

    except requests.exceptions.RequestException:
        return None

def preprocess(text):
    # remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text).lower()
    
    # remove stop words
    stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [word for word in words if word not in stop_words]
    
    # stem words to their root form
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]
    
    # join words back into a string with a space separator
    text = ' '.join(words)
    
    return text



def send_mail(data):
    # Configure API key authorization: api-key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.environ.get('SENDIN_BLUE_API')
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    # data = preprocess(data)
    df = pd.DataFrame(data, columns=['text'])
    df.to_excel(f"{filename}.xlsx",index=False)
    with open(f"{filename}.xlsx",'rb') as f :
        file_data = f.read()
        file_name = filename
    # file_content = data.encode('utf-8')
    # encoded_content = base64.b64encode(file_content).decode('utf-8')
    # Define email details
    encoded_file_contents = base64.b64encode(file_data).decode('utf-8')
    email_to = [{'email': 'ch18b053@smail.iitm.ac.in'}, {'email': 'naga@wishup.co'},{'email': 'ch18b054@smail.iitm.ac.in'}]
    email_subject = 'Scraped Data - excel file'
    email_text = 'Here is the scraped data in excel format.'
    email_sender = {'name': 'Naga Sai', 'email': 'nagasai317@gmail.com'}
    email_attachment = [
        {
                'content': encoded_file_contents,
                'name': filename,
                'type': 'application/vnd.ms-excel'
            }
    ]
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=email_to, subject=email_subject, text_content=email_text, sender=email_sender, attachment=email_attachment)
    try:
    # Send the email message
        api_response = api_instance.send_transac_email(send_smtp_email)
        return JsonResponse({'success': True, 'message': 'Email sent successfully'})
    except ApiException as e:
        return JsonResponse({'success': False, 'error': 'Failed to send email: {}'.format(str(e))})   

@csrf_exempt
def form_submission_api(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        # if not is_valid_url(url):
        #     return JsonResponse({'success': False, 'error': 'Invalid URL'})

        content = scrape_website_recursive(url, headers)
        if not content:
            return JsonResponse({'success': False, 'error': 'Unable to scrape website'})
        # content = content[:1500]
        response = send_mail(content)
        # response_json = json.dumps(response)
        return JsonResponse({'success': True, 'content': len(content)})
    else:
        return JsonResponse({'success': False, 'error': 'Method not allowed'})